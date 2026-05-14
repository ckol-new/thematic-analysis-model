# embedding pipelines
from thematic_analysis_model.model.scraping_pipeline import ScrapingPipeline
from thematic_analysis_model.model.dclasses import *
from abc import ABC, abstractmethod
from pathlib import Path
from sentence_transformers import SentenceTransformer, util

# initialize with model you want to embed
class EmbeddingPipeline:
    def __init__(self, data_location: Path | str | None, save_embeddings_location: Path | str | None, model: SentenceTransformer, embedding_type: str | None):
        self.data_location = data_location
        self.save_embeddings_location = save_embeddings_location
        self.model = model
        self.embedding_type = embedding_type

    # run pipeline master method
    def run_pipeline():
        # load data from file

        # for post in posts, embed post (create new object)
        # this involves recursive embedding of comments, and comments of comments. Depth first.
        # to save memory, clear post data from memory

        # save embeddedings to new file.
        ...

    

    # embed sentence
    def embed_sentence(self, sentence: str):
        embedding = self.model.encode(sentence)
        return embedding

    # save embeddings
    def save_embeddings(self, embeddings, location: Path | str):
        ...

    # load embeddings class method
    @classmethod
    def load_embeddings(cls, location: Path | str):
        ...

    