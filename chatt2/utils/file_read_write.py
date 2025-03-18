import json


def write_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:  # noqa: PTH123
        json.dump(data, f, indent=4, ensure_ascii=False)


def read_json(file_path):
    with open(file_path) as f:  # noqa: PTH123
        data = json.load(f)
    return data


def write_text(text, file_path):
    with open(file_path, "w") as f:  # noqa: PTH123
        f.write(text)


def read_text(file_path):
    with open(file_path) as f:  # noqa: PTH123
        content = f.read()
    return content
