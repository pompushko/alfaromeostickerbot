import os
import re
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, ChatMemberUpdatedFilter, ADMINISTRATOR, JOIN_TRANSITION
from aiogram.types import Message, ChatMemberUpdated, BufferedInputFile
from aiogram.exceptions import TelegramBadRequest

from datetime import datetime, timedelta

from UserRequests import UserRequests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHATS = set()
MAX_REQUESTS_PER_DAY = int(os.getenv("MAX_REQUESTS_PER_DAY", "5"))

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
                
                if not user_requests.add_request(user_id):
                    await message.reply("Ошибка при обработке запроса. Попробуйте позже.")
                    return
                
                url = f"https://www.alfaromeousa.com/hostd/windowsticker/getWindowStickerPdf.do?vin={vin}"
                
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(url)
                        if response.status_code == 200:
                            pdf_file = BufferedInputFile(
                                response.content,
                                filename=f"{vin}.pdf"
                            )

                            try:
                                await message.reply_document(
                                    document=pdf_file,
                                    caption=f"Window sticker for VIN: <b>{vin}</b>\nОсталось запросов сегодня: <b>{remaining-1}</b>",
                                    parse_mode="HTML"
                                )
                            except TelegramBadRequest as e:
                                if "message to be replied not found" in str(e):
                                    await message.chat.send_document(
                                        document=pdf_file,
                                        caption=f"Window sticker for VIN: <b>{vin}</b>\nОсталось запросов сегодня: <b>{remaining-1}</b>",
                                        parse_mode="HTML"
                                    )
                                else:
                                    raise
                        else:
                            user_requests.requests[user_id].pop()
                            try:
                                await message.reply("Не удалось загрузить PDF для данного VIN")
                            except TelegramBadRequest as e:
                                if "message to be replied not found" in str(e):
                                    await message.chat.send_message("Не удалось загрузить PDF для данного VIN")
                                else:
                                    raise
                except Exception as e:
                    user_requests.requests[user_id].pop()
                    await message.reply(f"Произошла ошибка: {str(e)}")

async def main():
    print(f"Бот запущен с лимитом {MAX_REQUESTS_PER_DAY} запросов в сутки на пользователя")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())