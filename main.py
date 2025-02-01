import random
from pathlib import Path

import redis
from environs import Env
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)

from tools import parse_text


def start(update: Update, context):
    chat_id_str = str(update.effective_chat.id)
    reply_keyboard = [["Новый вопрос", "Сдаться"], ["Мой счёт"]]
    update.message.reply_text(
        "Приветствуем на нашей викторине! Для начала нажми [Новый вопрос]",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
            is_persistent=True,
        ),
    )
    db_connection.set(chat_id_str, "")


def handle_new_question_request(update: Update, context):
    chat_id_str = str(update.effective_chat.id)
    question = random.choice(list(qa_set.keys()))
    db_connection.set(chat_id_str, question)
    update.message.reply_text(question)

    return "SOLUTION_ATTEMPT"


def handle_solution_attempt(update: Update, context):
    text = update.message.text.replace("\n", " ").strip().lower()
    chat_id_str = str(update.effective_chat.id)
    question = db_connection.get(chat_id_str)

    answer = qa_set[question].lower()
    short_answer = answer.split(".")[0].split("(")[0].strip().lower()

    if text == short_answer or text == answer:
        update.message.reply_text(
            "Правильно! Поздравляю! Для следующего вопроса нажми [Новый вопрос]"
        )
        db_connection.set(chat_id_str, "")

        return ConversationHandler.END
    else:
        update.message.reply_text("Неправильно… Попробуешь ещё раз?")


def handle_giveup_request(update: Update, context):
    chat_id_str = str(update.effective_chat.id)
    question = db_connection.get(chat_id_str)
    answer = qa_set[question]
    update.message.reply_text(
        f"Правильный ответ: {answer}"
    )
    db_connection.set(chat_id_str, "")

    handle_new_question_request(update, context)


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
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[
                MessageHandler(
                    Filters.regex(r"^Новый вопрос$"),
                    handle_new_question_request,
                )
            ],
            states={
                "SOLUTION_ATTEMPT": [
                    MessageHandler(
                        Filters.regex(r"^Сдаться$"),
                        handle_giveup_request,
                    ),
                    MessageHandler(
                        Filters.text,
                        handle_solution_attempt,
                    )
                ],
            },
            fallbacks=[],
        )
    )
    dispatcher.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()
