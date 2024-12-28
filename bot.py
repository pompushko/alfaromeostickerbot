import os
import re
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, ChatMemberUpdatedFilter, ADMINISTRATOR, JOIN_TRANSITION
from aiogram.types import Message, ChatMemberUpdated

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHATS = set()

bot = Bot(token=TOKEN)
dp = Dispatcher()

VIN_PATTERN = re.compile(r'VIN ZA[A-HJ-NPR-Z0-9]{15}')

@dp.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def on_added_to_group(event: ChatMemberUpdated):
    if event.new_chat_member.status == "member":
        ALLOWED_CHATS.add(event.chat.id)
        await bot.send_message(event.chat.id, "Бот активирован в этой группе")

@dp.message()
async def handle_message(message: Message):
    # Проверяем, что сообщение из разрешенной группы
    # if message.chat.type in ['group', 'supergroup'] and message.chat.id in ALLOWED_CHATS:
    if message.chat.type in ['group', 'supergroup']:
        if message.text:
            match = VIN_PATTERN.search(message.text)
            if match:
                vin = match.group(0).split('VIN ')[1]
                url = f"https://www.alfaromeousa.com/hostd/windowsticker/getWindowStickerPdf.do?vin={vin}"
                
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(url)
                        if response.status_code == 200:
                            with open(f"{vin}.pdf", "wb") as f:
                                f.write(response.content)
                            await message.reply_document(
                                document=types.FSInputFile(f"{vin}.pdf"),
                                caption=f"Window sticker for VIN: {vin}"
                            )
                            os.remove(f"{vin}.pdf")
                        else:
                            await message.reply("Не удалось загрузить PDF для данного VIN")
                except Exception as e:
                    await message.reply(f"Произошла ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())