import logging
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

from log_handler import TgLogHandler
from tools import parse_text

logger = logging.getLogger(__file__)


def start(update: Update, context):
    chat_id_str = str(update.effective_chat.id)
    reply_keyboard = [["Новый вопрос", "Сдаться"], ["Мой счёт"]]

    try:
        update.message.reply_text(
            "Приветствуем на нашей викторине!\nДля начала нажми [Новый вопрос]",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard,
                resize_keyboard=True,
                is_persistent=True,
            ),
        )
    except Exception as err:
        logger.info("Бот Телаграм упал с ошибкой:")
        logger.error(err)

    db_connection.set(chat_id_str, "")


def handle_new_question_request(update: Update, context):
    chat_id_str = str(update.effective_chat.id)
    question = random.choice(list(qa_set.keys()))
    db_connection.set(chat_id_str, question)
    try:
        update.message.reply_text(question)
    except Exception as err:
        logger.info("Бот Телаграм упал с ошибкой:")
        logger.error(err)

    return "SOLUTION_ATTEMPT"


def handle_solution_attempt(update: Update, context):
    message = update.message.text.replace("\n", " ").strip().lower()
    chat_id_str = str(update.effective_chat.id)
    question = db_connection.get(chat_id_str)

    answer = qa_set.get(question)
    if answer:
        answer = answer.lower()
        short_answer = answer.split(".")[0].split("(")[0].strip().lower()

    if message == short_answer or message == answer:
        try:
            update.message.reply_text(
                "Правильно! Поздравляю!\nДля следующего вопроса нажми [Новый вопрос]"
            )
        except Exception as err:
            logger.info("Бот Телаграм упал с ошибкой:")
            logger.error(err)
        db_connection.set(chat_id_str, "")

        return ConversationHandler.END
    else:
        try:
            update.message.reply_text("Неправильно… Попробуешь ещё раз?")
        except Exception as err:
            logger.info("Бот Телаграм упал с ошибкой:")
            logger.error(err)


def handle_giveup_request(update: Update, context):
    chat_id_str = str(update.effective_chat.id)
    question = db_connection.get(chat_id_str)
    answer = qa_set.get(question)
    try:
        update.message.reply_text(f"Правильный ответ: {answer}")
    except Exception as err:
        logger.info("Бот Телаграм упал с ошибкой:")
        logger.error(err)
    db_connection.set(chat_id_str, "")

    handle_new_question_request(update, context)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    env = Env()
    env.read_env()

    tg_bot_token = env.str("TG_BOT_TOKEN")
    admin_chat_id = env("TG_CHAT_ID")
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
                    ),
                ],
            },
            fallbacks=[],
        )
    )
    dispatcher.add_handler(CommandHandler("start", start))

    logger.addHandler(TgLogHandler(updater.bot, admin_chat_id))
    logger.info("Бот Телаграм запущен")

    updater.start_polling()
    updater.idle()
