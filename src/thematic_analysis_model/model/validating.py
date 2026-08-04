from .data_management import Loader, Manager
from .dataclasses import TrialConfig, ValidationMetric, ModelOutput
from .config import SENTENCE_TBL_NAME, VALIDATING_BATCH_SIZE, FILE_IO_BATCH_SIZE, MODEL_OUTPUT_TBL_NAME
from thematic_analysis_model.view.visualizing import Visualizer

from bertopic import BERTopic
from bertopic.dimensionality import BaseDimensionalityReduction
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
import gc
import pandas as pd
import numpy as np
import uuid
import json
import math
import ast

# topic stability metrics
import itertools
from typing import Dict, List, Union, Optional, Tuple, Any
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score, adjusted_mutual_info_score
from sklearn.metrics.pairwise import cosine_similarity

# validation of models
class Validator:
    def __init__(self, model: BERTopic, loader: Loader, manager: Manager, visualizer: Visualizer, trial_config: TrialConfig | None = None):
        self.model = model
        self.model.calculate_probabilities = True
        self.visualizer = visualizer
        self.loader = loader
        self.manager = manager
        self.trial_config = trial_config

    # main entry
    #   validates, generates validation metrics, reassigns document positions, generates visuals, serializes Model Output
    def run_validator(self) -> ModelOutput:
        # reassign document position
        self.reassign_document_position()

        # generate validation metrics
        validation_metric = self.get_validation_metrics()

        # get data for reproducibility testing
        doc_ids, doc_topics, valid_topics, topic_vectors, topic_words = self.get_stability_data()

        # generate visualizations/figures
        topic_map, doc_map, heatmap, hierarchy_map = self.get_visualizations()
        topic_map = topic_map.to_json(engine='orjson')
        doc_map = doc_map.to_json(engine='orjson') if doc_map else None
        heatmap = heatmap.to_json(engine='orjson')
        hierarchy_map = hierarchy_map.to_json(engine='orjson')

        # save model output
        print('saving output')
        if not self.trial_config: 
            return validation_metric, topic_map, doc_map, heatmap, hierarchy_map
        else:
            model_output = ModelOutput(
                trial_config=self.trial_config,
                validation_metrics=validation_metric.model_dump_json(),
                doc_ids=json.dumps(doc_ids),
                doc_topics=json.dumps(doc_topics),
                valid_topics=json.dumps(valid_topics),
                topic_vectors=json.dumps(topic_vectors),
                topic_words=json.dumps(topic_words),
                topic_map=topic_map,
                document_map=doc_map,
                heatmap=heatmap,
                hierarchy_map=hierarchy_map
            )
        print('a')
        self.manager.add_model_output(model_output=model_output)
        return model_output

    # reassings document position in loaded model
    #   returns reduced embedding values for later (visualize document position)
    #   serialize data to lance
    #   use transform
    def reassign_document_position(self):
        pbar = tqdm(
            total=self.manager.get_num_match_condition(tbl_name=SENTENCE_TBL_NAME, condition='is_validated = false'),
            desc='RECOVERING DOCUMENT POSITION',
            unit='sentence'
        )
        # get batch of document
        #   transform
        #   serialize data output (reduced embeddings, topic, probability data)
        for batch in self.manager.batch_generator(
            tbl_name=SENTENCE_TBL_NAME,
            condition='is_validated = false AND is_modelled = true',
            shuffle=True,
            columns=['sentence', 'embedding', 'uuid_'],
            BATCH_SIZE=VALIDATING_BATCH_SIZE # OOM concerns
        ):
            docs = batch['sentence'].tolist()
            uuids = batch['uuid_'].tolist()
            embeddings = batch['embedding'].tolist()

            topics, probs = self.model.transform(documents=docs, embeddings=np.array(embeddings))
            reduced_embeddings = self.model.umap_model.transform(embeddings)

            # serialize data
            data = [
                {
                    'uuid_': uuid,
                    'is_validated': True,
                    'reduced_embedding': list(red_embedding),
                    'topic': topic,
                    'probabilities': list(prob),
                } for uuid, red_embedding, topic, prob in zip(uuids, reduced_embeddings, topics, probs, strict=True)
            ]
            self.manager.matched_update(
                tbl_name= SENTENCE_TBL_NAME,
                key='uuid_',
                data=data
            )               
            pbar.update(len(data))
        pbar.close()

    # get validation metrics
    #   including NPMI score, pairwise topic coherence, intertopic cosine similarity, topic diversity, probability values, redundant pairs, stability metrics
    def get_validation_metrics(self) -> ValidationMetric:
        print('getting validation metrics')
        # get NPMI
        #   NEED TO IMPLEMENT THIS
        npmi_core = 1.0

        # get pairwise embedding coherence score
        #   Cosine similarity across topic representation
        total_pairwise_distance, topics_pairwise_distance = self.get_pairwise_embedding_distance()

        # topic diversity
        topic_diversity = self.get_topic_diversity()

        # intertopic cosine similarity score
        #    and get redundant pairs
        mean_cos_similarity, max_cos_similarity, redundant_pairs = self.get_intertopic_cosine_similarity(REDUNDANT_PAIR_THRESHOLD=0.7)

        # topic probabilities
        #   avg probability, avg prob per cluster, plus raw probability data
        noise_ratio, probability_data_by_topic = self.get_probability_data()

        validation_metrics = ValidationMetric(
            num_topics=len(topics_pairwise_distance),
            npmi_score=1.0, # ignore for now
            total_pairwise_distance=total_pairwise_distance,
            topics_pairwise_distance=topics_pairwise_distance,
            topic_diversity=topic_diversity,
            mean_intertopic_cos_similarity=mean_cos_similarity,
            redundant_pairs=redundant_pairs,
            noise_ratio=noise_ratio,
            prob_distributions=probability_data_by_topic
        )
        return validation_metrics

    # get data for reproducibility testing: doc_id, doc_topics, valid_topics, topic_vectors, topic_words
    def get_stability_data(self):
        # get doc ids and doc topic membership from lance
        doc_ids = self.manager.retrieve_column_list(SENTENCE_TBL_NAME, condition='is_validated = true', columns=['uuid_'])
        doc_topics = self.manager.retrieve_column_list(SENTENCE_TBL_NAME, condition='is_validated = true', columns=['topic'])

        # get topic info
        topic_info = self.model.get_topic_info()
        valid_topics = [int(t) for t in topic_info['Topic'] if t != -1] # get topics (excluding outlier)
        
        # get vector of topic
        topic_vectors = [
            self.model.topic_embeddings_[t].tolist()
            for t in valid_topics
            if  t in self.model.topic_embeddings_
        ]

        # get topic words
        topic_words = {str(t): [word for word, _ in self.model.get_topic(t)[:10]] for t in valid_topics}
        return doc_ids, doc_topics, valid_topics, topic_vectors, json.dumps(topic_words)

    # gets visualizations using functions from Visualizer
    def get_visualizations(self):
        # get topic map
        print('getting topic map')
        topic_map = self.visualizer.visualize_topic_map(model=self.model)

        # get document map
        if self.trial_config.visualize_documents == True:
            print('getting doc_map')
            doc_map = self.visualizer.visualize_document_map(model=self.model, manager=self.manager)
        else: 
            doc_map = None

        # get heatmap
        print('getting heat map')
        heatmap = self.visualizer.visualize_topic_heatmap(model=self.model)

        # get topic hierarchy
        print('getting hierarchy map')
        hierarchy = self.visualizer.visualize_topic_hierarchy(model=self.model)

        return topic_map, doc_map, heatmap, hierarchy

    # validation metrics methods
    def get_pairwise_embedding_distance(self):
        topic_info = self.model.get_topics()
        topics = [
            [
                word for word, _ in topic_info[topic]
            ] for topic in topic_info if topic != -1
        ]

        all_topic_scores = [] # pair-wise embedding avg for each topic
        for topic_words in topics: 
            topic_embeddings = self.model.embedding_model.embedding_model.encode(topic_words, device='mps')
            similarity_matrix = cosine_similarity(topic_embeddings)
            upper_triangle_indices = np.triu_indices_from(similarity_matrix, k=1)
            pairwise_scores = similarity_matrix[upper_triangle_indices]

            if len(pairwise_scores) > 0:
                all_topic_scores.append(np.mean(pairwise_scores)) 

        all_topic_avg = float(np.mean(all_topic_scores)) if all_topic_scores else 0.0
        return all_topic_avg, all_topic_scores

    def get_topic_diversity(self, top_n: int = 10):
        # get valid topics (no outlier)
        raw_topics = self.model.get_topics()
        valid_topics = [
            [word for word, _ in word_weight_list[:top_n]]
            for topic_id, word_weight_list in raw_topics.items()
            if topic_id != -1
        ]
        if not valid_topics: return 0.0

        # get all words
        all_topic_words = []
        for topic in valid_topics:
            for word in topic:
                all_topic_words.append(word)

        # get all unique words
        unique_topic_words = set(all_topic_words)           

        # compute topic diversity score -> return
        return float(len(unique_topic_words) / len(all_topic_words))

    def get_intertopic_cosine_similarity(self, REDUNDANT_PAIR_THRESHOLD=0.8):
        # get topic ids
        topic_ids = self.model.get_topics().keys()
        valid_topic_ids = [tid for tid in topic_ids if tid != -1] # filter outliers out
        if len(valid_topic_ids) < 2:
            # not enough topics
            return None # need to null check later

        # get topic embeddings
        topic_embeddings = self.model.topic_embeddings_ # still has outlier, we need to get rid of
        id_to_index = {tid: idx for idx, tid in enumerate(topic_ids)} 
        valid_indices = [id_to_index[tid] for tid in valid_topic_ids]
        valid_topic_embeddings = topic_embeddings[valid_indices] # filter out outlier topic -1

        # get similarity matrix, extract upper triangle to get pairwise comparisons
        similarity_matrix = cosine_similarity(valid_topic_embeddings)
        upper_triangle_indices = np.triu_indices_from(similarity_matrix, k=1)
        pairwise_similarity = similarity_matrix[upper_triangle_indices]

        # avg pairwise comparisons -> return value
        mean_similarity = float(np.mean(pairwise_similarity))
        max_similarity = float(np.max(pairwise_similarity))

        #TODO get redundant scores
        redundant_pairs = []
        for i in range(len(valid_topic_ids)):
            for j in range(i + 1, len(valid_topic_ids)):
                score = similarity_matrix[i, j]
                if score > REDUNDANT_PAIR_THRESHOLD:
                    redundant_pair = {
                        'topic1': valid_topic_ids[i],
                        'topic2': valid_topic_ids[j],
                        'score': float(score)
                    }
                    redundant_pairs.append(redundant_pair)


        return mean_similarity, max_similarity, redundant_pairs 

    def get_probability_data(self):
        model_info = self.model.get_topic_info()

        # seperate outliers from topics
        outliers_info = model_info[model_info['Topic'] == -1]
        topics_info = model_info[model_info['Topic'] != -1]
        topics_info.sort_values(by='Topic') # should put into right order.
        topics = topics_info['Topic'].tolist()
        topics_count = topics_info['Count'].tolist()

        # get noise ratio
        noise_ratio = self.compute_noise_ratio(outliers_info, topics_info)

        # avg prob per topic
        # prob distribution by topic
        topic_prob_data: list[dict] = self.compute_probability_per_topic(topics=topics)

        return noise_ratio, topic_prob_data

    def compute_noise_ratio(self, outlier_info, topics_info) -> float:
        topics_count = topics_info['Count'].to_list()
        topics_doc_num = sum(topics_count)

        # Safeguard against empty outlier DataFrame
        if outlier_info.empty:
            outlier_doc_num = 0
        else:
            outlier_doc_num = outlier_info['Count'].iloc[0]

        nr = outlier_doc_num / topics_doc_num
        return nr

    def compute_probability_per_topic(self, topics: list[int]):
        topics_data: list[dict] = []
        for topic_num in topics:
            topic_max_prob = []
            for batch in self.get_probs_by_topic(topic_num=topic_num):
                # batch shape: (batch_size, n_topics) -> one max per document
                topic_max_prob.extend(np.max(batch, axis=1).tolist())

            if len(topic_max_prob) > 0:
                avg_prob = sum(topic_max_prob) / len(topic_max_prob)
            else:
                print(f'Error for topic num: {topic_num}')
                continue

            # topics organized by index.
            topics_data.append({
                'avg_prob': avg_prob,
                'prob_dist': topic_max_prob
            })

        return topics_data

     # generator 

    def get_probs_by_topic(self, topic_num: int, BATCH_SIZE: int = FILE_IO_BATCH_SIZE):
        for batch in self.manager.batch_generator(tbl_name=SENTENCE_TBL_NAME, condition=f'topic = {topic_num}', columns=['probabilities'], BATCH_SIZE=BATCH_SIZE):
            yield batch['probabilities'].tolist()

    # model stability metrics
    #   top level function
    #   returns ARI, AMI, 
    @classmethod
    def get_model_stability_metrics(cls, loader: Loader, batch_name: str):
        # get data
        records = loader.connect(MODEL_OUTPUT_TBL_NAME).search().where(f'trial_config.batch_name = "{batch_name}"').to_pandas().to_dict(orient="records")
        num_samples = len(records)

        # get list of lists of all data
        all_doc_topics = [r["doc_topics"] for r in records]
        all_doc_ids = [r["doc_ids"] for r in records]
        all_valid_topics = [r["valid_topics"] for r in records]
        all_topic_vectors = [r["topic_vectors"] for r in records]
        all_topic_words = [r["topic_words"] for r in records]

        # get adjusted rand index
        print('get ari')
        ari_score = cls.compute_ari_multi(list_of_doc_topics=all_doc_topics, list_of_doc_ids=all_doc_ids)

        # get adjusted mutual info
        print('get ami')
        ami_score = cls.compute_ami_multi(list_of_doc_topics=all_doc_topics, list_of_doc_ids=all_doc_ids)

        # get outlier jaccard score
        print('get jaccard')
        outlier_jaccard_score = cls.compute_outlier_jaccard_multi(list_of_doc_topics=all_doc_topics, list_of_doc_ids=all_doc_ids)

        # get hungarian alignment score
        print('get hungarian')
        # hungarian_alignment_score = cls.compute_hungarian_alignment_multi(list_of_topic_vectors=all_topic_vectors)

        # get matched topic rbo
        print('get rbo')
        # rbo_score = cls.compute_matched_topic_rbo_multi(list_of_words=all_topic_words, list_of_valid_topics=all_valid_topics, list_of_topic_vectors=all_topic_vectors)

        # get topic num stability
        print('get count stability')
        topic_num_stability = cls.compute_topic_count_stability_multi(list_of_valid_topics=all_valid_topics)

        stability_data = {
            'num_samples': num_samples,
            'Adjusted Rand Index':ari_score,
            'Adjusted Mutual Information': ami_score,
            'Jaccard Score': outlier_jaccard_score,
           #'Hungarian Alignment': hungarian_alignment_score,
        #   'Matched RBO': rbo_score,
            'Number of Topics Stability': topic_num_stability
        }
        return stability_data

    @classmethod
    def _to_1d_array(cls, data, dtype=None) -> np.ndarray:
        """Safely converts input lists/arrays (including LanceDB/Pandas object wrappers) into a flat 1D array."""

        # 1. Handle top-level string representation of lists
        if isinstance(data, (str, np.str_)):
            try:
                data = json.loads(data)
            except Exception:
                data = ast.literal_eval(data)

        arr = np.asarray(data)
        
        arr = np.asarray(data)
        # Unpack 0D object scalar wrapper if present (e.g. from Pandas df.to_dict())
        if arr.ndim == 0:
            arr = np.asarray(arr.item())
        arr = arr.ravel()
        if dtype is not None:
            arr = arr.astype(dtype)
        return arr

    @classmethod
    def _to_2d_float_array(cls, data) -> np.ndarray:
        """
        Safely parses stringified 2D topic vectors (e.g. '[[...]]' or '[]')
        into a proper float32 2D NumPy array.
        """
        if isinstance(data, (str, np.str_)):
            try:
                data = json.loads(data)
            except Exception:
                data = ast.literal_eval(data)

        arr = np.asarray(data)

        # Unpack 0D object wrappers (e.g. from Pandas Series)
        if arr.ndim == 0:
            item = arr.item()
            if isinstance(item, (str, np.str_)):
                try:
                    item = json.loads(item)
                except Exception:
                    item = ast.literal_eval(item)
                arr = np.asarray(item)
            else:
                arr = np.asarray(item)

        if arr.size == 0 or len(arr) == 0:
            return np.empty((0, 0), dtype=np.float32)

        return arr.astype(np.float32)

    # def get Adjusted Rand Index
    # AI GENERATED
    @classmethod
    def _align_multi_doc_topics(
        cls,
        list_of_doc_topics: List[List[int]],
        list_of_doc_ids: Optional[List[List[str]]] = None
    ) -> list[np.ndarray]:
        """
        Ultra-fast document topic alignment across N models.
        Pre-aligns all models ONCE using vectorized NumPy operations.
        """
        if list_of_doc_ids is None or len(list_of_doc_ids) == 0:
            return [np.array(t, dtype=np.int32) for t in list_of_doc_topics]

        # Convert all inputs to robust 1D arrays upfront
        ids_1d = [cls._to_1d_array(ids) for ids in list_of_doc_ids]
        topics_1d = [cls._to_1d_array(t, dtype=np.int32) for t in list_of_doc_topics]

        n_models = len(list_of_doc_topics)
        ref_ids = list_of_doc_ids[0]

        # 1. Fast Path: All doc_ids are already identical in order
        if all(np.array_equal(ids, ref_ids) for ids in ids_1d[1:]):
            return topics_1d

        # 2. Fast Path: All models contain the same set of UUIDs (NumPy argsort)
        ref_len = len(ref_ids)
        same_lengths = all(len(ids) == ref_len for ids in ids_1d[1:])
        
        if same_lengths:
            aligned_topics = []
            for arr_topics, arr_ids in zip(topics_1d, ids_1d):
                sort_order = np.argsort(arr_ids)
                aligned_topics.append(arr_topics[sort_order])
                
            return aligned_topics

        # 3. Fallback: Overlapping/Drifted Subsets (Dict Lookup)
        common_ids = set(ref_ids)
        for ids in ids_1d[1:]:
            common_ids.intersection_update(ids)

        canonical_ids = list(common_ids)
        aligned_topics = []

        for arr_topics, arr_ids in zip(topics_1d, ids_1d):
            mapping = dict(zip(arr_ids, arr_topics))
            aligned_topics.append(
                np.array([mapping[uid] for uid in canonical_ids], dtype=np.int32)
            )

        return aligned_topics

    # AI GENERATED
    @classmethod
    def _format_metric_result(cls, matrix: np.ndarray) -> Dict[str, Any]:
        """Extracts summary statistics and upper triangle pair values from an N x N matrix."""
        n_models = matrix.shape[0]
        triu_indices = np.triu_indices(n_models, k=1)
        pair_values = matrix[triu_indices]

        mean = float(np.mean(pair_values)) if pair_values.size > 0 else None
        std = float(np.std(pair_values)) if pair_values.size > 0 else None
        min_ = float(np.min(pair_values)) if pair_values.size > 0 else None
        max_ = float(np.max(pair_values)) if pair_values.size > 0 else None

        return {
            "mean": mean,
            "std": std,
            "min": min_,
            "max": max_,
            "pairwise_matrix": matrix
        }

    @classmethod
    def compute_ari_multi(
        cls,
        list_of_doc_topics: List[List[int]],
        list_of_doc_ids: Optional[List[List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Computes Adjusted Rand Index (ARI) across N model runs.
        """
        aligned_topics = cls._align_multi_doc_topics(list_of_doc_topics, list_of_doc_ids)
        n_models = len(aligned_topics)
        matrix = np.ones((n_models, n_models))
        pbar = tqdm(total=math.comb(len(range(n_models)), 2), desc='COMPUTE ARI')

        for i, j in itertools.combinations(range(n_models), 2):
            score = adjusted_rand_score(aligned_topics[i], aligned_topics[j])
            matrix[i, j] = matrix[j, i] = score
            pbar.update(1)

        pbar.close()

        return cls._format_metric_result(matrix)

    @classmethod
    def compute_ami_multi(
        cls,
        list_of_doc_topics: List[List[int]],
        list_of_doc_ids: Optional[List[List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Computes Adjusted Mutual Information (AMI) across N model runs.
        """
        aligned_topics = cls._align_multi_doc_topics(list_of_doc_topics, list_of_doc_ids)
        n_models = len(aligned_topics)
        matrix = np.ones((n_models, n_models))
        pbar = tqdm(total=math.comb(len(range(n_models)), 2), desc='COMPUTE AMI')

        for i, j in itertools.combinations(range(n_models), 2):
            score = adjusted_mutual_info_score(aligned_topics[i], aligned_topics[j])
            matrix[i, j] = matrix[j, i] = score
            pbar.update(1)

        pbar.close()

        return cls._format_metric_result(matrix)

    @classmethod
    def compute_outlier_jaccard_multi(
        cls,
        list_of_doc_topics: List[List[int]],
        list_of_doc_ids: Optional[List[List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Computes Outlier (-1 topic) Jaccard Similarity across N model runs.
        """
        aligned_topics = cls._align_multi_doc_topics(list_of_doc_topics, list_of_doc_ids)
        n_models = len(aligned_topics)
        matrix = np.ones((n_models, n_models))

        pbar = tqdm(total=math.comb(len(range(n_models)), 2), desc='COMPUTE JACCARD')

        for i, j in itertools.combinations(range(n_models), 2):
            outliers_i = set(np.where(aligned_topics[i] == -1)[0])
            outliers_j = set(np.where(aligned_topics[j] == -1)[0])

            union = len(outliers_i | outliers_j)
            score = 1.0 if union == 0 else len(outliers_i & outliers_j) / union
            matrix[i, j] = matrix[j, i] = score
            pbar.update(1)

        pbar.close()

        return cls._format_metric_result(matrix)

    @classmethod
    def compute_hungarian_alignment_multi(
        cls,
        list_of_topic_vectors: List[List[List[float]]]
    ) -> Dict[str, Any]:
        """
        Computes Hungarian Bipartite Alignment across N model topic vector spaces.
        """
        n_models = len(list_of_topic_vectors)
        if n_models < 2:
            raise ValueError("At least 2 model runs are required.")

        matrix = np.ones((n_models, n_models))

        # Parse all vector matrices safely upfront
        parsed_vectors = [cls._to_2d_float_array(vecs) for vecs in list_of_topic_vectors]

        pbar = tqdm(total=math.comb(len(range(n_models)), 2), desc='COMPUTE HUNGARIAN')
        
        for i, j in itertools.combinations(range(n_models), 2):
            vecs_i = parsed_vectors[i]
            vecs_j = parsed_vectors[j]

            if len(vecs_i) == 0 or len(vecs_j) == 0:
                matrix[i, j] = matrix[j, i] = 0.0
                continue

            sim_matrix = cosine_similarity(vecs_i, vecs_j)
            row_ind, col_ind = linear_sum_assignment(-sim_matrix)
            score = np.mean(sim_matrix[row_ind, col_ind])
            matrix[i, j] = matrix[j, i] = float(score)
            pbar.update(1)

        pbar.close()

        return cls._format_metric_result(matrix)

    @classmethod
    def compute_rbo(cls, list_a: List[str], list_b: List[str], p: float = 0.9) -> float:
        """Helper for single pair Rank-Biased Overlap."""
        if not list_a or not list_b:
            return 0.0

        k = min(len(list_a), len(list_b))
        set_a, set_b = set(), set()
        rbo_score = 0.0
        for d in range(1, k + 1):
            set_a.add(list_a[d - 1])
            set_b.add(list_b[d - 1])
            agreement = len(set_a & set_b) / d
            rbo_score += (p ** (d - 1)) * agreement


        return (1 - p) * rbo_score
    
    @classmethod
    def compute_matched_topic_rbo_multi(
        cls,
        list_of_words: List[Dict[str, List[str]]],
        list_of_valid_topics: List[List[int]],
        list_of_topic_vectors: List[List[List[float]]],
        p: float = 0.9
    ) -> Dict[str, Any]:
        """
        Pairs topics across N models via Hungarian alignment, then computes mean RBO.
        """
        n_models = len(list_of_words)
        if n_models < 2:
            raise ValueError("At least 2 model runs are required.")

        matrix = np.ones((n_models, n_models))

        pbar = tqdm(total=math.comb(len(range(n_models)), 2), desc='COMPUTE RBO')

        for i, j in itertools.combinations(range(n_models), 2):
            vecs_i = np.array(list_of_topic_vectors[i])
            vecs_j = np.array(list_of_topic_vectors[j])

            if len(vecs_i) == 0 or len(vecs_j) == 0:
                matrix[i, j] = matrix[j, i] = 0.0
                continue

            # Pair topics via vectors
            sim_matrix = cosine_similarity(vecs_i, vecs_j)
            row_ind, col_ind = linear_sum_assignment(-sim_matrix)

            rbo_scores = []
            for idx_i, idx_j in zip(row_ind, col_ind):
                t_id_i = str(list_of_valid_topics[i][idx_i])
                t_id_j = str(list_of_valid_topics[j][idx_j])

                words_i = list_of_words[i].get(t_id_i, [])
                words_j = list_of_words[j].get(t_id_j, [])

                rbo_scores.append(cls.compute_rbo(words_i, words_j, p=p))

            matrix[i, j] = matrix[j, i] = float(np.mean(rbo_scores))
            pbar.update(1)

        pbar.close()

        return cls._format_metric_result(matrix)

    @classmethod
    def compute_topic_count_stability_multi(
        cls,
        list_of_valid_topics: List[List[int]]
    ) -> Dict[str, float]:
        """
        Computes global topic count metrics across N model runs.
        """
        counts = np.array([len(topics) for topics in list_of_valid_topics])
        mean_k = float(np.mean(counts))
        std_k = float(np.std(counts))

        return {
            "mean_topics": mean_k,
            "std_topics": std_k,
            "min_topics": int(np.min(counts)),
            "max_topics": int(np.max(counts)),
            "relative_std": float(std_k / mean_k) if mean_k > 0 else 0.0
        }