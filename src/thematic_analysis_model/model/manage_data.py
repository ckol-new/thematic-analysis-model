# all classes around managing data

# methods around loading the database
class Loader:
    def __init__(self, lance_path: Path | str, tbl1_name: str, tbl2_name: str):
        ...

# methods for processing text, and splitting to sentences
class Processor:
    ...

# methods around pruning, cleaning, and diagnosing the corpus
class CorpusManager:
    ...