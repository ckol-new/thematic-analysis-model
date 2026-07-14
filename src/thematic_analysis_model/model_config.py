from .config import EMBEDDING_MODEL_NAME

from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from umap import UMAP
from hdbscan import HDBSCAN
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer

embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
umap_model = UMAP()
hdbscan_model = HDBSCAN()
vectorizer_model = CountVectorizer()
ctfidf_model = ClassTfidfTransformer()

topic_model = BERTopic(
    embedding_model=embed_model,
    umap_model=umap_model,
    hdbscan_model=hdbscan_model,
    vectorizer_model=vectorizer_model,
    ctfidf_model=ctfidf_model,
    calculate_probabilities=False, # set to True for validation
)
