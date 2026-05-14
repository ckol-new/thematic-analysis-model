from thematic_analysis_model.model.embedding_pipeline import EmbeddingPipeline
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np



# if initilaized with all paramaters, you can run pipeline to perform query or queue of queries.
# otherwise, manual
class QueryEngine:
    def __init__(self, model: SentenceTransformer | None, *data_locations: tuple[Path | str] | None, top_n: int = 10):
        self.model = model
        self.data_locations = data_locations
        self.top_n = top_n

        # load embedded database
        embedded_db = []
        for location in data_locations:
            embeddings = EmbeddingPipeline.load_embeddings(location)
            embedded_db = embedded_db + embeddings
            
        self.embedded_db = embedded_db


    # query each embedded sentence
    def run_query(self, query: str):
        if not query:
            return None

        embedded_query = self.embed_query(query)



    # embed query
    def embed_query(self, query: str) -> np.ndarray:
        return self.model.encode(query)

    # similarity calculations
    # cosine similarity for dense vectors
    def cosine_similarity(self, A: np.ndarray, B: np.ndarray):
        return A.dot(B) / (np.linalg.norm(A) * np.linalg.norm(B))