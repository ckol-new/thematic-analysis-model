# all classes around managing data
from pathlib import Path
import lancedb
from .dclasses import Line, Content
from datetime import timedelta
import codecs

# methods around loading the database
class Loader:
    def __init__(self, lance_path: Path | str, tbl1_name: str, tbl2_name: str):
        self.lance_path = lance_path
        self.tbl1_name = tbl1_name
        self.tbl2_name = tbl2_name
    
    # creates table with schema 
    def first_init(self, schema1: type, schema2: type):
        db = lancedb.connect(self.lance_path)
        tbl1 = db.create_table(name=self.tbl1_name, schema=schema1, mode='overwrite')
        tbl2 = db.create_table(name=self.tbl2_name, schema=schema2, mode='overwrite')
    
    # opens table
    def connect(self):
        db = lancedb.connect(self.lance_path)
        tbl1 = db.open_table(name=self.tbl1_name)
        tbl2 = db.open_table(name=self.tbl2_name)
        return db, tbl1, tbl2

# methods for processing text, and splitting to sentences
class Processor:
    @classmethod
    def clean_text(cls, text: str) -> str:
        if not text:
            return None
        # two step decoding for double escape
        try:
            text = codecs.decode(text, 'unicode-escape') 
        except:
            pass
        for i in range(2):
            try:
                text = text.encode('latin-1').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                break
            
        return text 

# methods around pruning, cleaning, and diagnosing the corpus
class CorpusManager:
    def __init__(self, tbl1: lancedb.Table, tbl2: lancedb.Table):
        self.tbl1 = tbl1
        self.tbl2 = tbl2

    # reset validation flags
    def reset_validation_bool_flags(self):
        self.tbl2.update(values_sql={
        'is_validated': 'cast(false as boolean)'
        })
    
    # reset modelling + validation flags(self):
    def reset_modelling_bool_flags(self):
        self.tbl2.update(values_sql={
        'is_modelled': 'cast(false as boolean)'
        })
        self.reset_validation_bool_flags()

    # reset embedding + modelling + validating flags   
    def reset_embedding_bool_flags(self):
        self.tbl2.update(values_sql={
            'is_embedded': 'cat(false as boolean)'
        })
        self.reset_modelling_bool_flags()

    # reset processing flags
    def reset_processing_flags(self):
        self.tbl1.update(values_sql={
            'is_processed': 'cat(false as boolean)'
        })
        self.reset_embedding_bool_flags()
    
    # clean lancedb size: reduces size of lancedb
    def clean_lancedb(self, days: int = 0):
        # compact data
        self.tbl1.compact_files()
        self.tbl2.compact_files()

        # clean old versioning
        self.tbl1.cleanup_old_versions(
            older_than=timedelta(days=days),
            delete_unverified=True
        )
        self.tbl2.cleanup_old_versions(
            older_than=timedelta(days=days),
            delete_unverified=True
        )