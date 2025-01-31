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
