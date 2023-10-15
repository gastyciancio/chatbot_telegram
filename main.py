import constants as keys
from telegram.ext import *
import responses as Responses
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import pdb

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
    response = Responses.respond_to(text)
    if len(response['analogous_questions']) == 0 and len(response['general_questions']) == 0 and len(response['similar_questions']) == 0:
        await update.message.reply_text(response['answer'])
    else:
        final_text = response['answer'] + ' Maybe these questions will be useful to you:'

        await update.message.reply_text(final_text, reply_markup= await build_markup(response, text))

async def option_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    text = str(query.data).lower()
    response = Responses.respond_to(text)
    if len(response['analogous_questions']) == 0 and len(response['general_questions']) == 0 and len(response['similar_questions']) > 0:
        await query.edit_message_text(text=response['answer'])
    else:
        final_text = response['answer'] + ' Maybe these questions will be useful to you:'
        
        await update.callback_query.message.reply_text(final_text, reply_markup=await build_markup(response, text))

async def build_markup(response, question):
    keyboard = []

    if len(response['similar_questions']) > 0:
        for similar_question in response['similar_questions']:
            option = [InlineKeyboardButton(similar_question[0], callback_data=similar_question[0] + '_similar_to_question_'+ question)]
            keyboard.append(option)
        keyboard.append([InlineKeyboardButton('It does not help me', callback_data='It does not help me for: '+ question.capitalize())])
   
    else:
        for analogous_question in response['analogous_questions']:
            option = [InlineKeyboardButton(analogous_question, callback_data=analogous_question)]
            keyboard.append(option)
        
        for general_question in response['general_questions']:
            option =  [InlineKeyboardButton(general_question, callback_data=general_question)]
            keyboard.append(option)

        keyboard.append([InlineKeyboardButton('Bye', callback_data='Bye')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup

def main():
    app = ApplicationBuilder().token(keys.API_KEY).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))

    app.add_handler(MessageHandler(filters.ALL, handle_messages))
    app.add_handler(CallbackQueryHandler(option_selected))

    app.add_error_handler(error)

    app.run_polling()
 

main()
