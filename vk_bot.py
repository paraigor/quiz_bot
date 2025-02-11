import logging
import random

import telegram
import vk_api
from environs import Env
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id

from log_handler import TgLogHandler
from tools import connect_to_db, fill_db_with_questions

logger = logging.getLogger(__file__)


def start(event, vk_api):
    user_id = event.user_id
    db_user_id = f"vk-{str(user_id)}"
    keyboard = VkKeyboard()
    keyboard.add_button("Новый вопрос", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("Сдаться", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("Мой счёт", color=VkKeyboardColor.SECONDARY)

    try:
        vk_api.messages.send(
            user_id=user_id,
            message="Приветствуем на нашей викторине!\nДля начала нажми [Новый вопрос]",
            keyboard=keyboard.get_keyboard(),
            random_id=get_random_id(),
        )
    except Exception as err:
        logger.info("Бот VK упал с ошибкой:")
        logger.error(err)
    db_connection.set(db_user_id, "")


def handle_new_question_request(event, vk_api):
    user_id = event.user_id
    db_user_id = f"vk-{str(user_id)}"
    questions_total = int(db_connection.get("questions_total"))
    question_number = f"{random.randint(1, questions_total):03}"
    question = db_connection.hget(f"question:{question_number}", "question")
    db_connection.set(db_user_id, question_number)

    try:
        vk_api.messages.send(
            user_id=user_id,
            message=question,
            random_id=get_random_id(),
        )
    except Exception as err:
        logger.info("Бот VK упал с ошибкой:")
        logger.error(err)


def handle_solution_attempt(event, vk_api):
    message = event.text.replace("\n", " ").strip().lower()
    user_id = event.user_id
    db_user_id = f"vk-{str(user_id)}"
    question_number = db_connection.get(db_user_id)
    answer = db_connection.hget(f"question:{question_number}", "answer")
    if answer:
        answer = answer.lower()
        short_answer = answer.split(".")[0].split("(")[0].strip().lower()

    if message == short_answer or message == answer:
        try:
            db_connection.set(db_user_id, "")
            vk_api.messages.send(
                user_id=user_id,
                message="Правильно! Поздравляю!\nДля следующего вопроса нажми [Новый вопрос]",
                random_id=get_random_id(),
            )
        except Exception as err:
            logger.info("Бот VK упал с ошибкой:")
            logger.error(err)
    else:
        try:
            vk_api.messages.send(
                user_id=user_id,
                message="Неправильно… Попробуешь ещё раз?",
                random_id=get_random_id(),
            )
        except Exception as err:
            logger.info("Бот VK упал с ошибкой:")
            logger.error(err)


def handle_giveup_request(event, vk_api):
    user_id = event.user_id
    db_user_id = f"vk-{str(user_id)}"
    question_number = db_connection.get(db_user_id)
    answer = db_connection.hget(f"question:{question_number}", "answer")
    try:
        vk_api.messages.send(
            user_id=user_id,
            message=f"Правильный ответ: {answer}\nДля следующего вопроса нажми [Новый вопрос]",
            random_id=get_random_id(),
        )
    except Exception as err:
        logger.info("Бот VK упал с ошибкой:")
        logger.error(err)
    db_connection.set(db_user_id, "")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    env = Env()
    env.read_env()

    vk_token = env.str("VK_GROUP_TOKEN")
    bot_token = env("TG_BOT_TOKEN")
    admin_chat_id = env("TG_CHAT_ID")

    bot = telegram.Bot(bot_token)
    logger.addHandler(TgLogHandler(bot, admin_chat_id))
    logger.info("Бот VK запущен")

    db_connection = connect_to_db()
    if not db_connection.get("questions_total"):
        fill_db_with_questions()

    try:
        vk_session = vk_api.VkApi(token=vk_token)
        vk_api = vk_session.get_api()
        longpoll = VkLongPoll(vk_session)
    except Exception as err:
        logger.info("Бот VK упал с ошибкой:")
        logger.error(err)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == "Начать":
                start(event, vk_api)
            elif event.text == "Новый вопрос":
                handle_new_question_request(event, vk_api)
            elif event.text == "Сдаться":
                handle_giveup_request(event, vk_api)
            else:
                handle_solution_attempt(event, vk_api)
