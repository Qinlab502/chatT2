import numpy as np

# 这里可以结合马尔可夫过程，和LLM如何通过结合历史记录的查询重写查询，将当前查询转化为只与上一个查询相关，然后计算两个查询相似度调整召回率
# 或者从聚类建模的角度，将通过计算当前问题与历史问题簇的相关性


def recall_rate_adapter(past_query_embedding, rewrited_query_embedding, recall_rate):
    cos_similarity = np.dot(np.array(past_query_embedding), np.array(rewrited_query_embedding))  # two embeddings are standardized
    if cos_similarity > 0.8:
        recall_rate = recall_rate + (1 - recall_rate) * cos_similarity
    return recall_rate
