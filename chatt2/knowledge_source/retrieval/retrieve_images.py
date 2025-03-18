import os
import pickle
import numpy as np

import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url

from nltk.tokenize import word_tokenize
from rank_bm25 import BM25Plus
import json
from ..images_database import static_images_cache_path

# Configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_NAME"),
    api_key=os.getenv("CLOUDINARY_KEY"),
    api_secret=os.getenv("CLOUDINARY_SECRET"),
    secure=True,
)


def retrieve_images(query):
    def search_image(search_value):
        try:
            search_results = cloudinary.api.resources_by_context(
                key="description", value=f"{search_value}"
            )["resources"][0]["url"]
        except Exception as e:
            search_results = "No image found"
        return search_results

    figure_description_path = static_images_cache_path + "figure_description.json"
    with open(figure_description_path, "r") as f:
        figure_description = json.load(f)

    bm25_model_path = static_images_cache_path + "bm25_model.pkl"
    with open(bm25_model_path, "rb") as f:
        bm25 = pickle.load(f)

    tokenized_query = word_tokenize(query)
    scores = bm25.get_scores(tokenized_query)
    # k = int(os.getenv("N_FIGURES"))
    k = 5
    top_k_indices = np.argsort(scores)[::-1][:k]
    retrieval_figure = {}
    for i in top_k_indices:
        retrieval_figure[figure_description[i]] = search_image(figure_description[i])
    return retrieval_figure
