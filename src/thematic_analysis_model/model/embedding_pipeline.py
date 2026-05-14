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

    def embed_content(self, content: Content):
        text = content.content
        metadata = content.metadata
        if type(content) == Post: text_type = 'post'
        elif type(content) == Comment: text_type = 'comment'
        else: text_type = 'unknown'

        # split text
        sentences: list[str] = self.split_text(text)

        # emebd sentences
        embeddings = []
        count = 0
        for sentence in sentences:
            count += 1
            embedded_metadata = EmbeddedMetadata(metadata.uuid, metadata.author, metadata.url, metadata.date, metadata.origin, text_type, count)
            embedded_sentence = self.embed_sentence(sentence, embedded_metadata)
            embeddings.append(embedded_sentence)

        return embeddings


    # split text into sentence by newline character
    def split_text(self, text: str) -> list[str]:
        sentences: list = text.split('\n')
        return sentences

    # embed sentence
    def embed_sentence(self, sentence: str, metadata: EmbeddedMetadata) -> EmbeddedSentence:
        embedding: np.ndarray = self.model.encode(sentence)
        embedded_sentence = EmbeddedSentence(metadata, embedding)
        return embedded_sentence

    # save embeddings
    def save_embeddings(self, embeddings, location: Path | str):
        ...

    # load embeddings class method
    @classmethod
    def load_embeddings(cls, location: Path | str):
        ...

    