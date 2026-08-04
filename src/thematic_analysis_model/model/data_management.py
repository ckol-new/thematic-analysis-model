from .frozen_umap_model import FrozenParametricUMAP
from .config import DATABASE_PATH, CONTENT_TBL_NAME, SENTENCE_TBL_NAME, MODEL_OUTPUT_TBL_NAME, FILE_IO_BATCH_SIZE, EMBEDDING_MODEL_NAME
from .dataclasses import Content, Sentence, ModelOutput, TrialConfig

import lancedb
import pandas as pd
import random
from pathlib import Path
from datetime import timedelta

from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from umap import UMAP
from umap.parametric_umap import ParametricUMAP
from hdbscan import HDBSCAN
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer


# managing data: Loading data, cleaning database
#   while other classes can interact with the data, update the data, and read from data, this is more for general data management.


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

    # load embedding model
    def load_embedding_model(self, model_name: str = EMBEDDING_MODEL_NAME):
        return SentenceTransformer(model_name)

    # load bertopic model
    #   Load from trial config, or defualt paramters
    def load_bertopic_model(self, trial_config: TrialConfig | None = None) -> BERTopic:
        if not trial_config:
            embedding_model = self.load_embedding_model()
            umap_model = UMAP(random_state=42)
            hdbscan_model = HDBSCAN()
            vectorizer_model = CountVectorizer(stop_words='english')
            ctfidf_model = ClassTfidfTransformer()
            bertopic_model = BERTopic(
                embedding_model=embedding_model,
                umap_model=umap_model,
                hdbscan_model=hdbscan_model,
                vectorizer_model=vectorizer_model,
                ctfidf_model=ctfidf_model,
                calculate_probabilities=False, # change later
            )
        else: # this needs to be updated as I change what parameters I am tuning
            embedding_model = self.load_embedding_model(model_name=trial_config.embedding_model)
            if trial_config.umap_parametric:
                umap_model = FrozenParametricUMAP() # load global parametric umap 
            else:
                umap_model = UMAP(
                    n_neighbors=trial_config.umap_n_neighbours,
                    n_components=trial_config.umap_n_components,
                    metric=trial_config.umap_metric,
                    min_dist=trial_config.umap_min_dist,
                    random_state=trial_config.umap_random_state
                )
            hdbscan_model = HDBSCAN(
                min_cluster_size=trial_config.hdbscan_min_cluster_size,
                min_samples=trial_config.hdbscan_min_samples,
                metric=trial_config.hdbscan_metric,
                cluster_selection_method=trial_config.hdbscan_cluster_selection_method,
                prediction_data=False
            )
            vectorizer_model = CountVectorizer(stop_words='english') # need to do this later
            ctfidf_model = ClassTfidfTransformer()
            bertopic_model = BERTopic(
                embedding_model=embedding_model,
                umap_model=umap_model,
                hdbscan_model=hdbscan_model,
                vectorizer_model=vectorizer_model,
                ctfidf_model=ctfidf_model,
                calculate_probabilities=False, # change later
                nr_topics=trial_config.nr_topics,
                top_n_words=trial_config.top_n_words
            )
        return bertopic_model


    def load_untrained_parametric_umap(self, trial_config: TrialConfig):
        umap_model = ParametricUMAP(
            n_neighbors=trial_config.umap_n_neighbours,
            n_components=trial_config.umap_n_components,
            metric=trial_config.umap_metric,
            min_dist=trial_config.umap_min_dist,
            random_state=trial_config.umap_random_state,
            batch_size=1000,
            n_epochs=200,
            verbose=True
        )
        return umap_model
        ...


# Manager class:
#   Manages data, updates boolean flags, clears history to save space.
#   Manager can be passed to classes that require ability to alter database state, at a broad level.
#   Anything that wants to interface with the data, goes through the manager.
class Manager:
    # 
    def __init__(self, loader: Loader):
        self.__loader = loader # loader to access data
        self.tbl1, self.tbl2, self.tbl3 = self.__loader.connect_all() 

    # clean lance versioning, save space
    def clean_lancedb(self, days: int = 1):
        ctbl = self.__loader.connect(CONTENT_TBL_NAME)
        stbl = self.__loader.connect(SENTENCE_TBL_NAME)
        motbl = self.__loader.connect(MODEL_OUTPUT_TBL_NAME)

        ctbl.optimize(cleanup_older_than=timedelta(days=days))
        stbl.optimize(cleanup_older_than=timedelta(days=days))
        motbl.optimize(cleanup_older_than=timedelta(days=days))


    def check_tbl_name(self, tbl_name: str) -> lancedb.Table:
        # get relevant table
        if self.tbl1.name == tbl_name:
            tbl = self.tbl1
        elif self.tbl2.name == tbl_name:
            tbl = self.tbl2
        elif self.tbl3.name == tbl_name:
            tbl = self.tbl3
        else: 
            raise Exception(f'Error; no table of name {tbl_name} in lance')

        return tbl

    def reset_processed_flags(self):
        tbl = self.check_tbl_name(SENTENCE_TBL_NAME)
        tbl.update(values_sql={
            'is_processed': 'cast(false as boolean)'
        })
        self.reset_embedding_flags()
    def reset_embedding_flags(self):
        tbl = self.check_tbl_name(SENTENCE_TBL_NAME)
        tbl.update(values_sql={
            'is_embedded': 'cast(false as boolean)'
        })
        self.reset_modelling_flags()
    def reset_modelling_flags(self):
        tbl = self.check_tbl_name(SENTENCE_TBL_NAME)
        tbl.update(values_sql={
            'is_modelled': 'cast(false as boolean)'
        })
        self.reset_validation_flags()
    def reset_validation_flags(self):
        tbl = self.check_tbl_name(SENTENCE_TBL_NAME)
        tbl.update(values_sql={
            'is_validated': 'cast(false as boolean)'
        })

    # returns number of rows that matches its condition
    #   if condition is none, returns length of db
    def get_num_match_condition(self, tbl_name: str, condition: str | None = None):
        tbl = self.check_tbl_name(tbl_name=tbl_name)
        if not condition:
            return tbl.count_rows()
        else:
            return tbl.count_rows(filter=condition)


    # retrieve rowids by condition and/or limit
    #   optional shuffling
    def retrieve_rowids(self, tbl_name: str, condition: str | None = None, limit: int | None = None, shuffle: bool = False) -> list[int]:
        tbl = self.check_tbl_name(tbl_name=tbl_name)

        # check if limit
        if not limit:
            query_limit: int = tbl.count_rows() + 1 # set limit to greater than table length to get all rows

        # check condition
        if not condition:
            ids = tbl.search().with_row_id(True).select(['_rowid']).limit(query_limit).to_arrow()['_rowid'].to_pylist()
        else:
            ids = tbl.search().where(condition).with_row_id(True).select(['_rowid']).to_arrow()['_rowid'].to_pylist()

        # check if shuffle
        if shuffle:
            random.shuffle(ids)

        return ids

    # retrieve data in batches (generator)
    #   optional shuffling, limits, and column conditions
    #   returns dataframes
    def batch_generator(self, tbl_name: str, condition: str | None = None, limit: int | None = None, shuffle: bool = False, columns: list[str] | None = None, BATCH_SIZE: int = FILE_IO_BATCH_SIZE) -> pd.DataFrame:
        # get relevant tbl
        tbl = self.check_tbl_name(tbl_name=tbl_name)

        # get ids (by condition, by limit, optionally shuffled)
        ids: list[int] = self.retrieve_rowids(
            tbl_name=tbl_name,
            condition=condition,
            limit=limit,
            shuffle=shuffle
        )

        # yield in batches
        #   paginate through ids, and return
        for i in range(0, len(ids), BATCH_SIZE):
            batch_ids = ids[i:i+BATCH_SIZE]

            # check which columns to retrieve
            if not columns:
                batch_df = tbl.take_row_ids(batch_ids).to_pandas()
            else:
                batch_df = tbl.take_row_ids(batch_ids).select(columns).to_pandas()
            yield batch_df

    # retrieve column as list
    def retrieve_column_list(self, tbl_name: str, condition: str | None = None, limit: int | None = None, shuffle: bool = False, columns: list[str] | None = None) -> list[any]:
        tbl = self.check_tbl_name(tbl_name=tbl_name)
        if not columns:
            raise Exception("Must input valid column to retrieve column as list")
        if len(columns) != 1:
            raise Exception("Must input only one column to retrieve as list")

        if not limit:
            limit = tbl.count_rows() + 1 # greater than size of db

        if not condition:
            arr = tbl.search().limit(limit).select(columns).to_arrow()[columns[0]].to_pylist()
        else:
            arr = tbl.search().where(condition).limit(limit).select(columns).to_arrow()[columns[0]].to_pylist()

        return arr

    # when not matching on column, insert data.
    #   for deduplication mostly
    def deduplicate_insert(self, tbl_name: str, key: str, data: list[dict]):
        tbl = self.check_tbl_name(tbl_name=tbl_name)
        (
            tbl.merge_insert(on=key)
            .when_not_matched_insert_all()
            .execute(data)
        )

    # when data matches key, update the following rows according to data
    def matched_update(self, tbl_name: str, key: str, data: list[dict]):
        tbl = self.check_tbl_name(tbl_name=tbl_name)
        (
            tbl.merge_insert(on=key)
            .when_matched_update_all()
            .execute(data)
        )

    def get_model_output(self, condition: str | None, semantic_search: bool = False) -> list[ModelOutput]:
        tbl = self.check_tbl_name(tbl_name=MODEL_OUTPUT_TBL_NAME)

        if not condition:
            result = tbl.search().to_pydantic(model=ModelOutput)
        elif semantic_search:
            result = tbl.search(condition).to_pydantic(model=ModelOutput)
        else:
            result = tbl.search().where(condition).to_pydantic(model=ModelOutput)

        return result

    def add_model_output(self, model_output: ModelOutput):
        tbl = self.check_tbl_name(tbl_name=MODEL_OUTPUT_TBL_NAME)
        tbl.add([model_output])


    # save model, either as safetensors or pickle
    def save_model(self, path: Path | str, model: BERTopic, serialization: str = 'safetensors'):
        model.save(path=path, serialization=serialization)

    def load_model(self, path: Path | str) -> BERTopic:
        return BERTopic.load(path=path, embedding_model=EMBEDDING_MODEL_NAME)
