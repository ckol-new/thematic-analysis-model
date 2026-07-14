# config file for global vars, things I want to keep constant
# basically everything will import from here.
# note this is separate from TrialConfig, which is a dataclass to store the config of a given trial 
from pathlib import Path

# basic file paths and names
LANCE_PATH: Path = Path.cwd() / 'lancedatabase'
CONTENT_TBL_NAME = 'content'
LINE_TBL_NAME = 'lines'

MODEL_SAVE_PATH_BASE = Path.cwd() / 'models' / 'testing'
VALIDATION_SAVE_PATH_BASE = Path.cwd() / 'validation_metrics' / 'testing'

# Basic constants
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
EMBEDDING_DIMENSIONS = 384
NUMBER_OF_CRAWLERS = 20
NUMBER_OF_SCRAPERS = 20

# validation constants
MIN_SENTENCE_LEN = 5


# Batch Size Defaults: expeirmentally derived, alter these to test for speed.
EMBEDDING_BATCH_SIZE_DEFUALT = 4096
MODELLING_BATCH_SIZE_DEFAULT = 50000
FILE_IO_BATCH_SIZE_DEFUALT = 100000

