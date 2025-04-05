# delete_vin.py
import logging
from aiogram import types
from aiogram.types import Message
from AsyncDbHandler import AsyncDbHandler

logger = logging.getLogger(__name__)

async def delete_vin(message: Message, vin_pattern, require_admin=True):
    if require_admin:
        try:
            # Получаем информацию о статусе пользователя в чате
            member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
            if member.status not in ['administrator', 'creator']:
                await message.reply("Эта команда доступна только администраторам")
                return
        except Exception as e:
            logger.error(f"Ошибка при проверке прав администратора: {str(e)}")
            await message.reply("Ошибка при проверке прав доступа")
            return    
   
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Использование: /deletevin <VIN>\nПример: /deletevin ZARFANBN2M7642011")
        return
    
    vin = args[1].upper()
    
    if not vin_pattern.match(vin):
        await message.reply("Неверный формат VIN")
        return
    
    try:
        db = AsyncDbHandler()
        msg_id = await db.GetMessageIdByVin(vin)
        if not msg_id:
            await message.reply(f"VIN {vin} не найден в базе данных")
            return
        
        await db.DeleteVin(vin)
        logger.info(f"VIN {vin} удален пользователем {message.from_user.id}")
        await message.reply(f"VIN {vin} успешно удален из базы данных")
        
    except Exception as e:
        logger.error(f"Ошибка при удалении VIN {vin}: {str(e)}")
        await message.reply(f"Произошла ошибка при удалении VIN: {str(e)}")