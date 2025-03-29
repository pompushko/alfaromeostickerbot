import os 
import asyncio
import logging
from collections import defaultdict

from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s -  %(message)s'
)

MARKET_THREAD_ID = os.getenv("MARKET_THREAD_ID")
if MARKET_THREAD_ID is not None:
    MARKET_THREAD_ID = int(MARKET_THREAD_ID)
SCAM_WARNING_DELETE_DELAY = int(os.getenv("SCAM_WARNING_DELETE_DELAY", "1800"))
WARNING_DELETE_DELAY = int(os.getenv("WARNING_DELETE_DELAY", "60")) 

monitored_messages = {}
processed_media_groups = set()
media_group_messages = defaultdict(list)

async def monitor_message(bot: Bot, message: Message):
    if message.from_user.is_bot:
        return
    if (message.chat.type not in ['group', 'supergroup'] or 
        message.message_thread_id != MARKET_THREAD_ID):
        return

    media_group_id = message.media_group_id
    
    if media_group_id:
        media_group_messages[media_group_id].append(message)
        
        if media_group_id in processed_media_groups:
            return
        
        if len(media_group_messages[media_group_id]) == 1:
            await asyncio.sleep(0.5) 
            processed_media_groups.add(media_group_id)
            
            first_message = media_group_messages[media_group_id][0]
            message_text = (first_message.text or first_message.caption or '').lower()
            
            message_ids = [msg.message_id for msg in media_group_messages[media_group_id]]
            logger.info(f"Media group {media_group_id} collected: {len(message_ids)} messages, IDs: {message_ids}")
        else:
            message_ids = [msg.message_id for msg in media_group_messages[media_group_id]]
            logger.info(f"Media group {media_group_id} updated: {len(message_ids)} messages, IDs: {message_ids}")
            return
    else:
        message_text = (message.text or message.caption or '').lower()
        first_message = message
        message_ids = [message.message_id]
        logger.info(f"Single message ID: {message.message_id}")

    if '#buy' in message_text or 'куплю' in message_text:
        try:
            warning_msg = await bot.send_message(
                chat_id=message.chat.id,
                reply_to_message_id=first_message.message_id,
                message_thread_id=MARKET_THREAD_ID,
                text="⚠️ <b>Внимание!</b> В чате ошиваются мутные типы, "
                     "которые впаривают товары через своих знакомых. Не ведитесь на эти разводы!",
                parse_mode="HTML"
            )
            
            async def delete_warning_task():
                await asyncio.sleep(SCAM_WARNING_DELETE_DELAY)
                try:
                    await bot.delete_message(message.chat.id, warning_msg.message_id)
                except TelegramBadRequest:
                    pass 
            
            asyncio.create_task(delete_warning_task())
            
        except TelegramBadRequest as e:
            logger.warning(f"Ошибка при отправке предупреждения о мошенниках: {e}")
    
    elif '#buy' not in message_text and '#sell' not in message_text:
        try:
            warning_msg = await bot.send_message(
                chat_id=message.chat.id,
                reply_to_message_id=first_message.message_id,
                message_thread_id=MARKET_THREAD_ID,
                text="В сообщении отсутствуют хэштеги #buy или #sell. "
                     "Сообщение будет удалено через 1 минуту. Разместите объявление согласно правилам.",
                parse_mode="HTML"
            )
            
            async def delete_task():
                await asyncio.sleep(WARNING_DELETE_DELAY)
                message_ids = [msg.message_id for msg in media_group_messages.get(media_group_id, [first_message])]
                all_ids = message_ids + [warning_msg.message_id]
                logger.info(f"Preparing to delete messages for media group {media_group_id or 'single'}: IDs {all_ids}")
                try:
                    await bot.delete_messages(chat_id=message.chat.id, message_ids=all_ids)
                    logger.info(f"Successfully deleted messages: {all_ids}")
                except TelegramBadRequest as e:
                    logger.warning(f"Failed to delete messages: {e}, attempted IDs: {all_ids}")
                    for msg_id in all_ids:
                        try:
                            await bot.delete_message(message.chat.id, msg_id)
                            logger.info(f"Manually deleted message: {msg_id}")
                        except TelegramBadRequest as e:
                            logger.warning(f"Failed to delete message {msg_id}: {e}")
            
            task = asyncio.create_task(delete_task())
            monitored_messages[first_message.message_id] = {
                'task': task,
                'warning_id': warning_msg.message_id
            }
            
        except TelegramBadRequest as e:
            logger.warning(f"Ошибка при мониторинге сообщения: {e}")

async def check_edited_message(bot: Bot, message: Message):
    """Проверка отредактированных сообщений"""
    if message.message_id in monitored_messages:
        message_text = (message.text or message.caption or '').lower()
        if '#buy' in message_text or '#sell' in message_text:
            task_info = monitored_messages.pop(message.message_id)
            task_info['task'].cancel()
            try:
                await bot.delete_message(message.chat.id, task_info['warning_id'])
            except TelegramBadRequest:
                pass