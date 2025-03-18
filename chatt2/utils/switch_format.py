import json


def dict_to_markdown_table(view):
    data = [dict(zip(view.columns, row)) for row in view.to_numpy()]
    # 确认所有的键都在每个字典中
    keys = set()
    for item in data:
        keys.update(item.keys())
    keys = list(keys)

    header = "| " + " | ".join(keys) + " |"
    separator = "|---" * len(keys) + "|"

    rows = []
    for item in data:
        row = "| " + " | ".join(str(item.get(key, "")) for key in keys) + " |"
        rows.append(row)

    return "\n".join([header, separator, *rows])


def object_to_str(ob):
    return json.dumps(ob)


def str_to_object(string: str):
    return json.loads(string)
