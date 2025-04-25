from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
import requests
import os
import json
import asyncio
import math
import time
from datetime import datetime, timezone, timedelta
from backend_interaction import query_get_json_async, query_put
from keyboard_generators import get_category_keyboard, get_subcat_msg_and_keyboard, get_comment_msg_and_keyboard
from service_functions import is_authorized
import logging

from dotenv import load_dotenv
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BACKEND_URL = os.getenv('BACKEND_URL')

CUSTOM_AMOUNT, CATEGORY_NAME, SUB_CATEGORY_NAME, COMMENT_NAME = range(4)
KEYBOARD_ROW_LEN = 3


logging.basicConfig(
    level=logging.INFO,  # Рівень логів (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(levelname)s : %(asctime)s : %(name)s : %(funcName)s : %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def start(update: Update, context: CallbackContext):
    logging.info(f'Function started')
    if not await is_authorized(update):
        return
    
    keyboard = [['🔄 Update', '➕ Add transaction']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    logging.info('Welcome message printing')
    await update.message.reply_text('Welcome!', reply_markup=reply_markup)
    logging.info('"load_last_trn" function starting')
    await load_last_trn(update, context)


async def add_custom_trn(update: Update, context: CallbackContext):
    logging.info(f'Function started')
    if not await is_authorized(update):
        return

    unix_ts = int(datetime.now().timestamp())
    context.user_data['trn_unix'] = unix_ts

    dt = datetime.fromtimestamp(unix_ts) + timedelta(hours=2)
    context.user_data['ts'] = dt.strftime("%Y-%m-%d %H:%M:%S.%f %z")

    context.user_data['trn_id'] = f'custom_{unix_ts}'

    print('[INFO] - Function add_custom_trn triggered')

    await context.bot.send_message(chat_id=update.effective_chat.id, text='Please enter transaction amount:')
    return CUSTOM_AMOUNT
    


async def load_last_trn(update: Update, context: CallbackContext):
    logging.info('-'*100)
    logging.info(f'Function started')
    URI = f'{BACKEND_URL}/get_last_trn'

    while True:
        resp = await query_get_json_async(URI)
        
        if isinstance(resp, dict):
            logging.info(f'resp: {resp}')
            logging.info(f'len(resp): {len(resp)}')
            if len(resp) == 0:
                logging.info('asleep 10 sec')
                await asyncio.sleep(10)
            else:
                context.user_data['trn_id'] = resp['trn_id']    # to update correct transaction later

                message = f"""🙀 New unknown transaction 🙀\n
🗓 Date: {resp['dt']}\n
💰 Amount: {resp['amount']}\n
📜 Description: {resp['bank_description']}, {resp['mcc_group_description']} ({resp['mcc_short_description']})"""
                
                keyboard = [[InlineKeyboardButton('Choose category', callback_data='chooseCategory')]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await context.bot.send_message(chat_id=update.effective_chat.id, text=message, reply_markup=reply_markup)
                break
        elif resp is None:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Troubles with DB')








# async def get_category_keyboard():
#     """
#     1. Функція дістає список категорій по АПІ
#     2. Додає у кінець списку категорію 'New category'
#     3. Повертає клавіатуру
#     """
#     logging.info(f'Function started')
#     URI = f'{BACKEND_URL}/get_categories'
#     categories = await query_get_json_async(URI)    # Отримуємо список категорії по АПІ
#     categories.append('New category')               # Додаємо останнім пунктом "Нова категорія"
#     chunks_list = [categories[i:i+3] for i in range(0, len(categories), KEYBOARD_ROW_LEN)]
#     keyboard = [[InlineKeyboardButton(cat, callback_data=f'updCat_{cat}') for cat in chunk] for chunk in chunks_list]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     message = 'Please choose category'
#     return [message, reply_markup]


# async def get_subcat_msg_and_keyboard(category):
#     logging.info(f'Function started')
#     SUBCATEGORIES_URI = f'{BACKEND_URL}/get_sub_categories/{category}'
#     sub_categories = await query_get_json_async(SUBCATEGORIES_URI)          # Отримуємо список субкатегорій по АПІ
#     sub_categories.append('New subCategory')                                # Додаємо останнім пунктом "Нова субКатегорія"
#     chunks_list = [sub_categories[i:i+3] for i in range(0, len(sub_categories), KEYBOARD_ROW_LEN)]

#     # Формуємо клавіатуру (кожна кнопка починається із "updTrn_")
#     keyboard = [[InlineKeyboardButton(subCat, callback_data=f'updSubCat_{subCat}') for subCat in chunk] for chunk in chunks_list]
#     reply_markup = InlineKeyboardMarkup(keyboard)

#     message = f'Category updated to {category}. Choose subCategory:'

#     return [message, reply_markup]


# async def get_comment_msg_and_keyboard(sub_category):
#     logging.info(f'Function started')
#     keyboard = [[InlineKeyboardButton('Without comment', callback_data=f'updComment_without')], [InlineKeyboardButton('Add comment', callback_data=f'updComment_add')]]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     message = f'SubCategory updated to {sub_category}. What about comment?'
#     return [message, reply_markup]


async def upd_trn(update: Update, context: CallbackContext):
    logging.info(f'Function started')

    data = {
        "set_dict": {
            "category": context.user_data['trn_category'],
            "sub_category": context.user_data['trn_sub_category'],
            "comment": context.user_data['trn_comment'],
            "handle_marker": "False"
        }
    }

    logging.info('-'*20)
    logging.info(context.user_data)
    
    if context.user_data["trn_id"].startswith('custom_'):
        data['set_dict']['trn_id'] = context.user_data['trn_id']
        data['set_dict']['trn_unix'] = str(context.user_data['trn_unix'])
        data['set_dict']['ts'] = context.user_data['ts']
        data['set_dict']['amount'] = str(context.user_data['amount'])

        UPD_URI = f'{BACKEND_URL}/insert_custom_trn'

        logging.info(f'UPD_URI == {UPD_URI}')
        logging.info(f'data == {data}')
        await query_put(UPD_URI, data)
        return '✅ Transaction created!'
    else:
        UPD_URI = f'{BACKEND_URL}/update_trn/{context.user_data["trn_id"]}'
        await query_put(UPD_URI, data)
        return '✅ Transaction updated!'




async def btn_callback(update: Update, context: CallbackContext):
    if not await is_authorized(update):
        return
    logging.info(f'Function started')
    
    query = update.callback_query
    await query.answer()
    
    if query.data == 'chooseCategory':
        reply_markup = await get_category_keyboard()
        await query.edit_message_reply_markup(reply_markup=reply_markup[1])

    # Відловлюємо натискання на кнопку обирання категорії транзакції
    elif query.data.startswith('updCat_'):
        PICKED_CATEGORY = query.data.split('_')[1]

        if PICKED_CATEGORY == 'New category':
            await query.edit_message_reply_markup(None)
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Please enter the name of the new category:')
            return CATEGORY_NAME
        else:
            context.user_data['trn_category'] = PICKED_CATEGORY
            subcat_data = await get_subcat_msg_and_keyboard(PICKED_CATEGORY)
            await query.edit_message_reply_markup(None)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=subcat_data[0], reply_markup=subcat_data[1])

    elif query.data.startswith('updSubCat_'):
        PICKED_SUB_CATEGORY = query.data.split('_')[1]

        if PICKED_SUB_CATEGORY == 'New subCategory':
            await query.edit_message_reply_markup(None)
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Please enter the name of the new subCategory:')
            return SUB_CATEGORY_NAME
        else:
            context.user_data['trn_sub_category'] = PICKED_SUB_CATEGORY
            comment_data = await get_comment_msg_and_keyboard(PICKED_SUB_CATEGORY)
            await query.edit_message_reply_markup(None)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=comment_data[0], reply_markup=comment_data[1])
            
    elif query.data.startswith('updComment_'):
        ADD_COMMENT_MARKER =  True if query.data.split('_')[1] == 'add' else False
        print(ADD_COMMENT_MARKER)

        if ADD_COMMENT_MARKER:
            await query.edit_message_reply_markup(None)
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Please enter the comment to the transaction:')
            return COMMENT_NAME
        else:
            context.user_data['trn_comment'] = ''
            resp_msg = await upd_trn(update, context)
            await query.edit_message_reply_markup(None)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=resp_msg)
            await load_last_trn(update, context)





async def button_response(update: Update, context: CallbackContext):
    if not await is_authorized(update):
        return
    logging.info(f'Function started')
    
    user_message = update.message.text
    logging.info(f'User clicked {user_message}')

    if user_message == '🔄 Update':
        await start(update, context)
    else:
        await update.message.reply_text('Unknown command :(')



# Хендлер інпутів користувача коли ми опитуємо його текстовими повідомленнями
async def handle_user_input(update: Update, context: CallbackContext, field_name: str, next_step_func):
    logging.info(f'Function handle_user_input started. field_name: {field_name}, next_step_func: {next_step_func}.')

    if await is_authorized(update):
        context.user_data[field_name] = update.message.text  # Отримуємо введений текст
        print(f'field == {context.user_data[field_name]}')

        if next_step_func:
            next_step_data = await next_step_func(update.message.text)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=next_step_data[0], reply_markup=next_step_data[1])
        elif field_name == 'amount':
            print(f'_ _ _ {field_name} == {context.user_data[field_name]}')
            return CATEGORY_NAME
        else:
            resp_msg = await upd_trn(update, context)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=resp_msg)
            await load_last_trn(update, context)

    return ConversationHandler.END




async def get_transaction_amount(update: Update, context: CallbackContext):
    logging.info(f'Function started')
    try:
        context.user_data['amount'] = float(update.message.text)
        reply_markup = await get_category_keyboard()
        
        logging.info(f'Amount saved. Sending message about category')
        await update.message.reply_text(
            f"Transaction amount: {context.user_data['amount']}. Please choose the category:",
            reply_markup=reply_markup[1]
        )
        
        return ConversationHandler.END
        # return CATEGORY_NAME  # Переходимо до вибору категорії
        
    except ValueError:
        logging.info(f'Value error. Please enter the number (Ex: 100 or 50.5)')
        await update.message.reply_text("Please enter the number (Ex: 100 or 50.5)")
        return CUSTOM_AMOUNT




async def get_category_name(update: Update, context: CallbackContext):
    logging.info(f'Function started')
    return await handle_user_input(update, context, 'trn_category', get_subcat_msg_and_keyboard)

async def get_sub_category_name(update: Update, context: CallbackContext):
    logging.info(f'Function started')
    return await handle_user_input(update, context, 'trn_sub_category', get_comment_msg_and_keyboard)

async def get_comment_name(update: Update, context: CallbackContext):
    logging.info(f'Function started')
    return await handle_user_input(update, context, 'trn_comment', None)




def main():
    print('app start')
    logging.info('-'*100)
    logging.info("Bot started!")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^➕ Add transaction$'), add_custom_trn),
            CallbackQueryHandler(btn_callback)
        ],  
        states={
            CUSTOM_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_transaction_amount)],
            CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category_name)],
            SUB_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_sub_category_name)],
            COMMENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_comment_name)],
        },
        fallbacks=[]
    )


    app.add_handler(CommandHandler("start", start))

    # app.add_handler(CallbackQueryHandler(btn_callback))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_response))

    app.run_polling()


if __name__ == "__main__":
    main()
