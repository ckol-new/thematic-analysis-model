# config file for global vars
from pathlib import Path

# Paths
DATABASE_PATH = Path.cwd() / 'db'

# Global Vars
CONTENT_TBL_NAME = "content"
SENTENCE_TBL_NAME = "sentence"
MODEL_OUTPUT_TBL_NAME = "model_output"

EMBEDDING_DIMENSIONS = 384

NUM_CRAWLERS = 20
NUM_SCRAPERS = 20
SAVER_BATCH_SIZE = 2500

# Batch Sizes
FILE_IO_BATCH_SIZE = 100000

