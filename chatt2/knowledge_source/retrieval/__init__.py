from .function_repository import FunctionMaster
from .retrieve_images import retrieve_images
from .retrieve_structured_data import (
    fuzz_search_structured_database,
    retrieve_structured_data,
)
from .retrieve_vector_database import retrieve_vector_data
from .sql import fuzz_sql_for_database, sql_for_database
import copy

from ...utils import (
    get_embedding,
    get_text_completion,
    get_text_completion_with_stream,
    streamable,
)
import os


def retrieval_for_context(question, recall_rate=float(os.getenv("RECALL_RATE"))):
    information_types = ["table", "text", "image", "tool"]

    query_embedding = get_embedding(question)

    context = ""
    structured_data = None
    for information_type in information_types:
        if os.getenv(information_type.upper()) == "true":
            if information_type == "table":
                sql = sql_for_database(question)
                data = retrieve_structured_data(sql, recall_rate)
                structured_data = copy.deepcopy(data)
                # print("table:", structured_data is None)
            elif information_type == "text":
                # print("text:", structured_data is None)
                data = retrieve_vector_data(query_embedding, structured_data)

            elif information_type == "image":
                data = retrieve_images(question)
            elif information_type == "tool":
                data = FunctionMaster(query=question).loop()
            context += (
                f"<{information_type}_information>"
                + str(data)
                + f"</{information_type}_information>"
            )

    context = "<knowledge>" + context + "</knowledge>"

    if os.getenv("cache") == "true":
        with open(os.getenv("cache_dir") + "/del.xml", "w") as f:  # noqa: PTH123
            f.write(context)
    return context
