import os

import numpy as np
import pandas as pd


from ...utils import read_json
from .retrieve_structured_data import StrcturedDatabaseResult
from ...utils import get_embeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, Match, PointsSelector
from pathlib import Path


class VectorDatabaseResult:
    def __init__(
        self,
        rewrited_query_embedding,
        chunk_df_for_articles,
        chunk_xml,
        text_description,
        unstructured_reference,
    ):
        self.rewrited_query_embedding = rewrited_query_embedding
        self.chunk_df_for_articles = chunk_df_for_articles
        self.retrieve_information = chunk_xml
        self.extra_description = text_description
        self.reference_text = unstructured_reference

    def __str__(self) -> str:
        return self.reference_text


def filter_paper_metadata(strctured_data_view):
    try:
        filter_paper_index = strctured_data_view["colluid"].tolist()
    except KeyError:
        filter_paper_index = []
    return filter_paper_index


def search_qdrant(
    collection_name, query=None, query_vector=None, filter_condition=None, limit=5
):
    search_params = {}
    if query is not None:
        query_vector = get_embeddings([query])[0]

    if query_vector is not None:
        search_params["query_vector"] = query_vector

    if collection_name is not None:
        search_params["collection_name"] = collection_name

    if filter_condition is not None:
        search_params["query_filter"] = filter_condition

    if limit is not None:
        search_params["limit"] = limit

    search_params["timeout"] = 120

    qdrant_client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )
    search_results = qdrant_client.search(**search_params)
    # 返回ScoredPoint的迭代器，可以通过以下代码获得id, score, payload等数据
    # for result in search_results:
    #     print(f"ID: {result.id}, Distance: {result.score}, Payload: {result.payload}")
    return search_results


# def search_qdrant_main_text(
#     query_vector, top_n=int(20 + 100 * float(os.getenv("RECALL_RATE")))
# ):
#     all_results = search_qdrant(
#         collection_name="main_text", query_vector=query_vector, limit=top_n
#     )
#     chunk_df_for_articles = pd.DataFrame(columns=["colluid", "text", "score"])
#     for result in all_results:
#         # print(result.score, float(os.getenv("MIN_SCORE_THRESHOLD")))
#         if result.score >= float(os.getenv("MIN_SCORE_THRESHOLD")):
#             chunk_df_for_articles.loc[chunk_df_for_articles.shape[0]] = {
#                 "colluid": result.payload["colluid"],
#                 "text": result.payload["text"],
#                 "score": result.score,
#             }

#     root = Path(__file__) / ".."
#     cwd = Path.cwd()
#     table = pd.read_excel(
#         (root / "article_paper_sum.xlsx").resolve().relative_to(cwd).as_posix()
#     )[["colluid", "title", "doi"]]

#     chunk_df_for_articles["colluid"] = chunk_df_for_articles["colluid"].str.replace(
#         "_", ":"
#     )

#     merge_table = pd.merge(chunk_df_for_articles, table, on="colluid", how="inner")
#     return merge_table


def search_qdrant_main_text(
    colluid_list,
    query_vector,
    batch_size=40,
    top_n=int(20 + 100 * float(os.getenv("RECALL_RATE"))),
):
    all_results = []
    # print(colluid_list)
    for i in range(0, len(colluid_list), batch_size):
        batch = colluid_list[i : i + batch_size]
        filter_condition = Filter(
            should=[
                {"key": "colluid", "match": {"value": colluid}} for colluid in batch
            ]
        )
        search_results = search_qdrant(
            "main_text",
            filter_condition=filter_condition,
            query_vector=query_vector,
            limit=top_n,
        )
        all_results.extend(search_results)
    # print(all_results)
    chunk_df_for_articles = pd.DataFrame(columns=["colluid", "text", "score"])
    for result in all_results:
        if result.score >= float(os.getenv("MIN_SCORE_THRESHOLD")):
            chunk_df_for_articles.loc[chunk_df_for_articles.shape[0]] = {
                "colluid": result.payload["colluid"],
                "text": result.payload["text"],
                "score": result.score,
            }
    return chunk_df_for_articles


def search_qdrant_abstract(query_vector, top_n=int(os.getenv("TOP_N_DOCUMENT"))):
    # payload = {"colluid": 1, "title": 2, "abstract": 3, "citation": 4, "doi": 5}
    search_results = search_qdrant("abstract", query_vector=query_vector, limit=top_n)
    articles_df = pd.DataFrame(
        columns=["colluid", "title", "abstract", "citation", "doi"]
    )
    for result in search_results:
        if result.score >= float(os.getenv("MIN_SCORE_THRESHOLD")):
            articles_df.loc[articles_df.shape[0]] = {
                "colluid": result.payload["colluid"].replace(":", "_"),
                "title": result.payload["title"],
                "abstract": result.payload["abstract"],
                "pubyear": result.payload["pubyear"],
                "doi": result.payload["doi"],
                "authors": result.payload["authors"],
            }
    return articles_df


def filter_paper_abstract(query_embedding):
    articles_df = search_qdrant_abstract(query_vector=query_embedding)
    return (articles_df["colluid"].to_numpy(), articles_df)


def chunk_with_description(chunk_df_for_articles: pd.DataFrame):
    chunk_list_str = ""
    for index, (_, item) in enumerate(chunk_df_for_articles.iterrows()):
        chunk_xml = f"<chunk id={index}>\
<text>{item['text']}</text>\
<citation>\
<title>{item['title']}</title>\
<doi>{'https://doi.org/' + item['doi']}</doi>\
</citation>\
</chunk>"
        chunk_list_str += chunk_xml

    text_information_description = (
        "The text within the XML tags 'chunk_list' contains text snippets from the relevant papers regarding the question."
        "Each 'chunk' in 'chunk_list' contains two parts: 'text' and 'citation'."
    )
    unstructured_reference = (
        "<text_information_description>"
        + text_information_description
        + "</text_information_description>"
        "<chunk_list>" + chunk_list_str + "</chunk_list>"
    )

    return unstructured_reference, text_information_description, chunk_list_str


def retrieve_vector_data(
    query_embedding, structured_data: StrcturedDatabaseResult = None
):
    query_embedding = np.array(query_embedding)

    # 处理strctured_data的检索文献索引
    if structured_data is not None:
        Is_index = filter_paper_metadata(structured_data.view)
    else:
        Is_index = []
    # 处理rewrited_query_embedding确实的检索文献索引
    Iv_index, articles_df = filter_paper_abstract(query_embedding)
    # print(Is_index)
    # print(Iv_index)

    total_index = [
        index.replace(":", "_") for index in list(set(Is_index) | set(Iv_index))
    ]

    # print(total_index)

    chunk_df_for_articles = search_qdrant_main_text(
        colluid_list=total_index, query_vector=query_embedding
    )
    # print(chunk_df_for_articles)
    chunk_df_for_articles = chunk_df_for_articles.sort_values(
        by="score", ascending=False
    ).head(int(20 + 100 * float(os.getenv("RECALL_RATE"))))

    # chunk_df_for_articles.to_excel("chunk_df_for_articles.xlsx")
    # articles_df.to_excel("articles_df.xlsx")

    merge_table = pd.merge(chunk_df_for_articles, articles_df, on="colluid", how="left")

    # print(bool(os.getenv("CACHE")))
    if bool(os.getenv("CACHE")):
        merge_table.to_excel(os.getenv("cache_dir") + "/merge_table.xlsx")
        # with open(os.getenv("cache_dir") + "/del.xml", "w") as f:  # noqa: PTH123
        #     f.write(chunk_xml)

    unstructured_reference, text_description, chunk_xml = chunk_with_description(
        merge_table
    )

    return VectorDatabaseResult(
        query_embedding,
        chunk_df_for_articles,
        chunk_xml,
        text_description,
        unstructured_reference,
    )
