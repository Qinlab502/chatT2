import json

from ...template import fuzz_sql_template, sql_template, modify_sql_template
from ...utils import get_text_completion

import re


def modify_sql(sql, error_str):
    error_prompt = f"""base on the error "{error_str}", correct the sql "{sql}" and provide the reason about how you correct briefly. Provide output in JSON format as follows: '{{"sql":"...","sql":"...","reason":"...",}}'"""
    print(error_prompt)
    modified_sql = get_text_completion(
        [{"role": "system", "content": f"完成用户请求基于该数据库:{modify_sql_template}"}, {"role": "user", "content": error_prompt}],
        temperature=0,
        response_format="json_object",
    )
    print(json.loads(modified_sql)["reason"])
    return json.loads(modified_sql)["sql"]


def extract_json_from_string(input_string):
    """
    Extract JSON substrings from a given input string.

    Args:
        input_string (str): The input string containing JSON-like substrings.

    Returns:
        list: A list of valid JSON objects extracted from the string.
    """
    # Use regex with recursive patterns to match nested curly braces
    json_matches = re.findall(r"\{(?:[^{}]*|(?R))*\}", input_string)

    # extracted_json = []
    # for match in json_matches:
    #     try:
    #         # Validate if the matched string is a valid JSON
    #         extracted_json.append(json.loads(match))
    #     except json.JSONDecodeError:
    #         pass  # Skip invalid JSON strings

    return json_matches[0]


def sql_for_database(rewrited_query):
    rewrited_query = rewrited_query.lower()  # 在数据查询中与数据库对齐统一小写
    # 这里的
    sql_message = [
        {
            "role": "system",
            "content": sql_template,
        },
        {"role": "user", "content": "my query:" + rewrited_query},
    ]
    sql = get_text_completion(sql_message, temperature=0.2, response_format="json_object")
    try:
        # print(sql)
        return json.loads(sql)["sql"]
    except json.JSONDecodeError:
        sql = extract_json_from_string(sql)
        return json.loads(sql)["sql"]


def fuzz_sql_for_database(sql):
    # 这里的sql不需要小写，避免列名不一致

    sql_message = [
        {
            "role": "system",
            "content": fuzz_sql_template,
        },
        {"role": "user", "content": sql},
    ]
    sql = get_text_completion(sql_message, temperature=0, response_format="json_object")
    return json.loads(sql)["sql"]
