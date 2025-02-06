import logging
import random

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
from tools import fill_db_with_questions

logger = logging.getLogger(__file__)


def start(update: Update, context):
    db = context.bot_data["db"]
    chat_id = f"tg-{str(update.effective_chat.id)}"
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

    db.set(chat_id, "")


def handle_new_question_request(update: Update, context):
    db = context.bot_data["db"]
    chat_id = f"tg-{str(update.effective_chat.id)}"
    questions_total = int(db.get("questions_total"))
    question_number = f"{random.randint(1, questions_total):03}"
    question = db.hget(f"question:{question_number}", "question")
    db.set(chat_id, question_number)
    try:
        update.message.reply_text(question)
    except Exception as err:
        logger.info("Бот Телаграм упал с ошибкой:")
        logger.error(err)

    return "SOLUTION_ATTEMPT"


def handle_solution_attempt(update: Update, context):
    db = context.bot_data["db"]
    message = update.message.text.replace("\n", " ").strip().lower()
    chat_id = f"tg-{str(update.effective_chat.id)}"
    question_number = db.get(chat_id)
    answer = db.hget(f"question:{question_number}", "answer")
    if answer:
        answer = answer.lower()
        short_answer = answer.split(".")[0].split("(")[0].strip().lower()

    if message == short_answer or message == answer:
        try:
            db.set(chat_id, "")
            update.message.reply_text(
                "Правильно! Поздравляю!\nДля следующего вопроса нажми [Новый вопрос]"
            )
        except Exception as err:
            logger.info("Бот Телаграм упал с ошибкой:")
            logger.error(err)

        return ConversationHandler.END
    else:
        try:
            update.message.reply_text("Неправильно… Попробуешь ещё раз?")
        except Exception as err:
            logger.info("Бот Телаграм упал с ошибкой:")
            logger.error(err)


def handle_giveup_request(update: Update, context):
    db = context.bot_data["db"]
    chat_id = f"tg-{str(update.effective_chat.id)}"
    question_number = db.get(chat_id)
    answer = db.hget(f"question:{question_number}", "answer")
    try:
        update.message.reply_text(f"Правильный ответ: {answer}")
    except Exception as err:
        logger.info("Бот Телаграм упал с ошибкой:")
        logger.error(err)
    db.set(chat_id, "")

    handle_new_question_request(update, context)


def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    env = Env()
    env.read_env()

    tg_bot_token = env.str("TG_BOT_TOKEN")
    admin_chat_id = env("TG_CHAT_ID")

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data["db"] = fill_db_with_questions()
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


if __name__ == "__main__":
    main()
