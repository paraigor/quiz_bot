from pathlib import Path


def main():
    question_file = Path("questions/1vs1200.txt")
    with open(question_file, encoding="KOI8-R") as file:
        file_content = file.read()

    content = file_content.split("\n\n")
    qa_set = {}

    for i in range(0, len(content)):
        if content[i].startswith("Вопрос"):
            qa_set[content[i][content[i].find("\n")+1:]] = content[i + 1][7:]

    print(qa_set)

if __name__ == "__main__":
    main()
