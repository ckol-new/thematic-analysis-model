# config file for global vars, things I want to keep constant
# basically everything will import from here.
# note this is separate from TrialConfig, which is a dataclass to store the config of a given trial 

# Basic constants
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'


# Batch Size Defaults: expeirmentally derived, alter these to test for speed.
EMBEDDING_BATCH_SIZE_DEFUALT = 4096
MODELLING_BATCH_SIZE_DEFAULT = 50000
FILE_IO_BATCH_SIZE_DEFUALT = 100000
