from lancedb import Table
import gc
import random
from bertopic import BERTopic
from pathlib import Path
import copy
import tqdm
import numpy as np


class TopicModeller:
    def __init__(self):
        ...

    @classmethod
    def run_pipeline(cls, tbl: Table, spath: Path, model: BERTopic | None = None, SHUFFLE_BATCH_SIZE: int = 1024, MODEL_BATCH_SIZE: int = 50000, SAVE_INTERVAL: int = 20):
        if not model:
            model = cls.load_model(spath)
        else:
            model = model

        # get rows and shuffle
        shuffled_rows: list[int] = cls.shuffle(tbl)

        # load as batches
        current_embeddings = []
        current_documents = []
        current_ids = []
        total = tbl.count_rows(filter='is_modelled = false')
        pbar = tqdm.tqdm(desc='MODELLING', total=total, unit='sentence')
        sub_models = []
        for shuffled_batch in cls.batch_generator(tbl, shuffled_rows, SHUFFLE_BATCH_SIZE):
            # add to current batch
            current_documents.extend(shuffled_batch['sentence'].to_list())
            current_embeddings.extend(shuffled_batch['vector'].to_list())
            current_ids.extend(shuffled_batch['sentence_uuid'].to_list())

            del shuffled_batch
            gc.collect()

            # check if time to do batch
            if len(current_ids) >= MODEL_BATCH_SIZE:
                # model
                sub_model = copy.deepcopy(model)
                sub_model = cls.fit_model(tbl, sub_model, current_ids, current_embeddings, current_documents) # fit model and update flags
                sub_models.append(sub_model)

                pbar.update(len(current_ids))

                # clear current batch
                current_documents.clear()
                current_embeddings.clear()
                current_ids.clear()

            
            # check if time to merge and save
            if len(sub_models) >= SAVE_INTERVAL:
                merged_model = BERTopic.merge_models(sub_models)
                sub_models.clear()
                sub_models.append(merged_model)
                # save merged model (save progress)
                cls.save_model(spath, merged_model)

        pbar.close()

        # check if still current things to model
        if len(current_ids) != 0:
                # model
                sub_model = copy.deepcopy(model)
                sub_model = cls.fit_model(tbl, sub_model, current_ids, current_embeddings, current_documents) # fit model and update flags
                sub_models.append(sub_model)

                # clear current batch
                current_documents.clear()
                current_embeddings.clear()
                current_ids.clear()
        
        # check if there is anything that needs to be merged first
        if len(sub_models) != 1:
            merged_model = BERTopic.merge_models(sub_models)
            del sub_models
            gc.collect()
            return merged_model
        else:
            return sub_models[0] # return merged_model in first position

    @classmethod
    def shuffle(cls, tbl: Table) -> list[int]:
        row_ids = tbl.search().where('is_modelled = false').with_row_id(True).select(['sentence_uuid']).to_arrow()
        ids = row_ids['_rowid'].to_pylist()
        random.shuffle(ids)
        return ids
    
    @classmethod
    def batch_generator(cls, tbl: Table, ids: list[int], SHUFFLE_BATCH_SIZE: int = 1024):
        total = tbl.count_rows(filter='is_modelled = false')
        for i in range(0, total, SHUFFLE_BATCH_SIZE):
            batch_ids = ids[i:i+SHUFFLE_BATCH_SIZE]
            batch = tbl.take_row_ids(batch_ids).to_pandas()
            yield batch

            del batch_ids, batch
            gc.collect()

    @classmethod
    def fit_model(cls, tbl: Table, model: BERTopic, ids, embeddings, sentences):
        model.fit(documents=sentences, embeddings=np.array(embeddings))

        # update boolean flags
        upsert_dict = [
            {
                'sentence_uuid': my_uuid,
                'is_modelled': True
            } for my_uuid in ids
        ]
        (
            tbl.merge_insert(on='sentence_uuid')
            .when_matched_update_all()
            .execute(upsert_dict)
        )

        return model

    @classmethod
    def save_model(cls, spath: Path, model: BERTopic):
        model.save(spath, serialization='pickle', save_embedding_model=True, save_ctfidf=True)

    @classmethod
    def load_model(cls, spath: Path):
        model = BERTopic.load(spath)
        return model
        
    @classmethod
    def reset_flags(cls, tbl: Table):
        tbl.update(
            values_sql={"is_modelled": "false"}
        )