from aiogram.types import CallbackQuery
from SendPhoto import send_photos  
from GetImage import get_image

async def handle_photos_callback(callback_query: CallbackQuery, bot, get_image):
    vin = callback_query.data.split(":")[1]
    await callback_query.answer()

    try:
        _, lot_url = await get_image(vin)
        original_caption = callback_query.message.caption

        updated_caption = (
            f"{original_caption}\n\n"
            f"<b>Ссылка на лот:</b>\n\n"
            f'<a href="{lot_url}"><u>ТЫЦ</u></a>'
        )

        await bot.edit_message_caption(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            caption=updated_caption,
            parse_mode="HTML",
            reply_markup=None  # Убираем клавиатуру
        )
        await send_photos(
            bot=bot,
            vin=vin,
            chat_id=callback_query.message.chat.id,
            reply_to_message_id=callback_query.message.message_id,
            get_image=get_image
        )
    except Exception as e:
        await callback_query.answer(f"Ошибка: {str(e)}")