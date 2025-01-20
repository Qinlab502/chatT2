from .function_repository import FunctionMaster
from .recall_rate_adapter import recall_rate_adapter
from .retrieve_images import retrieve_images
from .retrieve_structured_data import (
    fuzz_search_structured_database,
    retrieve_structured_data,
)
from .retrieve_vector_database import retrieve_vector_data
from .sql import fuzz_sql_for_database, sql_for_database

from ...utils import (
    get_embedding,
    get_text_completion,
    get_text_completion_with_stream,
    streamable,
)


def retrieval_for_context(question, recall_rate=0.5):
    rewrited_query = question
    rewrited_query_embedding = get_embedding(rewrited_query)
    sql = sql_for_database(rewrited_query)

    strctured_data = retrieve_structured_data(sql, recall_rate)
    vector_data = retrieve_vector_data(rewrited_query_embedding, strctured_data, recall_rate)  # 在结点内直接做完reranker和上下文补充
    images_data = retrieve_images(rewrited_query, rewrited_query_embedding)
    tool_data = FunctionMaster(query=question).loop()

    # raise ValueError("aa")
    context = (
        "<knowledge>"
        "<table_information>" + str(strctured_data) + "</table_information>"
        "<text_information>" + str(vector_data) + "</text_information>"
        "<images_information>" + str(images_data) + "</images_information>"
        "<tool_output_information>" + str(tool_data) + "</tool_output_information>"
        "</knowledge>"
    )
    return context
