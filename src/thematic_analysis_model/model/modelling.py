from .frozen_umap_model import FrozenParametricUMAP
from .data_management import Manager, Loader
from .dataclasses import TrialConfig
from .config import SENTENCE_TBL_NAME, MODEL_BATCH_SIZE, MERGE_BATCH_SIZE, FILE_IO_BATCH_SIZE, GLOBAL_PARAMETRIC_UMAP_PATH, GLOBAL_PARAMETRIC_UMAP_ENCODER_PATH

from bertopic import BERTopic
from umap import ParametricUMAP, load_ParametricUMAP
from pathlib import Path
from tqdm import tqdm
import keras
from copy import deepcopy
import numpy as np
import gc
import pandas as pd
import plotly.express as px


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
        baseline_model.verbose=False # make sure it is false

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
            # if parametric umap, needs fresh instantiation
            if self.trial_config.umap_parametric:
                empty_model = self.loader.load_bertopic_model(trial_config=self.trial_config)
            else:
                empty_model = deepcopy(baseline_model)

            # model batch, save data + update bools
            if self.trial_config.umap_parametric:
                sub_model: BERTopic = empty_model.fit(documents=docs, embeddings=np.array(embeddings))
            else:
                sub_model: BERTopic = empty_model.fit(documents=docs, embeddings=np.array(embeddings)) 
            self.save_model_data(model=sub_model, uuids=uuids, save_reduced_embeddings=save_reduced_embeddings)
            submodels.append(sub_model)

            # merge models
            if len(submodels) >= MERGE_BATCH_SIZE:
                merged_model = selected_merge_mode(submodels=submodels)
                submodels.clear()
                gc.collect()
                submodels.append(merged_model)

            # update pbar
            pbar.update(len(uuids))

        pbar.close()

        # merge leftover models
        if len(submodels) == 0:
            raise Exception('Failed to train model, or add model to submodels')
        elif len(submodels) == 1:
            return submodels[0]
        else:
            merged_model = selected_merge_mode(submodels=submodels)
            submodels.clear()
            gc.collect()
            return merged_model

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


    # model paremetric umap (DONE ONCE)
    #   save encoder layers, not model -> load this later.
    def model_paremetric_umap(self, umap_model: ParametricUMAP, save_path: Path, sample_size: int = FILE_IO_BATCH_SIZE):
        embeddings = self.manager.retrieve_column_list(SENTENCE_TBL_NAME, limit=sample_size, shuffle=True, columns=['embedding'])
        umap_model.fit(np.array(embeddings))
        umap_model.encoder.save(save_path /'global_model.keras')

        loss = umap_model.parametric_model.history.history['loss']
        loss_dict = {i: l for i, l in enumerate(loss)}
        loss_df = pd.DataFrame(list(loss_dict.items()), columns=['Epochs', 'Loss'])

        fig = px.line(loss_df, x='Epochs', y='Loss', title='Loss Curve of Global Parametric UMAP Model')
        return fig
    