from pathlib import Path
import pyarrow as pa
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
import umap
import hdbscan

base = Path.cwd()

LDB_PATH = base / 'lance_db'
SCRAPE_DATA_TABLE_NAME = 'scrape_data'


# BATCH SIZES
SCRAPING_BATCH_SIZE = 10000



# sentence db schema
EMBEDDING_DIMENSIONS = 384
SENTENCE_SCHEMA = pa.schema([
    pa.field('uuid', pa.string()),
    pa.field('sentence', pa.string()),
    pa.field('vector', pa.list_(pa.float32(), EMBEDDING_DIMENSIONS), nullable=True),
    pa.field('url', pa.string()),
    pa.field('content_uuid', pa.string()),
    pa.field('is_modelled', pa.bool_()),
    pa.field('origin', pa.string()),
    pa.field('content_type', pa.string())
])

# SCHEMA
SENTENCE_SCHEMA2 = pa.schema([
    pa.field('uuid', pa.string()),
    pa.field('sentence', pa.string()),
    pa.field('vector', pa.list_(pa.float32(), EMBEDDING_DIMENSIONS, nullable=True)),
    pa.field('url', pa.string()),

])



# models
S_MODEL_NAME = 'all-MiniLM-L6-v2'

embedding_model = SentenceTransformer(S_MODEL_NAME)
umap_model = umap.UMAP(n_neighbors=15, n_components=5, min_dist=0.0, verbose=True)
hdbscan_model = hdbscan.HDBSCAN(min_cluster_size=100, )
vectorizer_model = CountVectorizer(stop_words='english')
