from telegram import Update
import os
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

ALLOWED_USER_ID = int(os.getenv('ALLOWED_USER_ID'))


async def is_authorized(update: Update) -> bool:
    """Перевіряє, чи є користувач авторизованим."""
    if update.effective_user.id != ALLOWED_USER_ID:
        logger.error('User NOT Authorized')
        await update.message.reply_text("⛔ Not available for the user.")
        return False
    
    # logger.info('User Authorized')
    return True