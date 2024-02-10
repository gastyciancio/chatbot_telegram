from telegram.ext import *
import chatbot.response as Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import pdb
import sys
import os
from chatbot.utils import answers_reset, create_answers_file
from qa_autocomplete.utils import  templates_update, logger
sys.path.insert(0, './scripts')
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

load_dotenv()

print('Bot started....')

QAWIKI_ENDPOINT = os.environ.get("QAWIKI_ENDPOINT")
QAWIKI_ENTITY_PREFIX = os.environ.get("QAWIKI_ENTITY_PREFIX")
JOB_INTERVAL_MINUTES = int(os.environ.get("JOB_INTERVAL_MINUTES"))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Type a question to start')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('You have to send question in English starting with "what","which", "where", "when", "how", "is", "did", "do", "in", "who", "on" ,"kim", "from", "has", "was" or "are"')

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')
    await update.message.reply_text('An unexpected error happened')

async def templates_update_function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    templates_update(QAWIKI_ENDPOINT, QAWIKI_ENTITY_PREFIX, logger)
    await update.message.reply_text('Updated templates')

async def answers_reset_function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answers_reset()
    await update.message.reply_text('Reseted answers')

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = str(update.message.text).lower()
    context.user_data['input'] = text
    context.user_data['search_similar'] = True
    response = Response.respond_to(text, context)
    if len(response['analogous_questions']) == 0 and len(response['general_questions']) == 0 and response['ask_for_add_alias'] == False:
        await update.message.reply_text(response['answer'][:4096])
    else:
        if response['ask_for_add_alias'] == True:
            final_text = response['answer'][:4096]
        else:
            final_text = response['answer'] + '\n Maybe these next questions will be useful to you:'
            context.user_data['search_similar'] = False

        await update.message.reply_text(final_text, reply_markup= await build_markup(response))

async def option_selected(update: Update, context: CallbackContext):
    search_similar = context.user_data.get('search_similar')
    if search_similar == False:
        context.user_data['search_similar'] = True
    query = update.callback_query
    await query.answer()

    text = str(query.data).lower()
    response = Response.respond_to(text, context)
    if len(response['analogous_questions']) == 0 and len(response['general_questions']) == 0 and response['ask_for_add_alias'] == False:
        await update.callback_query.message.reply_text(response['answer'][:4096])
    else:
        if response['ask_for_add_alias'] == True:
            final_text = response['answer'][:4096]
        else:
            final_text = response['answer'] + '\n Maybe these questions will be useful to you:'
            context.user_data['search_similar'] = False
        
        await update.callback_query.message.reply_text(final_text, reply_markup=await build_markup(response))

async def build_markup(response):
    keyboard = []


    if response['ask_for_add_alias'] == True:
        keyboard.append([InlineKeyboardButton('The answer was helpful', callback_data='it was helpful')])
        keyboard.append([InlineKeyboardButton('This did not help me', callback_data='it was not helpful')])
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

    create_answers_file()
    sched = BackgroundScheduler()
    sched.add_job(templates_update, 'interval', args=[QAWIKI_ENDPOINT, QAWIKI_ENTITY_PREFIX, logger], minutes=JOB_INTERVAL_MINUTES, next_run_time=datetime.datetime.now())
    sched.add_job(answers_reset, 'interval', minutes=JOB_INTERVAL_MINUTES, next_run_time=datetime.datetime.now() + datetime.timedelta(minutes=5) )
    sched.start()

    try:
        app = ApplicationBuilder().token(os.environ.get("API_KEY_TELEGRAM")).build()

        app.add_handler(CommandHandler('start', start_command))
        app.add_handler(CommandHandler('help', help_command))
        app.add_handler(CommandHandler('templates_update', templates_update_function))
        app.add_handler(CommandHandler('answers_reset', answers_reset_function))

        app.add_handler(MessageHandler(filters.ALL, handle_messages))
        app.add_handler(CallbackQueryHandler(option_selected))

        app.add_error_handler(error)

        app.run_polling()
    except (KeyboardInterrupt, SystemExit):
        sched.shutdown()
 

main()
