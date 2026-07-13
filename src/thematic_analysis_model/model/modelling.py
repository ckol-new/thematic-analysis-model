# all classes around modelling
import pandas as pd
import lancedb
from pathlib import Path
import numpy as np
import copy
from tqdm import tqdm
import gc

from .util import shuffle_ids, batch_generator, get_ids_by_condition
from ..config import MODELLING_BATCH_SIZE_DEFAULT, EMBEDDING_MODEL_NAME

from bertopic import BERTopic 

class Modeller:
    def __init__(self, tbl: lancedb.Table, topic_model: BERTopic):
        self.tbl = tbl
        self.topic_model = topic_model
        self.merged_model = None # will be made after .model() is called

    # merge in batches, merge submodels, return merged model
    def model(self, MERGE_INTERVAL: int = 20, SAVE_INTERVAL: int = 100) -> BERTopic:
        # shuffle ids to model
        query: str = 'is_modelled = false'
        shuffled_ids: list[int] = shuffle_ids(
            ids=get_ids_by_condition(tbl=self.tbl, query=query)
            )
        pbar = tqdm(total=len(shuffled_ids), desc="MODELLING", unit="sentences")

        # for each batch
        submodels: list[BERTopic] = []
        count = 0
        for batch in batch_generator(ids=shuffled_ids, tbl=self.tbl, columns=['vector', 'uuid', 'sentence'], BATCH_SIZE=2000): 
            # model batch
            # update bools
            current_uuids = batch['uuid'].tolist()
            current_embeddings = batch['vector'].tolist()
            current_docs = batch['sentence'].tolist()

            submodel = self.model_batch(uuids=current_uuids, embeddings=current_embeddings, documents=current_docs, pbar=pbar)
            submodels.append(submodel)
            count += 1

            # if num of submodels too high, merge
            if len(submodels) >= MERGE_INTERVAL:
                submodels: list[BERTopic] = self.merge_submodels(submodels=submodels)
                
            # serialize submodels every interval
            if count >= SAVE_INTERVAL:
                # does nothing yet
                ...

        pbar.close()
        # final merge 
        if len(submodels) != 1:
            submodels = self.merge_submodels(submodels=submodels)
            return submodels[0]
        return submodels[0]

    # model batch return sub model
    # update bools
    def model_batch(self, uuids: list[str], embeddings: list[float], documents: list[str], pbar: tqdm):
        # copy empty topic model
        submodel: BERTopic = copy.deepcopy(self.topic_model)

        # model
        submodel.fit(documents=documents, embeddings=np.array(embeddings))
        pbar.update(len(uuids))
        
        # update bools
        payload = [
            {
                'uuid': uid,
                'is_modelled': True
            } for uid in uuids
        ]
        (
            self.tbl.merge_insert(on='uuid')
            .when_matched_update_all()
            .execute(payload)
        )

        return submodel

    # method for merging models
    def merge_submodels(self, submodels: list[BERTopic]) -> list[BERTopic]:
        merged_model = BERTopic.merge_models(submodels)
        submodels.clear()
        gc.collect()

        submodels.append(merged_model) # new submodels
        return submodels

    @classmethod
    def save_model(self, model: BERTopic, path: Path):
        model.save(path=path, save_embedding_model=True, serialization='safetensors')

    @classmethod
    def load_model(self, path: Path, embedding_model = EMBEDDING_MODEL_NAME) -> BERTopic:
        model = BERTopic.load(path=path, embedding_model=embedding_model)
        return model

class Validator:
    ...