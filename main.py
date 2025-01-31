from pathlib import Path

from environs import Env
from telegram import Update
from telegram.ext import (
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from tools import parse_text


def start(update: Update, context):
    update.message.reply_text("Здравствуйте!")


def echo(update: Update, context):
    update.message.reply_text(update.message.text)


if __name__ == "__main__":
    env = Env()
    env.read_env()
    tg_bot_token = env.str("TG_BOT_TOKEN")
    chat_id = env("TG_CHAT_ID")

    question_file = Path("questions/1vs1200.txt")
    qa_set = parse_text(question_file)

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(
        MessageHandler(Filters.text & ~Filters.command, echo)
    )

    updater.start_polling()
    updater.idle()
