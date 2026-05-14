from thematic_analysis_model.model.embedding_pipeline import EmbeddingPipeline
from thematic_analysis_model.model.scraping_pipeline import ScrapingPipeline
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

        # query pair is the key, val pair of uuid and cosine similarity
        query_pair = []

        # for each embedding, get cosine similarity
        for embedding in self.embedded_db:
            similarity = self.cosine_similarity(embedded_query, embedding.embedded_text)
            query_pair.append((embedding, similarity))

        # sort query pair
        query_pair.sort(key=lambda x: x[1], reverse=True)
        # only take highest top_n similarities
        del query_pair[self.top_n:]

        # convert to dict
        return dict(query_pair)



    # embed query
    def embed_query(self, query: str) -> np.ndarray:
        return self.model.encode(query)

    # similarity calculations
    # cosine similarity for dense vectors
    def cosine_similarity(self, A: np.ndarray, B: np.ndarray):
        return A.dot(B) / (np.linalg.norm(A) * np.linalg.norm(B))

    # display query method
    @classmethod
    def get_result_objects(cls, query_pair: dict, *data_locations):
        # get set of uuid
        target = set([key.metadata.uuid for key in query_pair.keys()])

        # added post objects to list, look for uuid matches, only keep matches
        scraped_db = []
        for location in data_locations:
            scraped_db = scraped_db + ScrapingPipeline.load_scraped_output(location)
        
        # match uuids
        matches = []
        for post in scraped_db:
            if post.metadata.uuid in target: 
                matches.append(post)
                continue
            elif post.comments:
                for comment in post.comments:
                    if comment.metadata.uuid in target:
                        matches.append(comment)
                        continue

        display_results = []
        for match in matches:
            for embedded_sentence in query_pair:
                if match.metadata.uuid == embedded_sentence.metadata.uuid:
                    display_results.append((match, embedded_sentence.sentence, query_pair[embedded_sentence]))
        
        display_results.sort(key=lambda x: x[2], reverse=True)

        return display_results

            
        
