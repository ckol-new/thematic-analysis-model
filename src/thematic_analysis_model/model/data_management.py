# managing data: Loading data, cleaning database
#   while other classes can interact with the data, update the data, and read from data, this is more for general data management.
from .config import DATABASE_PATH, CONTENT_TBL_NAME, SENTENCE_TBL_NAME, MODEL_OUTPUT_TBL_NAME
from .dataclasses import Content, Sentence, ModelOutput

import lancedb
import random
from pathlib import Path


# Loader class:
#   loads data, returns connection + lancedb tables. 
#   Generally, a single loader will be passed to other classes to enable them to make database connections. Rather than passing a bunch 
#   of connections around.
class Loader:
    def __init__(self, LANCE_PATH: Path = DATABASE_PATH, tbl1_name: str = CONTENT_TBL_NAME, tbl2_name: str = SENTENCE_TBL_NAME, tbl3_name: str = MODEL_OUTPUT_TBL_NAME):
        self.LANCE_PATH = LANCE_PATH
        self.tbl1_name = tbl1_name
        self.tbl2_name = tbl2_name
        self.tbl3_name = tbl3_name

        # connect to DB
        self.db = lancedb.connect(self.LANCE_PATH)

    # first time creating tables, or restarting
    def first_init(self):
        self.db.create_table(name=self.tbl1_name, schema=Content, mode='overwrite')
        self.db.create_table(name=self.tbl2_name, schema=Sentence, mode='overwrite')
        self.db.create_table(name=self.tbl3_name, schema=ModelOutput, mode='overwrite')

    # getting access to tables: returns tuple of tbl1 (content), tbl2 (sentence), and tbl3 (model output)
    def connect_all(self):
        tbl1 = self.db.open_table(name=self.tbl1_name)
        tbl2 = self.db.open_table(name=self.tbl2_name)
        tbl3 = self.db.open_table(name=self.tbl3_name)
        return  tbl1, tbl2, tbl3

    # connect to one table
    def connect(self, name: str):
        return self.db.open_table(name=name)


# Manager class:
#   Manages data, updates boolean flags, clears history to save space.
#   Manager can be passed to classes that require ability to alter database state, at a broad level.
#   Updates tables
class Manager:
    # 
    def __init__(self, loader: Loader):
        self.loader = loader # loader to access data
        self.tbl1, self.tbl2, self.tbl3 = self.loader.connect_all() 
        self.tbl1.name

    # retrieve rowids by condition and/or limit
    #   optional shuffling
    def retrieve_rowids(self, tbl_name: str, condition: str | None = None, limit: int | None = None, shuffle: bool = False) -> list[int]:
        # get relevant table
        if self.tbl1.name == tbl_name:
            tbl = self.tbl1
        elif self.tbl2.name == tbl_name:
            tbl = self.tbl2
        elif self.tbl2.name == tbl_name:
            tbl = self.tbl2
        else: 
            raise Exception(f'Error; no table of name {tbl_name} in lance')

        # check if limit
        if not limit:
            query_limit: int = tbl.count_rows() + 1 # set limit to greater than table length to get all rows

        # check condition
        if not condition:
            ids = tbl.search()._with_row_id(True).select(['_rowid']).limit(query_limit).to_arrow()['_rowid'].to_pylist()
        else:
            ids = tbl.search().where(condition)._with_row_id(True).select(['_rowid']).to_arrow()['_rowid'].to_pylist()

        # check if shuffle
        if shuffle:
            random.shuffle(ids)

        return ids
            


    # retrieve data in batches (generator)
    #   optional shuffling, limits, and column conditions


    # 



