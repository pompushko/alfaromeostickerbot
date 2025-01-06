import asyncio
from aiogram import Bot
from aiogram.types import BufferedInputFile, InputMediaPhoto
from aiogram.exceptions import TelegramRetryAfter
import re

MAX_IMAGES_PER_ALBUM = 10


async def send_photos(bot: Bot, vin: str, chat_id: int, reply_to_message_id: int, get_image):
    try:
        images, lot_url = await get_image(vin)
        if images:
            images = images[:MAX_IMAGES_PER_ALBUM]
            media_group = []
            media_group = [
                InputMediaPhoto(
                    media=BufferedInputFile(image.read(), filename=f"{vin}_{idx + 1}.jpg"),
                )
                for idx, image in enumerate(images)
            ]
            for attempt in range(3):
                try:
                    await bot.send_media_group(
                        chat_id=chat_id,
                        media=media_group,
                        reply_to_message_id=reply_to_message_id,
                    )
                    break
                except TelegramRetryAfter as e:
                    retry_after = e.retry_after
                    print(f"Flood control error: retrying after {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                    continue
        else:
            await bot.send_message(chat_id, "Фотографии для данного VIN не найдены.")
    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка при отправке фотографий: {str(e)}")
    return lot_url
