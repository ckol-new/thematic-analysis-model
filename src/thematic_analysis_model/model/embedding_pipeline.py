# embedding pipelines
from thematic_analysis_model.model.scraping_pipeline import ScrapingPipeline
from thematic_analysis_model.model.dclasses import *
from abc import ABC, abstractmethod
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

# initialize with model you want to embed
class EmbeddingPipeline:
    def __init__(self, data_location: Path | str | None, save_embeddings_location: Path | str | None, model, mmbedding_type: str | None):
        ...

    # run pipeline master method
    def run_pipeline():
        # load data from file

        # for post in posts, embed post (create new object)
        # this involves recursive embedding of comments, and comments of comments. Depth first.
        # to save memory, clear post data from memory

        # save embeddedings to new file.
        ...

    # embed comment, embeds all posts by calling traverse_embed_post for each post.
    def embed_data():
        # for post in posts, traverse_embed_post(post)
        ...
    
    # method for traversing nested comments
    # depth first traversal of comments attached to post
    def traverse_embed_post(post: Post):
        # queue of data structure objects to traverse (depth first search)

        # if post has comment, add comments to queue

        # for each comment, check if have comment, for each comment add to queue
        # repeat until no more comments

        # traverse queue, embed text and initialize new embedding data objects

        # return embedded post
        ...

    # embed text
    # embeds each sentence separately
    def embed_text():
        # embed each sentence add to list
        # return list
        ...

    # save embeddings
    def save_embeddings(self, embeddings, location: Path | str):
        ...

    # load embeddings class method
    @classmethod
    def load_embeddings(cls, location: Path | str):
        ...

    