class ImagesResult:
    def __init__(
        self,
        images_reference,
    ):
        self.reference_text = images_reference

    def __str__(self) -> str:
        return self.reference_text


def retrieve_images(rewrited_query, rewrited_query_embedding):  # noqa: ARG001
    return ""


# def retrieve_images(rewrited_query, rewrited_query_embedding):
#     images_table = pd.read_excel(static_images_cache_path + "catalog.xlsx")

#     # 这里可以做一些工作做更有针对性的检索策略

#     images_list_str = ""
#     for index, (_, item) in enumerate(images_table.iterrows()):
#         if int(
#             item["local"]
#         ):  # local 变量表示是否为本地的图片文件, 由于图片的description通常情况下是关键词性描述的，不一定包含完整语义，因此这里从one token as term 的 tf-idf（词频的角度）来构造语义向量进行匹配
#             images_xml = (
#                 "<image" + str(index) + ">"
#                 "<description>" + item["description"] + "</description>"
#                 "<url>" + static_images_cache_path + item["url"] + "</url>"
#                 "<citation>" + item["citation"] + "</citation>"
#                 "</image" + str(index) + ">"
#             )
#         else:
#             images_xml = (
#                 "<image" + str(index) + ">"
#                 "<description>" + item["description"] + "</description>"
#                 "<url>" + item["url"] + "</url>"
#                 "<citation>" + item["citation"] + "</citation>"
#                 "</image" + str(index) + ">"
#             )
#         images_list_str += images_xml

#     images_information_description = (
#         "The text within the XML tags 'images_list' represents the URLs of the images possibly related to the question and those images are cited in the 'citation' field."
#         "You can choose some images to output in Markdown image format '![](url)' to help the user understand better."
#     )
#     images_reference = (
#         "<images_information_description>" + images_information_description + "</images_information_description>" "<images_list>" + images_list_str + "</images_list>"
#     )

#     return ImagesResult(images_reference)
