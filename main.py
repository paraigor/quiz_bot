import random
from pathlib import Path

import redis
from environs import Env
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from tools import parse_text


def start(update: Update, context):
    reply_keyboard = [["Новый вопрос", "Сдаться"], ["Мой счёт"]]
    update.message.reply_text(
        "Здравствуйте!",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
            is_persistent=True,
        ),
    )


def echo(update: Update, context):
    text = update.message.text
    if text == "Новый вопрос":
        user_id = str(update.effective_chat.id)
        question = random.choice(list(qa_set.keys()))
        db_connection.set(user_id, question)
        db_question = str(db_connection.get(user_id))
        update.message.reply_text(db_question)


if __name__ == "__main__":
    env = Env()
    env.read_env()

    tg_bot_token = env.str("TG_BOT_TOKEN")
    chat_id = env("TG_CHAT_ID")
    db_host = env.str("REDIS_DB_HOST")
    db_port = env.int("REDIS_DB_PORT")
    db_user = env.str("REDIS_DB_USERNAME", "default")
    db_pass = env.str("REDIS_DB_PASSWORD")

    db_connection = redis.Redis(
        host=db_host,
        port=db_port,
        username=db_user,
        password=db_pass,
        decode_responses=True,
    )

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
