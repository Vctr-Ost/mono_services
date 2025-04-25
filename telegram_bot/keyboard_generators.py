from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
import logging
import os
from dotenv import load_dotenv
from backend_interaction import query_get_json_async

load_dotenv()
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv('BACKEND_URL')
KEYBOARD_ROW_LEN = int(os.getenv('KEYBOARD_ROW_LEN'))


async def get_category_keyboard(amount=None):
    """
    1. Функція дістає список категорій по АПІ
    2. Додає у кінець списку категорію 'New category'
    3. Повертає клавіатуру
    """
    logging.info(f'Function started')

    categories = await query_get_json_async(f'{BACKEND_URL}/get_categories')    # Отримуємо список категорії по АПІ
    categories.append('New category')                                           # Додаємо останнім пунктом "Нова категорія"

    chunks_list = [categories[i:i+3] for i in range(0, len(categories), KEYBOARD_ROW_LEN)]
    keyboard = [[InlineKeyboardButton(cat, callback_data=f'updCat_{cat}') for cat in chunk] for chunk in chunks_list]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if amount is None:
        message = 'Please choose category:'
    else:
        message = f'Amount updated to {amount}. Please choose category:'
        
    return [message, reply_markup]


async def get_subcat_msg_and_keyboard(category):
    logging.info(f'Function started')
    SUBCATEGORIES_URI = f'{BACKEND_URL}/get_sub_categories/{category}'
    sub_categories = await query_get_json_async(SUBCATEGORIES_URI)          # Отримуємо список субкатегорій по АПІ
    sub_categories.append('New subCategory')                                # Додаємо останнім пунктом "Нова субКатегорія"

    # Формуємо клавіатуру (кожна кнопка починається із "updTrn_")
    chunks_list = [sub_categories[i:i+3] for i in range(0, len(sub_categories), KEYBOARD_ROW_LEN)]
    keyboard = [[InlineKeyboardButton(subCat, callback_data=f'updSubCat_{subCat}') for subCat in chunk] for chunk in chunks_list]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = f'Category updated to {category}. Please choose subCategory:'

    return [message, reply_markup]


async def get_comment_msg_and_keyboard(sub_category):
    logging.info(f'Function started')
    keyboard = [[InlineKeyboardButton('Without comment', callback_data=f'updComment_without')], [InlineKeyboardButton('Add comment', callback_data=f'updComment_add')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = f'SubCategory updated to {sub_category}. What about comment?'
    return [message, reply_markup]