import random
from pathlib import Path

import redis
import vk_api
from environs import Env
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll
from vk_api.utils import get_random_id

from tools import parse_text


def start(event, vk_api):
    user_id = event.user_id
    keyboard = VkKeyboard()
    keyboard.add_button("Новый вопрос", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("Сдаться", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("Мой счёт", color=VkKeyboardColor.SECONDARY)

    vk_api.messages.send(
        user_id=user_id,
        message="Приветствуем на нашей викторине! Для начала нажми [Новый вопрос]",
        keyboard=keyboard.get_keyboard(),
        random_id=get_random_id(),
    )
    db_connection.set(user_id, "")


def handle_new_question_request(event, vk_api):
    user_id = event.user_id
    question = random.choice(list(qa_set.keys()))
    db_connection.set(user_id, question)
    vk_api.messages.send(
        user_id=user_id,
        message=question,
        random_id=get_random_id(),
    )


def handle_solution_attempt(event, vk_api):
    text = event.text.replace("\n", " ").strip().lower()
    user_id = event.user_id
    question = db_connection.get(user_id)

    answer = qa_set.get(question)
    if answer:
        answer = answer.lower()
        short_answer = answer.split(".")[0].split("(")[0].strip().lower()

    if text == short_answer or text == answer:
        vk_api.messages.send(
            user_id=user_id,
            message="Правильно! Поздравляю! Для следующего вопроса нажми [Новый вопрос]",
            random_id=get_random_id(),
        )
        db_connection.set(user_id, "")
    else:
        vk_api.messages.send(
            user_id=user_id,
            message="Неправильно… Попробуешь ещё раз?",
            random_id=get_random_id(),
        )


def handle_giveup_request(event, vk_api):
    user_id = event.user_id
    question = db_connection.get(user_id)
    answer = qa_set.get(question)
    vk_api.messages.send(
        user_id=user_id,
        message=f"Правильный ответ: {answer}\nДля следующего вопроса нажми [Новый вопрос]",
        random_id=get_random_id(),
    )
    db_connection.set(user_id, "")


if __name__ == "__main__":
    env = Env()
    env.read_env()
    vk_token = env.str("VK_GROUP_TOKEN")
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

    vk_session = vk_api.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

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
