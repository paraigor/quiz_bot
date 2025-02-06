from pathlib import Path

import redis
from environs import Env


def get_qa_set():
    question_file = Path("questions/base.txt")
    with open(question_file, encoding="KOI8-R") as file:
        content = file.read().splitlines()

    content_length = len(content)
    index = 0
    question = ""
    answer = ""
    qa_set = dict()

    while index < content_length:
        if content[index].startswith("Вопрос"):
            index += 1
            while content[index]:
                question += content[index] + " "
                index += 1

        if content[index].startswith("Ответ"):
            index += 1
            while content[index]:
                answer += content[index] + " "
                index += 1

        if question and answer:
            qa_set[question.strip()] = answer.strip()
            question = ""
            answer = ""

        index += 1

    return qa_set


def connect_to_db():
    env = Env()
    env.read_env()

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

    return db_connection


def fill_db_with_questions():
    db = connect_to_db()

    qa_set = get_qa_set()
    question_number = 1

    for question, answer in qa_set.items():
        db.hset(f"question:{question_number:03}", mapping={
            "question": question,
            "answer": answer
        })
        question_number += 1

    db.set("questions_total", len(qa_set))
