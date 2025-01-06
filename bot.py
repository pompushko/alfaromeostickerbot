import os 
import io
import re
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, ChatMemberUpdatedFilter, ADMINISTRATOR, JOIN_TRANSITION
from aiogram.types import Message, ChatMemberUpdated, BufferedInputFile, MaybeInaccessibleMessage
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import CopyMessage, DeleteMessage
import asyncio
from datetime import datetime, timedelta

from aiogram.types import InputMediaPhoto
from aiogram.exceptions import TelegramRetryAfter
from GetImage import get_image

import PyPDF2

from UserRequests import UserRequests
from AsyncDbHandler import AsyncDbHandler

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USER_ID = os.getenv("TELEGRAM_BOT_USER_ID")
ALLOWED_CHATS = set()
MAX_REQUESTS_PER_DAY = int(os.getenv("MAX_REQUESTS_PER_DAY", "10"))
MAX_IMAGES_PER_ALBUM = 10
user_requests = UserRequests(max_requests=MAX_REQUESTS_PER_DAY)
bot = Bot(token=TOKEN)
dp = Dispatcher()

VIN_PATTERN = re.compile(r'(?:VIN\s*)?(ZA[RS][A-HJ-NPR-Z0-9]{14})', re.IGNORECASE)

@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def on_added_to_group(event: ChatMemberUpdated):
    if event.new_chat_member.status == "member":
        ALLOWED_CHATS.add(event.chat.id)
        await bot.send_message(
            event.chat.id, 
            f"Бот активирован в этой группе\nЛимит запросов на пользователя: <b>{MAX_REQUESTS_PER_DAY}</b> в сутки",
            parse_mode="HTML"
        )


@dp.message()
async def handle_message(message: Message):
    if message.from_user.is_bot:
        return
    if message.content_type not in ['text', 'photo', 'document']:
        return
    # if message.chat.type in ['group', 'supergroup'] and message.chat.id in ALLOWED_CHATS:
    if message.chat.type in ['group', 'supergroup']:
        message_text = message.text or message.caption or ''
        if message_text:
            match = VIN_PATTERN.search(message_text)
            if match:
                vin = match.group(1)
                user_id = message.from_user.id

                remaining = user_requests.get_remaining_requests(user_id)
                if remaining <= 0:
                    next_reset = datetime.now() + timedelta(days=1)
                    try:
                        await message.reply(
                            f"Достигнут дневной лимит запросов (<b>{MAX_REQUESTS_PER_DAY}</b>). "
                            f"Следующий запрос будет доступен через <b>{next_reset.strftime('%H:%M:%S')}</b>",
                            parse_mode="HTML"
                        )
                    except TelegramBadRequest as e:
                        if "message to be replied not found" in str(e):
                            await message.chat.send_message(
                                f"Достигнут дневной лимит запросов (<b>{MAX_REQUESTS_PER_DAY}</b>). "
                                f"Следующий запрос будет доступен через <b>{next_reset.strftime('%H:%M:%S')}</b>",
                                parse_mode="HTML"
                            )
                    return
                db = AsyncDbHandler()
                msg_id_from_db = await db.GetMessageIdByVin(vin)

                if msg_id_from_db:
                     #check if message exists
                    try:
                        tmp_msg = await bot(CopyMessage(chat_id=message.chat.id, from_chat_id=message.chat.id, from_user_id=BOT_USER_ID, message_id=msg_id_from_db))
                        await bot(DeleteMessage(from_user_id=BOT_USER_ID, message_id=tmp_msg.message_id, chat_id=message.chat.id))
                    except TelegramBadRequest:
                    # delete it from db if it's inaccessible for the bot    
                        await db.DeleteVin(vin)
                        msg_id_from_db = None
                if not msg_id_from_db:
                    if not user_requests.add_request(user_id):
                        await message.reply("Ошибка при обработке запроса. Попробуйте позже.")
                        return
                    
                    url = f"https://www.alfaromeousa.com/hostd/windowsticker/getWindowStickerPdf.do?vin={vin}"
                    
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.get(url)
                            if response.status_code == 200:
                                pdf_buffer = io.BytesIO(response.content)
                                pdf_reader = PyPDF2.PdfReader(pdf_buffer)
                                text = pdf_reader.pages[0].extract_text()

                                if "Sorry, a Window Sticker is unavailable for this VIN" in text:
                                    user_requests.requests[user_id].pop()
                                    try:
                                        sent_msg = await message.reply("Window sticker недоступен для данного VIN")
                                    except TelegramBadRequest as e:
                                        if "message to be replied not found" in str(e):
                                           sent_msg = await  message.chat.send_message("Window sticker недоступен для данного VIN")
                                        else:
                                            raise
                                    await db.AddVIN(vin, sent_msg.message_id)
                                else:
                                    pdf_file = BufferedInputFile(
                                                        response.content,
                                                        filename=f"{vin}.pdf"
                                                    )
                                    try:
                                        sent_msg = await message.reply_document(
                                            document=pdf_file,
                                            caption=f"Window sticker for VIN: <b>{vin}</b>\nОсталось запросов сегодня: <b>{remaining-1}</b>",
                                            parse_mode="HTML"
                                        )
                                    except TelegramBadRequest as e:
                                        if "message to be replied not found" in str(e):
                                            sent_msg = await message.chat.send_document(
                                                document=pdf_file,
                                                caption=f"Window sticker for VIN: <b>{vin}</b>\nОсталось запросов сегодня: <b>{remaining-1}</b>",
                                                parse_mode="HTML"
                                            )
                                        else:
                                            raise
                                    await db.AddVIN(vin, sent_msg.message_id)
                            else:
                                user_requests.requests[user_id].pop()
                                try:
                                    await message.reply("Ошибка загрузки файла")
                                except TelegramBadRequest as e:
                                    if "message to be replied not found" in str(e):
                                        await message.chat.send_message("Ошибка загрузки файла")
                                    else:
                                        raise 
                    except Exception as e:
                        user_requests.requests[user_id].pop()
                        await message.reply(f"Произошла ошибка: {str(e)}")
                    try:
                        images = await get_image(vin)
                        if images:
                            max_images_per_album = MAX_IMAGES_PER_ALBUM
                            for i in range(0, len(images), max_images_per_album):
                                media_group = [
                                    InputMediaPhoto(media=BufferedInputFile(image.read(), filename=f"{vin}_{i + idx + 1}.jpg"))
                                    for idx, image in enumerate(images[i:i + max_images_per_album])
                                ]
                                for attempt in range(3):  
                                    try:
                                        await bot.send_media_group(
                                            chat_id=message.chat.id,
                                            media=media_group,
                                            reply_to_message_id=message.message_id   
                                        )
                                        break  
                                    except TelegramRetryAfter as e:
                                        retry_after = e.retry_after  
                                        print(f"Flood control error: retrying after {retry_after} seconds...")
                                        await asyncio.sleep(retry_after) 
                                        continue  
                        else:
                            await message.reply("Фотографии для данного VIN не найдены.")
                    except Exception as e:
                        await message.reply(f"Произошла ошибка при отправке фотографий: {str(e)}")

                else:
                    try:
                        await message.reply(f"Ссылка на сообщение с pdf:\nhttps://t.me/{message.chat.username}/{msg_id_from_db}")
                    except TelegramBadRequest as e:
                        if "message to be replied not found" in str(e):
                            await message.chat.send_message(f"Ссылка на сообщение с pdf:\nhttps://t.me/{message.chat.username}/{msg_id_from_db}")
                        else:
                            raise 

                # try:
                #     eper_client = FiatPartsClient(headers=headers, cookies=cookies)
                #     pdf_generator = FiatPartsPDFGenerator()
                #     result = await eper_client.get_full_vin_info(vin, session_id)

                #     pdf_report = BufferedInputFile(
                #                     pdf_generator.create_pdf(result),
                #                     filename=f"{vin}.pdf"
                #                 )
                #     await message.reply_document(
                #                         document=pdf_report,
                #                         caption=f"Комплектация по VIN: <b>{vin}</b>\nОсталось запросов сегодня: <b>{remaining-1}</b>",
                #                         parse_mode="HTML"
                #                     )
                    
                # except Exception as e:
                #     user_requests.requests[user_id].pop()

async def main():
    print(f"Бот запущен с лимитом {MAX_REQUESTS_PER_DAY} запросов в сутки на пользователя")
    db = AsyncDbHandler()
    await db.init_async()
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())