# all classes around managing data
from pathlib import Path
import lancedb
from .dclasses import Line, Content

# methods around loading the database
class Loader:
    def __init__(self, lance_path: Path | str, tbl1_name: str, tbl2_name: str):
        self.lance_path = lance_path
        self.tbl1_name = tbl1_name
        self.tbl2_name = tbl2_name
    
    def first_init(self, schema1: type, schema2: type):
        db = lancedb.connect(self.lance_path)
        tbl1 = db.create_table(name=self.tbl1_name, schema=schema1)
        tbl2 = db.create_table(name=self.tbl2_name, schema=schema2)
    
    def connect(self):
        db = lancedb.connect(self.lance_path)
        tbl1 = db.open_table(name=self.tbl1_name)
        tbl2 = db.open_table(name=self.tbl2_name)
        return db, tbl1, tbl2

# methods for processing text, and splitting to sentences
class Processor:
    ...

# methods around pruning, cleaning, and diagnosing the corpus
class CorpusManager:
    ...