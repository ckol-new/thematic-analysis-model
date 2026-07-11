import lancedb
import random
from ..config import *

# utility functions

# for a given query condition, shuffle integer _rowids from database that meets that condition
# return list of ids, shuffled by condition
#   if query = None, shuffle entire table
def shuffle_by_condition(tbl: lancedb.Table, query: str | None) -> list[int]:
    # query _rowid by condition
    if not query:
        ids = tbl.search().with_row_id(True).select(['_rowid']).to_arrow()['_rowid'].to_pylist()
    else: 
        ids = tbl.search().where(query).with_row_id(True).select(['_rowid']).to_arrow()['_rowid'].to_pylist()

    # shuffle
    random.shuffle(ids)
    
    # return
    return ids

# generator returning dataframes from list of ids, in the form of batches
# each id is a lancedb _rowid (not uuid, or hash_)
# columns field allows for selection of specific columns from table, if none return all columns
def batch_generator(ids: list[int], tbl: lancedb.Table, columns: list[str] = None, BATCH_SIZE: int = FILE_IO_BATCH_SIZE_DEFUALT):
    # paginate through ids
    total = len(ids)
    for i in range(0, total, BATCH_SIZE):
    #   take from table
        batch_ids = ids[i:i+BATCH_SIZE]
        if not columns:
            batch_df = tbl.take_row_ids(batch_ids).to_pandas()
        else: 
            batch_df = tbl.take_row_ids(batch_ids).select(columns).to_pandas() # common source of error

    #   yield batch
        yield batch_df