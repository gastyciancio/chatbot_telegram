import constants as keys
from telegram.ext import *
import responses as Responses
from telegram import Update

print('Bot started....')


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Escribi algo para empezar')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Preguntale a google')

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')
    await update.message.reply_text("Ocurrio un error")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = str(update.message.text).lower()
    response = Responses.respond_to(text)

    await update.message.reply_text(response)


def main():
    app = ApplicationBuilder().token(keys.API_KEY).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(MessageHandler(filters.ALL, handle_messages))

    app.add_error_handler(error)

    app.run_polling()
 

main()
