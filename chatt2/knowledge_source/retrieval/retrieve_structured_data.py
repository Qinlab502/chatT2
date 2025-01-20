import pandas as pd
from fuzzywuzzy import fuzz
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from ..data import structure_database_file
from ...utils import dict_to_markdown_table
from .sql import fuzz_sql_for_database, modify_sql
from sqlalchemy.exc import OperationalError
from ...utils import get_text_completion


class StrcturedDatabaseResult:
    def __init__(
        self,
        sql,
        database_path,
        recall_rate,
        view,
        max_record_num,
        view_markdown,
        column_data_description,
        structured_reference,
    ):
        self.sql = sql
        self.database_path = database_path
        self.recall_rate = recall_rate
        self.view = view
        self.record_num = min(view.shape[0], int(max_record_num * recall_rate))
        self.retrieve_information = view_markdown
        self.extra_description = column_data_description
        self.reference_text = structured_reference

    def repeat_search(self):
        engine = create_engine(self.database_path)
        Session = sessionmaker(bind=engine)  # noqa: N806

        with Session() as session:
            raw_sql_query = self.sql
            result = session.execute(text(raw_sql_query))
            columns = result.keys()
            rows_dict = [dict(zip(columns, row)) for row in result.fetchall()]
            view = pd.DataFrame(rows_dict)
        view = view.iloc[: min(view.shape[0], self.record_num)]
        return view

    def __str__(self) -> str:
        return self.reference_text


max_record_num = 100


def indel_similarity(item, query_item):
    threshold = 0.3
    """threshold 介于0-1之间，该比率表示对于item和query_item中较短的字符串需要插入或删除字符的百分比才能变成与较长字符串的最相似等长字串"""
    partial_ratio = fuzz.partial_ratio(item, query_item)
    # print(partial_ratio)
    # print(partial_ratio)
    return 2 * (1 - partial_ratio / 100) <= threshold


def fuzz_search_structured_database(database, sql, record_num):
    engine = create_engine(database)

    # 使用with语句来确保连接在使用完毕后被关闭
    with engine.connect() as connection:
        connection.connection.create_function("indel_similarity", 2, indel_similarity)
        result = connection.execute(text(sql))
        columns = result.keys()
        rows = result.fetchall()

    view = pd.DataFrame(rows, columns=columns)
    if record_num:
        view = view.iloc[: min(view.shape[0], record_num)]

    return view


def search_structured_database(database, sql, record_num=None):
    engine = create_engine(database)

    with engine.connect() as connection:
        result = connection.execute(text(sql))
        columns = result.keys()
        rows = result.fetchall()
    view = pd.DataFrame(rows, columns=columns)
    if record_num:
        view = view.iloc[: min(view.shape[0], record_num)]

    return view


def retrieve_structured_data(sql, recall_rate=0.5) -> StrcturedDatabaseResult:
    column_data_description_for_llm = {
        "mibig_number": "'MIBIG_number' serves as a reference source for information on biosynthetic gene clusters and is a unique identifier assigned to each biosynthetic gene cluster (BGC) in the MIBiG database.",
        "title": "'title' represents the title of papers introducing type-II polyketide natural product compounds and serves as a reference source for the biochemical properties of compounds.",
        "biosynthetic_path": "'biosynthetic_path' is a URL storing schematic diagrams of the synthesis pathways of type-II polyketide natural product compounds. You can output the biosynthetic_path of that row in Markdown image format '![products_name](biosynthetic_path)' to represent the synthesis pathway of a compound in a row of the view, whicn is quiet important!",
        "mibig_url": "'mibig_url' is the link introducing the biosynthetic gene cluster corresponding to the 'mibig_number'.You can output the url in html format '<a href=mibig_url>mibig_number</a>' to make the link clickable.",
        "citation": "'citation' provides references of a article in a specific format.",
        "DeepT2": "'DeepT2' column provides the result from DeepT2, which is a classification system of type 2 polyketides",
    }
    database_path = structure_database_file
    record_num = int(max_record_num * recall_rate)
    try:
        view = search_structured_database(database_path, sql, record_num)
        if view.shape[0] == 0:
            fuzz_sql = fuzz_sql_for_database(sql)
            # print(fuzz_sql)
            view = fuzz_search_structured_database(database_path, fuzz_sql, record_num)
            print("fuzz_sql finished")

    except OperationalError as e:
        sql = modify_sql(sql, str(e.orig))
        print("updated_sql:" + sql)
        view = search_structured_database(database_path, sql, record_num)
        if view.shape[0] == 0:
            fuzz_sql = fuzz_sql_for_database(sql)
            # print(fuzz_sql)
            view = fuzz_search_structured_database(database_path, fuzz_sql, record_num)
            print("fuzz_sql finished")
        # 这里暂时就更新一次

    view_text_markdown = dict_to_markdown_table(view)

    columns_text = ",".join(view.columns)
    extra_column_description_optional = ""
    for col in view.columns:
        if col in column_data_description_for_llm:
            extra_column_description_optional += column_data_description_for_llm[col] + "\n"
    column_data_description = (
        "The table is a view obtained through SQL queries from a database concerning type-II polyketide natural product compounds. "
        "It has " + str(len(view.columns)) + " columns: " + columns_text + "\n"
        "Each column name expresses the meaning of the corresponding column data. Additionally:" + extra_column_description_optional
    )

    structured_reference = (
        "<column_data_description>" + column_data_description + "</column_data_description><table>" + view_text_markdown + "</table>"
    )

    return StrcturedDatabaseResult(
        sql=sql,
        database_path=database_path,
        recall_rate=recall_rate,
        view=view,
        max_record_num=max_record_num,
        view_markdown=view_text_markdown,
        column_data_description=column_data_description,
        structured_reference=structured_reference,
    )


# def retrieve_structured_data_old(sql, GS_value=0.5):
#     def replace_newline(cell):
#         if isinstance(cell, str):
#             return cell.replace("\n", "\n")
#         return cell

#     column_data_description_for_llm = {
#         "mibig_number": "'MIBIG_number' serves as a reference source for information on biosynthetic gene clusters and is a unique identifier assigned to each biosynthetic gene cluster (BGC) in the MIBiG database.",
#         "title": "'title' represents the title of papers introducing type-II polyketide natural product compounds and serves as a reference source for the biochemical properties of compounds.",
#         "biosynthetic_path": "'biosynthetic_path' is a URL storing schematic diagrams of the synthesis pathways of type-II polyketide natural product compounds. You can output the biosynthetic_path of that row in Markdown image format '![products_name](biosynthetic_path)' to represent the synthesis pathway of a compound in a row of the view, whicn is quiet important!",
#         "mibig_url": "'mibig_url' is the link introducing the biosynthetic gene cluster corresponding to the 'mibig_number'.You can output the url in html format '<a href=mibig_url>mibig_number</a>' to make the link clickable.",
#         "citation": "'citation' provides references of a article in a specific format.",
#     }

#     view = search_structured_database("sqlite:///data/chat_t2_database.db", sql)
#     view_text_markdown = dict_to_markdown_table(view)

#     Canonical_SMILE_list = {}
#     if "Canonical_SMILE" in view.columns:
#         canonicalsmiles_table = pd.read_excel("data/structured_data/canonicalsmiles_table.xlsx")
#         canonicalsmiles_table.set_index("products_name", inplace=True)
#         canonicalsmiles_dict = canonicalsmiles_table["Canonical_SMILE"].to_dict()
#         for value in view["Canonical_SMILE"].values():
#             for name in value.split("\n"):
#                 Canonical_SMILE_list[name] = canonicalsmiles_dict[name.split("_can")[0]]
#         view = view.drop(columns=["Canonical_SMILE"])

#     view = view.applymap(replace_newline)
#     view = view.iloc[: min(view.shape[0], int(20 + 100 * GS_value))]

#     columns_text = ",".join(view.columns)
#     extra_column_description_optional = ""
#     for col in view.columns:
#         if col in column_data_description_for_llm:
#             extra_column_description_optional += column_data_description_for_llm[col] + "\n"
#     column_data_description = (
#         "The table is a view obtained through SQL queries from a database concerning type-II polyketide natural product compounds. "
#         "It has " + str(len(view.columns)) + " columns: " + columns_text + "\n"
#         "Each column name expresses the meaning of the corresponding column data. Additionally:" + extra_column_description_optional
#     )

#     structured_reference = "<column_data_description>" + column_data_description + "</column_data_description>" "<table>" + view_text_markdown + "</table>"

#     return structured_reference, Canonical_SMILE_list
