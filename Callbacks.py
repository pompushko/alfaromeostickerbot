from aiogram.types import CallbackQuery
from SendPhoto import send_photos  
from GetImage import get_image

async def handle_photos_callback(callback_query: CallbackQuery, bot, get_image):
    vin = callback_query.data.split(":")[1]
    await callback_query.answer()

    try:
        # Получение ориг сообщения
        original_caption = callback_query.message.caption

        # Вставляем текст о поиске
        progress_caption = (
            f"{original_caption}\n\n"
            f"<b>Идет поиск фотографий...</b> 🔄"
        )
        await bot.edit_message_caption(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            caption=progress_caption,
            parse_mode="HTML",
        )

        # Получение ссылки (по хорошему переделать без получения урл картинок)
        _, lot_url = await get_image(vin)
        # Убираем инфу о поиске. Вставляем ссылку на лот

        send_photo_caption = (
            f"{original_caption}\n\n"
            f"<b>Ссылка на лот:</b>\n\n"
            f'<a href="{lot_url}"><u>ТЫЦ</u></a>\n\n'
            f"<b>Нашел фотографии. Отправляю...</b>\n\n"
        )
        await bot.edit_message_caption(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            caption=send_photo_caption,
            parse_mode="HTML",
            reply_markup=None
        )

        # Отправка фотографий. 
        await send_photos(
            bot=bot,
            vin=vin,
            chat_id=callback_query.message.chat.id,
            reply_to_message_id=callback_query.message.message_id,
            get_image=get_image
        )
        # Убираем инфу что нашли. 
        final_caption = (
            f"{original_caption}\n\n"
            f"<b>Ссылка на лот:</b>\n\n"
            f'<a href="{lot_url}"><u>ТЫЦ</u></a>\n\n'
        )
        await bot.edit_message_caption(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            caption=final_caption,
            parse_mode="HTML",
            reply_markup=None
        )             
    except Exception as e:
        # Если ошибка
        error_caption = (
            f"{original_caption}\n\n"
            f"<b>Ошибка:</b> {str(e)} ❌"
        )
        await bot.edit_message_caption(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            caption=error_caption,
            parse_mode="HTML",
        )
