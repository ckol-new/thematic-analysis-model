from pathlib import Path
import pyarrow as pa
base = Path.cwd()

LDB_PATH = base / 'lance_db'
SCRAPE_DATA_TABLE_NAME = 'scrape_data'


# BATCH SIZES
SCRAPING_BATCH_SIZE = 10000



# sentence db schema
EMBEDDING_DIMENSIONS = 384
schema = pa.schema([
    pa.field('uuid', pa.string()),
    pa.field('sentence', pa.string()),
    pa.field('vector', pa.list_(pa.float32(), EMBEDDING_DIMENSIONS), nullable=True),
    pa.field('url', pa.string()),
    pa.field('content_uuid', pa.string()),
    pa.field('is_modelled', pa.bool_()),
    pa.field('origin', pa.string()),
    pa.field('content_type', pa.string())
])