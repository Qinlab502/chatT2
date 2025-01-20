import json

# def write_json(data, file_path):
#     with open(file_path, "w") as f:
#         json.dump(data, f, indent=4)


def write_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:  # noqa: PTH123
        json.dump(data, f, indent=4, ensure_ascii=False)  # 这个ensure_ascii表示是否要将字符串中的非ascii字符转码为unicode字符，为false时候就保留为原来字符


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
