from pathlib import Path

import redis
from environs import Env


def parse_text(file):
    with open(file, encoding="KOI8-R") as file:
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


def fill_db_with_questions():
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

    if not db_connection.get("questions_total"):
        question_file = Path("questions/base.txt")
        qa_set = parse_text(question_file)
        question_number = 1

        for question, answer in qa_set.items():
            db_connection.hset(f"question:{question_number:03}", mapping={
                "question": question,
                "answer": answer
            })
            question_number += 1

        db_connection.set("questions_total", len(qa_set))

    return db_connection
