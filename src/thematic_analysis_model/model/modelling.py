from .data_management import Manager, Loader
from .dataclasses import TrialConfig
from .config import SENTENCE_TBL_NAME, MODEL_BATCH_SIZE, MERGE_BATCH_SIZE

from bertopic import BERTopic
from tqdm import tqdm
from copy import deepcopy
import numpy as np
import gc

# class around modelling
class Modeller:
    def __init__(self, loader: Loader, manager: Manager, trial_config: TrialConfig | None):
        self.loader = loader
        self.manager = manager
        self.trial_config = trial_config

    # main entry
    #   returns final merged bertopic model
    def run_modeller(self, mode: str = 'merge_models', save_reduced_embeddings: bool = False, MERGE_BATCH_SIZE: int = MERGE_BATCH_SIZE) -> BERTopic:
        # load models, based on config or default

        # determine mode to model by
        mode_dict = {
            'merge_models': self.merge_model,
            'agglomerative': self.agglomerative_merge
        }
        selected_merge_mode = mode_dict[mode]

        # batch model
        pbar = tqdm(
            total=self.manager.get_num_match_condition(SENTENCE_TBL_NAME, condition='is_modelled = false'),
            desc='MODELLING',
            unit='sentences'
            )
        submodels: list[BERTopic] = []
        baseline_model = self.loader.load_bertopic_model(trial_config=self.trial_config)

        for batch in self.manager.batch_generator(
            tbl_name=SENTENCE_TBL_NAME,
            condition='is_modelled = false',
            shuffle=True, #important that it is shuffled
            columns=['sentence', 'embedding', 'uuid_'],
            BATCH_SIZE=MODEL_BATCH_SIZE
        ):
            docs = batch['sentence'].tolist()
            embeddings = batch['embedding'].tolist()
            uuids = batch['uuid_'].tolist()

            # duplicate model 
            empty_model = deepcopy(baseline_model)

            # model batch, save data + update bools
            sub_model: BERTopic = empty_model.fit(documents=docs, embeddings=embeddings) 
            self.save_model_data(model=sub_model, uuids=uuids, save_reduced_embeddings=save_reduced_embeddings)
            submodels.append(sub_model)

            # merge models
            if len(submodels) >= MERGE_BATCH_SIZE:
                merged_model = selected_merge_mode(submodels=submodels)
                submodels.clear()
                gc.collect()

                submodels.append(self.merge_model)

            # update pbar
            pbar.update(len(uuids))

        pbar.close()

        # merge leftover models
        if len(submodels) != 1:
            merged_model = selected_merge_mode(submodels=submodels)
            submodels.clear()
            gc.collect()
            return merged_model
        else:
            return submodels[0]

    # merge model data: using default .merge_models()
    def merge_model(self, submodels: list[BERTopic]) -> BERTopic:
        return BERTopic.merge_models(submodels)

    # agglomerative clustering merge
    def agglomerative_merge(self, submodels: list[BERTopic]) -> BERTopic:
        return


    # save data and update bools
    def save_model_data(self, model: BERTopic, uuids: list[str], save_reduced_embeddings: bool = False):
        if not save_reduced_embeddings:
            data = [
                {
                    'uuid_': uuid,
                    'is_modelled': True,
                } for uuid in uuids
            ]
        else:
            reduced_embeddings = model.umap_model.embedding_
            data = [
                {
                    'uuid_': uuid,
                    'is_modelled': True,
                    'reduced_embedding': r_embedding
                } for uuid, r_embedding in zip(uuids, reduced_embeddings, strict=True)
            ]

        self.manager.matched_update(
            tbl_name=SENTENCE_TBL_NAME,
            key='uuid_',
            data=data
        )