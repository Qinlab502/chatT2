import os

import numpy as np
import pandas as pd

from ..data import articles_table_file, vector_database_path
from ...utils import read_json
from .retrieve_structured_data import StrcturedDatabaseResult


class VectorDatabaseResult:
    def __init__(
        self,
        rewrited_query_embedding,
        vector_database_path,
        recall_rate,
        chunk_view,
        record_num,
        chunk_xml,
        text_description,
        unstructured_reference,
    ):
        self.rewrited_query_embedding = rewrited_query_embedding
        self.database_path = vector_database_path
        self.recall_rate = recall_rate
        self.chunk_view = chunk_view
        self.record_num = record_num
        self.retrieve_information = chunk_xml
        self.extra_description = text_description
        self.reference_text = unstructured_reference

    def repeat_search(self):
        pass

    def __str__(self) -> str:
        return self.reference_text


def filter_paper_metadata(strctured_data_view):
    try:
        filter_paper_index = strctured_data_view["colluid"].tolist()
    except KeyError:
        filter_paper_index = []
    return filter_paper_index


def filter_paper_abstract(rewrited_query_embedding, vector_database_path):
    abstract_vector = pd.DataFrame(read_json(vector_database_path + "abstract_vector.json"))
    abstract_vector["cosine_similarity"] = np.dot(np.array(abstract_vector["vector"].array.tolist()), rewrited_query_embedding)
    top_n_abstract = abstract_vector.nlargest(30, "cosine_similarity")  # 在问答场景下30篇文章足够，在研发场景下不一定

    return (
        top_n_abstract["colluid"].tolist(),
        top_n_abstract,
    )  # 20是一个自定义的大小，返回多少篇文章


def chunk_with_description(top_n_chunk_df_for_articles: pd.DataFrame):
    chunk_list_str = ""
    for index, (_, item) in enumerate(top_n_chunk_df_for_articles.iterrows()):
        chunk_xml = (
            "<chunk"
            + str(index)
            + "><text>"
            + item["text"]
            + "</text><citation>"
            + "["
            + item["citation"]
            + "]"
            + "("
            + "https://doi.org/"
            + item["doi"]
            + ")"
            + "</citation></chunk"
            + str(index)
            + ">"
        )
        chunk_list_str += chunk_xml

    text_information_description = (
        "The text within the XML tags 'chunk_list' contains text snippets from the relevant papers regarding the question."
        "Each 'chunk' within 'chunk_list' contains two parts: 'text' and 'citation'."
    )
    unstructured_reference = (
        "<text_information_description>"
        + text_information_description
        + "</text_information_description><chunk_list>"
        + chunk_list_str
        + "</chunk_list>"
    )

    return unstructured_reference, text_information_description, chunk_list_str


def retrieve_vector_data(rewrited_query_embedding, strctured_data: StrcturedDatabaseResult, recall_rate):
    rewrited_query_embedding = np.array(rewrited_query_embedding)

    # 处理strctured_data的检索文献索引
    Is_index = filter_paper_metadata(strctured_data.view)  # noqa: N806
    # 处理rewrited_query_embedding确实的检索文献索引
    Iv_index, top_n_abstract = filter_paper_abstract(rewrited_query_embedding, vector_database_path)  # noqa: N806
    # print(Is_index, Iv_index)

    total_index = list(
        set(Is_index)
        | set(Iv_index)
        | {
            "WOS:TII1",
            "WOS:TII2",
            "WOS:TII3",
            "WOS:TII4",
        }
    )  # 最后几个集合是必选的集合
    # print(Is_index, Iv_index)
    # print(total_index)
    vector_storage_path = vector_database_path
    articles_table_path = articles_table_file

    chunk_df_for_articles = []
    json_list = os.listdir(vector_storage_path)
    # print(json_list[:10], "_____________")
    articles_table = pd.read_excel(articles_table_path, index_col=0)
    # print(json_list)
    # raise ValueError("aa")
    for _index in total_index:
        index = _index.replace(":", "_")
        # print(index + ".json")
        if index + ".json" in json_list:  # 有摘要的文章不一定有对应的向量数据库存储
            chunk_df_for_article = pd.DataFrame(read_json(vector_storage_path + index + ".json"))
            try:
                chunk_df_for_article["citation"] = articles_table[articles_table["colluid"] == _index]["titles"].to_numpy()[0]
                chunk_df_for_article["doi"] = articles_table[articles_table["colluid"] == _index]["doi"].to_numpy()[0]
            except IndexError:
                print(_index)
            chunk_df_for_articles.append(chunk_df_for_article)

    chunk_df_for_articles = pd.concat(chunk_df_for_articles, axis=0)
    chunk_df_for_articles["chunk_similarity"] = np.dot(
        np.array(chunk_df_for_articles["vector"].to_numpy().tolist()),
        rewrited_query_embedding,
    )

    chunk_df_for_articles = chunk_df_for_articles[chunk_df_for_articles["chunk_similarity"] > 0.5]  # 仅考虑高相似度的chunk

    # 这里有很多个阈值
    # chunk都小于0.4的说明都是不相关文本，用原LLM
    # 可以预先提供LLM的答案，只有chunk都小于0.4的情况下才提供，减少串行执行时的时间花费
    # 对大于0.4的chunk，一般问答场景下所需要的上下文来源于少量的chunk，50个就够了，对于研究的场景下，可能不够
    # 因此返回的chunk应该就是int(50 + 100 * recall_rate)

    chunk_df_for_articles = chunk_df_for_articles.sort_values(by="chunk_similarity", ascending=False)
    chunk_df_for_articles = chunk_df_for_articles.reset_index(drop=True)
    # stochastic_citation = chunk_df_for_articles.iloc[: min(chunk_df_for_articles.shape[0], 5)]["citation"]
    # yield stochastic_citation?

    top_n_chunk_in_articles = int(50 + 80 * recall_rate)  # 按照最大最小规范化的思路

    top_n_chunk_df_for_articles = chunk_df_for_articles.iloc[: min(chunk_df_for_articles.shape[0], int(top_n_chunk_in_articles))]
    top_n_chunk_df_for_articles.to_excel("del-2.xlsx")
    # print(top_n_chunk_df_for_articles["chunk_similarity"])
    # print(top_n_chunk_df_for_articles["text"].iloc[:3].values)
    unstructured_reference, text_description, chunk_xml = chunk_with_description(top_n_chunk_df_for_articles)

    return VectorDatabaseResult(
        rewrited_query_embedding,
        vector_database_path,
        recall_rate,
        chunk_df_for_articles,
        min(chunk_df_for_articles.shape[0], int(top_n_chunk_in_articles)),
        chunk_xml,
        text_description,
        unstructured_reference,
    )


# def retrieve_vector_data_old(rewrited_query_embedding, strctured_data, recall_rate):
#     def json_to_df(json_file):
#         with open(json_file, "r") as f:
#             json_data = json.load(f)
#             df = pd.DataFrame(json_data)
#             return df

#     unstructured_data_path = "data/vector_database/"
#     articles_table = pd.read_excel(unstructured_data_path + "articles_table_3.0.xlsx")

#     chunk_df_for_articles = []
#     vector_file = unstructured_data_path + "vector storage_512_json/"
#     file_list = os.listdir(vector_file)
#     for article_index in filter_paper_index:
#         if str(article_index) + ".json" not in file_list:
#             continue
#         # print(article_index)
#         chunk_df_for_article = json_to_df(vector_file + str(article_index) + ".json")
#         # print(chunk_df_for_article)
#         chunk_df_for_article["citation"] = articles_table[
#             articles_table["article_index"] == article_index
#         ]["citation"].values[0]

#         chunk_df_for_articles.append(chunk_df_for_article)

#     rewrited_query_embedding = np.array(rewrited_query_embedding)
#     chunk_df_for_articles = pd.concat(chunk_df_for_articles, axis=0)

#     chunk_df_for_articles["chunk_similarity"] = np.dot(
#         np.array(chunk_df_for_articles["vector"].values.tolist()),
#         rewrited_query_embedding,
#     )
#     chunk_df_for_articles = chunk_df_for_articles.sort_values(
#         by="chunk_similarity", ascending=False
#     )
#     chunk_df_for_articles = chunk_df_for_articles.reset_index(drop=True)

#     top_n_chunk_in_articles = int(
#         200 * GS_value
#     )  # 按照最大最小规范化的思路，不过这个chunk的定义最好是测试出来的，或者根据LLM最大token数量

#     # 以下是generator中的工作，不过在测试先不做reranker的工作了

#     return chunk_df_for_articles.iloc[
#         : min(chunk_df_for_articles.shape[0], int(top_n_chunk_in_articles))
#     ]
