from aiogram.types import CallbackQuery
from SendPhoto import send_photos  

async def handle_photos_callback(callback_query: CallbackQuery, bot, get_image):
    vin = callback_query.data.split(":")[1]
    await callback_query.answer()
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=None
    )    
    try:
        await send_photos(
            bot=bot,
            vin=vin,
            chat_id=callback_query.message.chat.id,
            reply_to_message_id=callback_query.message.message_id,
            get_image=get_image
        )
    except Exception as e:
        await callback_query.answer(f"Ошибка: {str(e)}")