from telegram.ext import *
import chatbot.response as Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import pdb
import sys
import os
from chatbot.utils import answers_reset
from qa_autocomplete.utils import  templates_update, logger
sys.path.insert(0, './scripts')
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

load_dotenv()

print('Bot started....')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Type a question to start')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Ask Google')

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')
    await update.message.reply_text('An unexpected error happened')

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = str(update.message.text).lower()
    context.user_data['input'] = text
    context.user_data['search_similar'] = True
    response = Response.respond_to(text, None)
    if len(response['analogous_questions']) == 0 and len(response['general_questions']) == 0 and len(response['posibles_entities']) == 0:
        await update.message.reply_text(response['answer'])
    else:
        if len(response['posibles_entities']) > 0:
            final_text = 'Tell me which entity were u trying to refer:'
        else:
            final_text = response['answer'] + ' Maybe these questions will be useful to you:'
            context.user_data['search_similar'] = False

        await update.message.reply_text(final_text, reply_markup= await build_markup(response))

async def option_selected(update: Update, context: CallbackContext):
    previous_question = context.user_data.get('input')
    search_similar = context.user_data.get('search_similar')
    if search_similar == False:
        previous_question = None
        context.user_data['search_similar'] = True
    query = update.callback_query
    await query.answer()

    text = str(query.data).lower()
    response = Response.respond_to(text, previous_question)
    if len(response['analogous_questions']) == 0 and len(response['general_questions']) == 0 and len(response['posibles_entities']) == 0:
        await query.edit_message_text(text=response['answer'])
    else:
        if len(response['posibles_entities']) > 0:
            final_text = 'Tell me which entity were u trying to refer:'
        else:
            final_text = response['answer'] + ' Maybe these questions will be useful to you:'
            context.user_data['search_similar'] = False
        
        await update.callback_query.message.reply_text(final_text, reply_markup=await build_markup(response))

async def build_markup(response):
    keyboard = []

    if len(response['posibles_entities']) > 0:
        for posibles_entity in response['posibles_entities']:
            option = [InlineKeyboardButton(posibles_entity['description'].capitalize(), callback_data=posibles_entity['id'])]
            keyboard.append(option)
        keyboard.append([InlineKeyboardButton('No one of them', callback_data='No one of them')])
    else:
        for analogous_question in response['analogous_questions']:
            option = [InlineKeyboardButton(analogous_question.capitalize(), callback_data=analogous_question)]
            keyboard.append(option)
        
        for general_question in response['general_questions']:
            option =  [InlineKeyboardButton(general_question.capitalize(), callback_data=general_question)]
            keyboard.append(option)

        keyboard.append([InlineKeyboardButton('Bye', callback_data='Bye')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup

def main():

    QAWIKI_ENDPOINT = os.environ.get("QAWIKI_ENDPOINT")
    QAWIKI_ENTITY_PREFIX = os.environ.get("QAWIKI_ENTITY_PREFIX")
    JOB_INTERVAL_MINUTES = int(os.environ.get("JOB_INTERVAL_MINUTES"))

    #sched = BackgroundScheduler(daemon=True)
    #sched.add_job(templates_update, 'interval', args=[QAWIKI_ENDPOINT, QAWIKI_ENTITY_PREFIX, logger], minutes=JOB_INTERVAL_MINUTES, next_run_time=datetime.datetime.now())
    #sched.start()
    #sched2 = BackgroundScheduler(daemon=True)
    #sched2.add_job(answers_reset, 'interval', minutes=JOB_INTERVAL_MINUTES, next_run_time=datetime.datetime.now())
    #sched2.start()

    app = ApplicationBuilder().token(os.environ.get("API_KEY_TELEGRAM")).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))

    app.add_handler(MessageHandler(filters.ALL, handle_messages))
    app.add_handler(CallbackQueryHandler(option_selected))

    app.add_error_handler(error)

    app.run_polling()
 

main()
