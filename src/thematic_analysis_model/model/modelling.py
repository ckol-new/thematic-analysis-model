# all classes around modelling
import pandas as pd
import lancedb
from pathlib import Path
import numpy as np
import copy
from tqdm import tqdm
import gc

from .dclasses import TrialConfig, ValidationMetrics
from .util import shuffle_ids, batch_generator, get_ids_by_condition
from ..config import MODELLING_BATCH_SIZE_DEFAULT, EMBEDDING_MODEL_NAME

from bertopic import BERTopic 
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

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
        for batch in batch_generator(ids=shuffled_ids, tbl=self.tbl, columns=['vector', 'uuid', 'sentence'], BATCH_SIZE=MODELLING_BATCH_SIZE_DEFAULT): 
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
    def __init__(self, tbl: lancedb.Table, topic_model: BERTopic, embedding_model: SentenceTransformer):
        self.tbl = tbl
        self.topic_model = topic_model
        self.topic_model.calculate_probabilities = True
        self.embedding_model = embedding_model

    # validate
    def validate(self, BATCH_SIZE: int = MODELLING_BATCH_SIZE_DEFAULT):
        # get relevant ids in model
        query = 'is_modelled = true'
        ids = get_ids_by_condition(tbl=self.tbl, query=query)

        # recover data
        self.transform_model(ids, BATCH_SIZE=BATCH_SIZE)

        # get validation metrics
        

        # serialize validation metrics + figures
        ...

    # recover probabilities + topics
    def transform_model(self, ids: list[int], BATCH_SIZE: int = MODELLING_BATCH_SIZE_DEFAULT):
        # for batch in ids
        for batch in batch_generator(ids=ids, tbl=self.tbl, columns=['uuid', 'vector', 'sentence'], BATCH_SIZE=BATCH_SIZE):
            # transform batch
            uuids = batch['uuid'].tolist()
            embeddings = np.array(batch['vector'].tolist())
            documents = batch['sentence'].tolist()

            # note topics as int, for each doc + probs as 2D numpy array: ROW = doc index, COL= topic index
            topics, probs = self.topic_model.transform(documents=documents, embeddings=embeddings)

            # update database
            self.save_probability_topic_data(uuids=uuids, topics=topics, probs=probs)


    def save_probability_topic_data(self, uuids: list[str], topics, probs):
        payload = [
            {
                'uuid': uid,
                'topic': topic,
                'probabilities': list(prob),
                'is_validated': True
            } for uid, topic, prob in zip(uuids, topics, probs, strict=True)
        ]
        (
            self.tbl.merge_insert(on='uuid')
            .when_matched_update_all()
            .execute(payload)
        )

    # return validation metrics
    def get_validation_metrics(self) -> ValidationMetrics:
        # get NPMI

        # get pairwise embedding distance
        all_topic_pairwise_distance, pairwise_distance_by_topic = self.get_pairwise_embedding_distance()

        # get intertopic cosine similarity


        # get topic diversity

        # get probability data

        # get ARI

        # get bootstrap resampling stability

        validation_metrics = ValidationMetrics()
        return validation_metrics
    
    def get_pairwise_embedding_distance(self):
        topic_info = self.topic_model.get_topics()
        topics = [
            [
                word for word, _ in topic_info[topic]
            ] for topic in topic_info if topic != -1
        ]

        all_topic_scores = [] # pair-wise embedding avg for each topic
        for topic_words in topics: 
            topic_embeddings = self.embedding_model.encode(topic_words, device='mps')
            similarity_matrix = cosine_similarity(topic_embeddings)
            upper_triangle_indices = np.triu_indices_from(similarity_matrix, k=1)
            pairwise_scores = similarity_matrix[upper_triangle_indices]

            if len(pairwise_scores) > 0:
                all_topic_scores.append(np.mean(pairwise_scores)) 

        all_topic_avg = float(np.mean(all_topic_scores)) if all_topic_scores else 0.0
        return all_topic_avg, all_topic_scores
