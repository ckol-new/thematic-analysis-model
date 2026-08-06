from .data_management import Loader, Manager
from .dataclasses import TrialConfig, ValidationMetric, ModelOutput, validation_metric_adapter
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
from scipy.spatial.distance import cdist
from sklearn.metrics import adjusted_rand_score, adjusted_mutual_info_score
from sklearn.metrics.pairwise import cosine_similarity
from statsmodels.stats.inter_rater import fleiss_kappa, aggregate_raters

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

        # reassign topic centroids for topic vectors
        self.update_topic_embeddings_in_batches()

        # Quick sanity check
        has_nan = np.isnan(self.model.topic_embeddings_).any()
        has_zero_rows = (np.linalg.norm(self.model.topic_embeddings_, axis=1) == 0).any()

        print(f"Topic Embeddings Shape: {self.model.topic_embeddings_.shape}")
        print(f"Contains NaNs? {has_nan}")
        print(f"Contains Zero Vectors? {has_zero_rows}")

        # get data for reproducibility testing
        doc_ids, doc_topics, valid_topics, topic_vectors, topic_words = self.get_stability_data()
        doc_to_topics = {
            di: dt for di, dt in zip(doc_ids, doc_topics, strict=True)
        }

        # generate visualizations/figures
        topic_map, doc_map, heatmap, hierarchy_map = self.get_visualizations()
        topic_map = topic_map.to_json(engine='orjson')
        doc_map = doc_map.to_json(engine='orjson') if doc_map else None
        heatmap = heatmap.to_json(engine='orjson')
        hierarchy_map = hierarchy_map.to_json(engine='orjson')

        # save model output
        if not self.trial_config: 
            return validation_metric, topic_map, doc_map, heatmap, hierarchy_map
        else:
            model_output = ModelOutput(
                trial_config=self.trial_config,
                validation_metrics=validation_metric.model_dump_json(),
                doc_ids=json.dumps(doc_ids),
                doc_topics=json.dumps(doc_topics),
                doc_to_topics=json.dumps(doc_to_topics),
                valid_topics=json.dumps(valid_topics),
                topic_vectors=json.dumps(topic_vectors),
                topic_words=json.dumps(topic_words),
                topic_map=topic_map,
                document_map=doc_map,
                heatmap=heatmap,
                hierarchy_map=hierarchy_map
            )
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

    def update_topic_embeddings_in_batches(self):
        print('updating topics')
        """
        Calculates topic centroids incrementally across database batches
        without loading all embeddings into memory at once.
        """
        topic_info = self.model.get_topic_info()
        # Unique topic IDs (including outlier -1 if present)
        unique_topics = topic_info['Topic'].tolist()

        topic_sums = {}
        topic_counts = {}
        embedding_dim = None

        # Process documents in batches from Lance DB
        for batch in self.manager.batch_generator(
            tbl_name=SENTENCE_TBL_NAME,
            condition='is_validated = true',
            columns=['topic', 'embedding'],
            BATCH_SIZE=FILE_IO_BATCH_SIZE
        ):
            topics = np.array(batch['topic'].tolist())
            embeddings = np.array(batch['embedding'].tolist())

            if len(embeddings) == 0:
                continue

            if embedding_dim is None:
                embedding_dim = embeddings.shape[1]

            # Accumulate sums and counts per topic
            for topic_id in np.unique(topics):
                mask = (topics == topic_id)
                sum_emb = embeddings[mask].sum(axis=0)
                count = mask.sum()

                if topic_id not in topic_sums:
                    topic_sums[topic_id] = np.zeros(embedding_dim)
                    topic_counts[topic_id] = 0

                topic_sums[topic_id] += sum_emb
                topic_counts[topic_id] += count

        # Compute centroid mean vector for each topic
        topic_vectors = []
        for t in sorted(unique_topics):
            if t in topic_sums and topic_counts[t] > 0:
                centroid = topic_sums[t] / topic_counts[t]
            else:
                centroid = np.zeros(embedding_dim or 384)
            topic_vectors.append(centroid)
        print(topic_vectors)
        # Directly assign to the BERTopic model attribute
        self.model.topic_embeddings_ = np.array(topic_vectors)

    # get data for reproducibility testing: doc_id, doc_topics, valid_topics, topic_vectors, topic_words
    def get_stability_data(self):
        # get doc ids and doc topic membership from lance
        doc_ids = self.manager.retrieve_column_list(SENTENCE_TBL_NAME, condition='is_validated = true', columns=['uuid_'])
        doc_topics = self.manager.retrieve_column_list(SENTENCE_TBL_NAME, condition='is_validated = true', columns=['topic'])

        # get topic info
        topic_info = self.model.get_topic_info()
        unique_topics = sorted(topic_info['Topic'].tolist())

        # 1. Create a map of Topic ID -> Row index in topic_embeddings_
        topic_to_row_idx = {
            topic_id: row_idx 
            for row_idx, topic_id in enumerate(unique_topics)
        }

        valid_topics = [int(t) for t in unique_topics if t != -1] # get topics (excluding outlier)

        # get vector of topic
        topic_vectors = []
        if hasattr(self.model, "topic_embeddings_") and self.model.topic_embeddings_ is not None:
            for t in valid_topics:
                if t in topic_to_row_idx:
                    row_idx = topic_to_row_idx[t]
                    topic_vectors.append(self.model.topic_embeddings_[row_idx].tolist())

        # get topic words
        topic_words = {str(t): [word for word, _ in self.model.get_topic(t)[:10]] for t in valid_topics}
        return doc_ids, doc_topics, valid_topics, topic_vectors, topic_words

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

class StabilityEvaluator:
    def __init__(self, loader: Loader, manager: Manager):
        self.loader = loader
        self.manager = manager

    # main entry
    def evaluate(self, batch_name: str) -> dict:
        # load model output
        outputs = self.load_batch(batch_name=batch_name)

        # align documents
        aligned_doc_ids = self._get_aligned_uuids(outputs=outputs)

        M = len(outputs)
        n = len(aligned_doc_ids)

        # get topic assignment matrix (M, N): M= number of model outpust, N= number of common aligned documents
        assignment_matrix = np.zeros((M, n))
        for i, output in enumerate(outputs):
            doc_to_topics = json.loads(output.doc_to_topics)
            assignment_matrix[i] = [doc_to_topics[uid] for uid in aligned_doc_ids] # get topics in order of aligned ids

        # get macro metrics
        avg_topic_count, std_topic_count = self.compute_topic_count_stability(outputs=outputs)

        # get Pairwise Document Partition Metrics (How documents are split independent of topic)
        outlier_stability_dict = self.compute_outlier_stability(data=assignment_matrix)

        #   get ari + ami
        partition_stability_dict = self.compute_partition_stability(assignment_matrix=assignment_matrix, include_outliers=False)

        # get topic representation alignment
        bipartite_representation_stability_dict = self.compute_bipartite_representation_metrics(
            runs=outputs,
        )




        d = {
            'avg_topic_count': avg_topic_count,
            'std_topic_count': std_topic_count,
            'outlier_stability_data': outlier_stability_dict,
            'partition_stability_data': partition_stability_dict,
            'bipartite_representation_stability_dict': bipartite_representation_stability_dict
        }

        return d
        ...

    # load batch of models
    def load_batch(self, batch_name: str) -> list[ModelOutput]:
        return self.loader.connect(MODEL_OUTPUT_TBL_NAME).search().where(f'trial_config.batch_name = "{batch_name}"').to_pydantic(model=ModelOutput)

    def _get_aligned_uuids(self, outputs: list[ModelOutput]) -> list[str]:
        """Intersect UUID lists across all runs to ensure exact row alignment."""
        common = set(json.loads(outputs[0].doc_ids))
        for run in outputs[1:]:
            common.intersection_update(json.loads(run.doc_ids))
        return sorted(list(common))

    # compute outlier stability -> avg, std
    def compute_topic_count_stability(self, outputs: list[ModelOutput]) -> tuple:
        # get avg
        vals = np.array(
            [validation_metric_adapter.validate_json(model_output.validation_metrics).num_topics for model_output in outputs]
        )
        avg = float(np.average(vals))

        # get std
        std = float(np.std(vals))

        return avg, std

    # outlier stability results
    def compute_outlier_stability(self, data: np.ndarray):
        # get ratings (0 if not outlier, 1 if outlire)
        ratings = (data == -1).astype(int).T

        # get category count matrix
        count, _ = aggregate_raters(ratings)

        # get kappa value (degree of aggreement in outlier assignment)
        kappa = float(fleiss_kappa(count))

        is_outlier = ratings.T
        run_outlier_rates = np.mean(is_outlier, axis=1)

        return {
            'outlier_fleiss_kappa': kappa,
            'mean_outlier_rates': float(np.mean(run_outlier_rates)),
            'std_outlier_rates': float(np.std(run_outlier_rates)),
        }

    def compute_partition_stability(
        self, assignment_matrix: np.ndarray, include_outliers: bool = True
    ) -> dict[str, float]:
        """Calculates aggregate ARI and AMI across all M*(M-1)/2 run pairs.

        Args:
            assignment_matrix: 2D array of shape (M_runs, N_docs) where rows are
            runs and columns are aligned document assignments.
            include_outliers: If True, treats topic -1 (outliers) as a distinct
            cluster label. If False, masks out documents marked as -1 in either
            run being compared.

        Returns:
            dict containing mean and standard deviation for both ARI and AMI.
        """
        M, N = assignment_matrix.shape
        if M < 2:
            raise ValueError("Requires at least M >= 2 runs to evaluate partition stability.")

        ari_scores = []
        ami_scores = []

        # Generate all unique non-redundant pairs: M*(M-1)/2 combinations
        for i, j in itertools.combinations(range(M), 2):
            run_a = assignment_matrix[i]
            run_b = assignment_matrix[j]

            # Optional: Filter out outliers (-1) to test core-cluster stability only
            if not include_outliers:
                valid_mask = (run_a != -1) & (run_b != -1)
                run_a = run_a[valid_mask]
                run_b = run_b[valid_mask]

                if len(run_a) == 0:
                    continue  # Safeguard if all documents were outliers

            # 1. Adjusted Rand Index
            ari = adjusted_rand_score(run_a, run_b)

            # 2. Adjusted Mutual Information (arithmetic normalization is standard)
            ami = adjusted_mutual_info_score(run_a, run_b, average_method="arithmetic")

            ari_scores.append(ari)
            ami_scores.append(ami)

        return {
            "mean_ari": float(np.mean(ari_scores)),
            "std_ari": float(np.std(ari_scores)),
            "mean_ami": float(np.mean(ami_scores)),
            "std_ami": float(np.std(ami_scores)),
        }

    def compute_bipartite_representation_metrics(
    self, runs: list, rbo_p: float = 0.9
) -> dict[str, float]:
        """Calculates pairwise topic vector cosine similarity, keyword RBO,

        and Hungarian global match score across all M runs.

        Args:
            runs: List of RunArtifact objects containing topic_embeddings,
            topic_words, and topic_id_map.
            rbo_p: Persistence parameter for Rank-Biased Overlap (default: 0.9).

        Returns:
            dict containing aggregate mean scores across all run pairs.
        """
        M = len(runs)
        if M < 2:
            raise ValueError(
                "Bipartite matching requires at least M >= 2 runs."
            )

        matched_cosines = []
        global_hungarians = []
        matched_rbos = []

        for i, j in itertools.combinations(range(M), 2):
            run_a, run_b = runs[i], runs[j]

            # Step 1: Extract embeddings and IDs excluding outlier topic -1
            vecs_a, ids_a = self._extract_valid_embeddings(run_a)
            vecs_b, ids_b = self._extract_valid_embeddings(run_b)

            K_a, K_b = len(ids_a), len(ids_b)
            if K_a == 0 or K_b == 0:
                continue  # Safeguard for edge cases where a run produces no valid topics

            # Step 2: Construct Cost Matrix (Cosine Distance between topic vectors)
            # Shape: (K_a, K_b)
            cost_matrix = cdist(vecs_a, vecs_b, metric="cosine")

            # Step 3: Hungarian Bipartite Match (Optimal 1-to-1 pairings)
            # Returns row_ind and col_ind of length min(K_a, K_b)
            row_ind, col_ind = linear_sum_assignment(cost_matrix)

            # Step 4: Extract Cosine Similarity for matched pairs (1.0 - distance)
            matched_distances = cost_matrix[row_ind, col_ind]
            matched_sims = 1.0 - matched_distances
            total_matched_sim = np.sum(matched_sims)

            # Matched Quality (Cosine Sim): Normalized by min(K_a, K_b)
            # Measures pure semantic closeness of counterpart topics
            matched_quality = total_matched_sim / min(K_a, K_b)
            matched_cosines.append(matched_quality)

            # Hungarian Match Score (Global Alignment): Normalized by max(K_a, K_b)
            # Penalizes system score if one model created extra orphan topics
            global_score = total_matched_sim / max(K_a, K_b)
            global_hungarians.append(global_score)

            # Step 5: Calculate Keyword RBO for the Hungarian-paired topic word lists
            rbo_pair_scores = []
            topic_words_a = json.loads(run_a.topic_words)
            topic_words_b = json.loads(run_b.topic_words)
            for r, c in zip(row_ind, col_ind):
                topic_id_a = str(ids_a[r])
                topic_id_b = str(ids_b[c])

                words_a = topic_words_a.get(topic_id_a, [])
                words_b = topic_words_b.get(topic_id_b, [])

                rbo_pair_scores.append(self.compute_rbo(words_a, words_b, p=rbo_p))

            matched_rbos.append(np.mean(rbo_pair_scores))

        return {
            "topic_vector_cosine_sim": float(np.mean(matched_cosines)),
            "topic_rbo_sim": float(np.mean(matched_rbos)),
            "hungarian_match_score": float(np.mean(global_hungarians)),
        }

    def compute_rbo(
    self, list1: list[str], list2: list[str], p: float = 0.9
) -> float:
        """Calculates Rank-Biased Overlap (RBO) for two ranked keyword lists.

        Args:
            list1: Top words for Topic A ordered by c-TF-IDF weight.
            list2: Top words for Topic B ordered by c-TF-IDF weight.
            p: Persistence parameter in (0, 1). Higher values weigh lower-ranked words
            more. p=0.9 heavily weights top 5 words while evaluating top 20.

        Returns:
            RBO score bounded in [0.0, 1.0].
        """
        if not list1 or not list2:
            return 0.0

        k = min(len(list1), len(list2))
        set1, set2 = set(), set()
        sum_agreement = 0.0

        # Sum weighted overlap at increasing evaluation depths d=1..k
        for d in range(1, k + 1):
            set1.add(list1[d - 1])
            set2.add(list2[d - 1])

            # Agreement at depth d: proportion of shared words
            overlap = len(set1.intersection(set2))
            agreement = overlap / d

            # Weight by p^(d-1)
            sum_agreement += (p ** (d - 1)) * agreement

        # Extrapolation term for finite lists
        rbo_score = (1.0 - p) * sum_agreement + (p**k) * (
            len(set(list1[:k]).intersection(set(list2[:k]))) / k
        )

        return float(np.clip(rbo_score, 0.0, 1.0))

    def _extract_valid_embeddings(self, run: ModelOutput) -> tuple[np.ndarray, list[int]]:
        """Filters out topic -1 (outliers) from the embedding matrix."""
        vecs = np.array(json.loads(run.topic_vectors))
        t_ids = json.loads(run.valid_topics)
        return vecs, t_ids