# config file for global vars
from pathlib import Path

# Paths
DATABASE_PATH = Path.cwd() / 'db'

# Global Vars
CONTENT_TBL_NAME = "content"
SENTENCE_TBL_NAME = "sentence"
MODEL_OUTPUT_TBL_NAME = "model_output"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384

NUM_CRAWLERS = 20
NUM_SCRAPERS = 20
SAVER_BATCH_SIZE = 2500

# Processing Sentences
MIN_SENTENCE_LENGTH = 3
MAX_SENTENCE_LENGTH = 200

# Batch Sizes
FILE_IO_BATCH_SIZE = 100000
EMBED_BATCH_SIZE = 4096

