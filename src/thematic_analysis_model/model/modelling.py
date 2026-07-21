# all classes around modelling
import pandas as pd
import lancedb
from pathlib import Path
import numpy as np
import copy
from tqdm import tqdm
import gc

from .manage_data import CorpusManager
from .dclasses import TrialConfig, ValidationMetrics, validation_metrics_adapter, SchemaTrialOutput, trial_output_adapter
from .util import shuffle_ids, batch_generator, get_ids_by_condition
from ..config import MODELLING_BATCH_SIZE_DEFAULT, EMBEDDING_MODEL_NAME, FILE_IO_BATCH_SIZE_DEFUALT

from sentence_transformers import SentenceTransformer
from bertopic import BERTopic 
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import adjusted_rand_score
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer

import itertools
from typing import Any, List, Union, Dict
import json
from datetime import datetime, date
import uuid


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
    def __init__(self, tbl: lancedb.Table, tbl_output: lancedb.Table, topic_model: BERTopic, embedding_model: SentenceTransformer,  trial_config: TrialConfig):
        self.tbl = tbl
        self.tbl_output = tbl_output
        self.topic_model = topic_model
        self.topic_model.calculate_probabilities = True
        self.embedding_model = embedding_model
        self.trial_config = trial_config

    # validate
    def validate(self, BATCH_SIZE: int = MODELLING_BATCH_SIZE_DEFAULT):
        # get relevant ids in model
        query = 'is_modelled = true'
        ids = get_ids_by_condition(tbl=self.tbl, query=query)

        # recover data
        self.transform_model(ids, BATCH_SIZE=BATCH_SIZE)

        # get validation metrics
        validation_metric = self.get_validation_metrics()
        
        # get figures

        # Determine the number of valid topics (excluding outliers)
        topic_ids = self.topic_model.get_topics().keys()
        valid_topics = [tid for tid in topic_ids if tid != -1]
        num_valid_topics = len(valid_topics)

        print('***** VISUALIZING TOPICS *****')
        # 1. Visualize Topics (requires at least 1 valid topic)
        if num_valid_topics >= 1:
            print('visualize topics')
            try:
                fig1 = self.topic_model.visualize_topics()
            except Exception as e:
                print(f"Could not generate topic map: {e}")
                fig1 = None
        else:
            print("Skipping topic map (no valid topics found).")

        # 2. Heatmap & Hierarchy (require at least 2 valid topics)
        if num_valid_topics >= 2:
            print('visualize heat map')
            try:
                fig2 = self.topic_model.visualize_heatmap()
            except Exception as e:
                print(f"Could not generate topic heatmap: {e}")
                fig2 = None

            print('visualize hierarchy')
            try:
                fig4 = self.topic_model.visualize_hierarchy()
            except Exception as e:
                print(f"Could not generate topic hierarchy: {e}")
                fig4 = None
        else:
            print("Skipping heatmap and hierarchy plots (requires at least 2 valid topics).")

        ''' 
        # 3. Visualize Documents (works even with 0 valid topics, showing outliers)
        print('visualize documents')
        try:
            fig3 = self.visualize_documents()
        except Exception as e:
            print(f"Could not generate document map: {e}")
            fig3 = None
        '''

        # save to lance
        trial_output = SchemaTrialOutput(
            trial_config=self.trial_config,
            validation_metrics=str(validation_metrics_adapter.dump_json(validation_metric)),
            all_topic_prob_histogram=None,
            list_topic_prob_histogram=None,
            topic_map=str(fig1.to_json),
            topic_heatmap=str(fig2.to_json()),
            topic_hierarchy=str(fig4.to_json),
            document_map=None,
            date=str(date.today()),
            uuid=str(uuid.uuid4())
        )
        self.tbl_output.add([trial_output])




    # recover probabilities + topics
    def transform_model(self, ids: list[int], BATCH_SIZE: int = MODELLING_BATCH_SIZE_DEFAULT):
        # for batch in ids
        pbar = tqdm(total=len(ids), desc='TRANSFORMING DATA', unit='sentence')
        for batch in batch_generator(ids=ids, tbl=self.tbl, columns=['uuid', 'vector', 'sentence'], BATCH_SIZE=BATCH_SIZE):
            # transform batch
            uuids = batch['uuid'].tolist()
            embeddings = np.array(batch['vector'].tolist())
            documents = batch['sentence'].tolist()

            # note topics as int, for each doc + probs as 2D numpy array: ROW = doc index, COL= topic index
            topics, probs = self.topic_model.transform(documents=documents, embeddings=embeddings)

            # update database
            self.save_probability_topic_data(uuids=uuids, topics=topics, probs=probs)

            pbar.update(len(uuids))
        pbar.close()

    # save function
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

    # load function
    #   AI Generated, need to change later.
    @classmethod
    def compile_validation_metrics(
        cls,
        target_path: Union[str, Path, List[Union[str, Path]]],
        output_file: Union[str, Path] = None
    ) -> pd.DataFrame:
        """
        Recursively finds, loads, and flattens 'validation_metric_serialized.json' 
        files into a single flat Pandas DataFrame for Excel/CSV analysis.
        
        Args:
            target_path: A directory to scan recursively, a specific JSON file, 
                        or a list of file paths.
            output_file: Optional path to save the resulting table (.csv or .xlsx).
            
        Returns:
            pd.DataFrame: Flat table with one row per trial configuration.
        """
        json_files = []

        # 1. Gather all target JSON files
        if isinstance(target_path, list):
            json_files = [Path(p) for p in target_path]
        else:
            path = Path(target_path)
            if path.is_dir():
                # Recursively search for your serialized metric files
                json_files = list(path.rglob("validation_metric_serialized.json"))
                # Fallback to any JSON if the specific name isn't found
                if not json_files:
                    json_files = list(path.rglob("*.json"))
            else:
                json_files = [path]

        flat_rows = []

        # 2. Parse and flatten each metric file
        for file_path in json_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data: Dict[str, Any] = json.load(f)
                
                # Basic validation check to ensure it matches your schema
                if "trial_config" not in data:
                    continue
                    
                config = data["trial_config"]
                
                # Build flat dictionary row
                row = {
                    # Trial Identifiers
                    "trial_num": config.get("trial_num"),
                    "trial_desc": config.get("trial_desc"),
                    "embedding_model": config.get("embedding_model"),
                    
                    # Hyperparameters (Fine-tuning variables)
                    "umap_seed": config.get("umap_seed"),
                    "n_neighbours": config.get("n_neighbours"),
                    "n_components": config.get("n_components"),
                    "min_cluster_size": config.get("min_cluster_size"),
                    "min_samples": config.get("min_samples"),
                    "min_dist": config.get("min_dist"),
                    
                    # Evaluation Metrics
                    "num_topics": data.get("num_topics"),
                    "total_pairwise_embedding_distance": data.get("total_pairwise_embedding_distance"),
                    "mean_intertopic_cosine_similarity": data.get("mean_intertopic_cosine_similarity"),
                    "topic_diversity": data.get("topic_diversity"),
                    "noise_ratio": data.get("noise_ratio"),
                    "run_to_run_ARI": data.get("run_to_run_ARI"),
                    "bootstrap_ARI": data.get("bootstrap_ARI"),
                    
                    # Aggregated Complex Metrics
                    "num_redundant_pairs": len(data.get("redundant_pairs", [])),
                }
                
                # Compute average representative probability across all valid topics
                prob_data = data.get("topic_prob_data", [])
                if prob_data:
                    avg_probs = [t["avg_prob"] for t in prob_data if "avg_prob" in t]
                    row["mean_topic_probability"] = float(np.mean(avg_probs)) if avg_probs else None
                else:
                    row["mean_topic_probability"] = None
                    
                # Compute spread of intra-topic coherence
                pairwise_distances = data.get("topic_pairwise_embedding_distance", [])
                if pairwise_distances:
                    row["min_topic_coherence"] = float(np.min(pairwise_distances))
                    row["max_topic_coherence"] = float(np.max(pairwise_distances))
                    row["std_topic_coherence"] = float(np.std(pairwise_distances))
                else:
                    row["min_topic_coherence"] = None
                    row["max_topic_coherence"] = None
                    row["std_topic_coherence"] = None

                flat_rows.append(row)

            except Exception as e:
                print(f"Skipping file {file_path} due to error: {e}")

        if not flat_rows:
            print("No valid trial validation metrics were found.")
            return pd.DataFrame()

        # 3. Create DataFrame and sort by trial number
        df = pd.DataFrame(flat_rows)
        df = df.sort_values(by="trial_num").reset_index(drop=True)

        # 4. Save file if destination path is provided
        if output_file:
            output_path = Path(output_file)
            # Ensure target directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if output_path.suffix.lower() == ".xlsx":
                # Writes directly to Excel (requires 'openpyxl' installed)
                df.to_excel(output_path, index=False, sheet_name="Validation Summary")
                print(f"Successfully exported {len(df)} trials to Excel: {output_path}")
            else:
                # Writes to standard CSV
                df.to_csv(output_path, index=False)
                print(f"Successfully exported {len(df)} trials to CSV: {output_path}")

        return df

    # return validation metrics
    def get_validation_metrics(self) -> ValidationMetrics:
        # get NPMI

        num_topics: int = len(self.topic_model.get_topic_info()) - 1

        # get pairwise embedding distance
        all_topic_pairwise_distance, pairwise_distance_by_topic = self.get_pairwise_embedding_distance()
        print(f'topic pairwise embedding distance {all_topic_pairwise_distance}')

        # get intertopic cosine similarity
        mean_similarity, max_similarity, redundant_pairs = self.get_intertopic_cosine_similarity()
        print(f'mean similairty: {mean_similarity}')
        print(f'redundant pairs {len(redundant_pairs)}')

        # get topic diversity
        topic_diversity = self.get_topic_diversity()
        print(f'topic diversity: {topic_diversity}')

        # get probability data
        noise_ratio, topic_prob_data = self.get_probability_data()
        print(f'noise ratio: {noise_ratio}')

        # get ARI
        print('***** STABILITY METRICS *****')
        run_to_run_ARI, bootstrap_ARI = self.compute_stability_metrics()
        print(f'run to run stability: {run_to_run_ARI}')
        print(f'bootstrap stability: {bootstrap_ARI}')

        # get bootstrap resampling stability
        validation_metrics = ValidationMetrics(
            trial_config=self.trial_config,
            num_topics=num_topics,
            total_pairwise_embedding_distance=all_topic_pairwise_distance,
            mean_intertopic_cosine_similarity=mean_similarity,
            topic_diversity=topic_diversity,
            noise_ratio=noise_ratio,
            topic_pairwise_embedding_distance=pairwise_distance_by_topic,
            topic_prob_data=topic_prob_data,
            redundant_pairs=redundant_pairs,
            run_to_run_ARI=run_to_run_ARI,
            bootstrap_ARI=bootstrap_ARI
        )
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

    def get_intertopic_cosine_similarity(self, REDUNDANT_PAIR_THRESHOLD=0.8):
        # get topic ids
        topic_ids = self.topic_model.get_topics().keys()
        valid_topic_ids = [tid for tid in topic_ids if tid != -1] # filter outliers out
        if len(valid_topic_ids) < 2:
            # not enough topics
            return None # need to null check later

        # get topic embeddings
        topic_embeddings = self.topic_model.topic_embeddings_ # still has outlier, we need to get rid of
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
    

    def get_topic_diversity(self, top_n: int = 10):
        # get valid topics (no outlier)
        raw_topics = self.topic_model.get_topics()
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

    # return noise ratio, avg prob per topic, and prob distirbution per topic
    def get_probability_data(self):
        model_info = self.topic_model.get_topic_info()

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

            topics_data.append({
                'avg_prob': avg_prob,
                'prob_dist': topic_max_prob
            })

        return topics_data

    # generator 
    def get_probs_by_topic(self, topic_num: int, BATCH_SIZE: int = FILE_IO_BATCH_SIZE_DEFUALT):
        # query ids
        ids = self.tbl.search().where(f'topic = {topic_num}').with_row_id(True).select(['_rowid']).to_arrow()['_rowid'].to_pylist()
        total = len(ids)

        # take ids in batches -> return in batches
        for i in range(0, total, BATCH_SIZE):
            batch_ids = ids[i:i+BATCH_SIZE]
            yield np.array(self.tbl.take_row_ids(batch_ids).select(['probabilities']).to_arrow()['probabilities'].to_pylist())


    # generator
    def get_lines_by_topic(self, topic_num: int, BATCH_SIZE: int = FILE_IO_BATCH_SIZE_DEFUALT):
        # query ids
        ids = self.tbl.search().where(f'topic = {topic_num}').with_row_id(True).select(['_rowid']).to_arrow()['_rowid'].to_pylist()
        total = len(ids)

        # take ids in batches -> return generator of batch
        for i in range(0, total, BATCH_SIZE):
            batch_ids = ids[i:i+BATCH_SIZE]
            yield self.tbl.take_row_ids(batch_ids).to_pandas()

    # reproducibility testing
    # AI Generated, might need to be fixed later.
    def compute_stability_metrics(self, n_bootstrap: int = 5, n_runs: int = 5, max_samples: int = 2000) -> tuple[float, float]:
        """
        Computes Run-to-Run (UMAP Seed) ARI and Bootstrap Resampling ARI 
        without altering the main model or modifying the database.
        """
        # 1. Retrieve already modelled embeddings and their corresponding topics from LanceDB
        ids = get_ids_by_condition(tbl=self.tbl, query='is_modelled = true')
        shuffled_ids = shuffle_ids(ids)[0:max_samples]
        sample_df = pd.concat([df for df in batch_generator(ids=shuffled_ids, tbl=self.tbl, columns=['vector', 'topic'])], ignore_index=True)

        if sample_df.empty or len(sample_df) < 10:
            return 0.0, 0.0

        embeddings = np.vstack(sample_df['vector'].values)
        original_labels = sample_df['topic'].values
        n_docs = len(embeddings)

        # ==========================================
        # 1. RUN-TO-RUN ARI (Stochastic UMAP Seed Stability)
        # ==========================================
        # We run the pipeline on the exact same data using different UMAP seeds 
        # and compute the pairwise ARI to measure projection stochasticity.
        run_labels = []
        for i in range(n_runs):
            seed = 100 + i
            labels = self._fast_cluster(embeddings, seed=seed)
            run_labels.append(labels)
            
        ari_scores = []
        for i in range(len(run_labels)):
            for j in range(i + 1, len(run_labels)):
                ari_scores.append(adjusted_rand_score(run_labels[i], run_labels[j]))
        mean_run_to_run_ari = float(np.mean(ari_scores)) if ari_scores else 1.0

        # ==========================================
        # 2. BOOTSTRAP RESAMPLING ARI (Data Subset Stability)
        # ==========================================
        # We sample with replacement, cluster, and compare results on those 
        # sampled indices to the main model's original predictions.
        bootstrap_ari_scores = []
        for b in range(n_bootstrap):
            # Generate bootstrap indices
            boot_indices = np.random.choice(n_docs, size=n_docs, replace=True)
            boot_embeddings = embeddings[boot_indices]
            boot_original_labels = original_labels[boot_indices]

            # Fit-predict on bootstrapped embeddings with a static UMAP seed
            boot_labels = self._fast_cluster(boot_embeddings, seed=42)

            # Measure how stable the original assignments are compared to the resampled run
            score = adjusted_rand_score(boot_original_labels, boot_labels)
            bootstrap_ari_scores.append(score)

        mean_bootstrap_ari = float(np.mean(bootstrap_ari_scores)) if bootstrap_ari_scores else 1.0

        return mean_run_to_run_ari, mean_bootstrap_ari

    def _fast_cluster(self, embeddings: np.ndarray, seed: int) -> np.ndarray:
        """Helper to instantiate and run a clone of the trial's UMAP/HDBSCAN pipeline."""
        # Initialize fast, multi-threaded UMAP
        umap_model = UMAP(
            n_neighbors=self.trial_config.n_neighbours,
            n_components=self.trial_config.n_components,
            random_state=seed,
            n_jobs=-1  # Uses all CPU cores
        )
        # Initialize HDBSCAN
        hdbscan_model = HDBSCAN(
            min_cluster_size=self.trial_config.min_cluster_size,
            min_samples=self.trial_config.min_samples,
            prediction_data=False,
            core_dist_n_jobs=-1  # Uses all CPU cores
        )
        
        # Pipeline execution
        reduced_embeddings = umap_model.fit_transform(embeddings)
        labels = hdbscan_model.fit_predict(reduced_embeddings)
        return labels

    #TODO OPTIMIZE THIS....
    def visualize_documents(self):
        df = self.tbl.search().where('is_validated = true').select(['sentence', 'vector', 'topic']).to_pandas()
        docs = df['sentence'].tolist()
        embeddings = np.vstack(df["vector"].values)
        topics = df['topic'].tolist()

        fig = self.topic_model.visualize_documents(docs=docs, embeddings=embeddings, hide_annotations=True, hide_document_hover=True)
        return fig

# class for visualizing and generated plots
#   Validator will own a visualizer
class Visualizer:
    def __init__(self, tbl: lancedb.Table, topic_model: BERTopic):
        self.tbl = tbl
        self.topic_model = topic_model

    # get trial of relevance
    def get_trial(self, trial_name: str) -> SchemaTrialOutput:
        ...

    # visualize topic probability as histogram in total
    def topic_histogram_total(self):
        return

    # visualize topic probability as histogram by each topic
    def topic_histogram(self):

        return

    # generate line diagram
    def parameter_line_diagram(self):
        return

    # get avg + SD
    def average_and_SD(self):
        return 




class Trial:
    def __init__(self, trial_config: TrialConfig, tbl: lancedb.Table, tbl_output: lancedb.Table, corpus_manager: CorpusManager, model_save_path: Path):
        self.trial_config = trial_config
        self.tbl = tbl
        self.tbl_output = tbl_output
        self.corpus_manager = corpus_manager
        self.model_save_path = model_save_path

    def run_trial(self):
        # load models
        self.load_models()

        # model 
        self.corpus_manager.reset_modelling_bool_flags()
        modeller = Modeller(
            tbl=self.tbl,
            topic_model=self.topic_model
        )
        merged_model = modeller.model()
        Modeller.save_model(model=merged_model, path=self.model_save_path)
    
        # have to reload model, to force BERTopic to realize the HDBSCAN tree is gone, otherwise it assumes it is still there, even if it isn't due to .merge_models()
        # REALLY IMPORTANT FOR IT TO WORK.
        merged_model = Modeller.load_model(self.model_save_path)

        # validate
        validator = Validator(
            tbl=self.tbl,
            tbl_output=self.tbl_output,
            topic_model=merged_model,
            embedding_model=self.embedding_model,
            trial_config=self.trial_config
        )
        validation_metric = validator.validate()
        
        # save validation metric

    def load_models(self):
        self.embedding_model = SentenceTransformer(self.trial_config.embedding_model)
        self.umap_model = UMAP(
            n_neighbors=self.trial_config.n_neighbours,
            n_components=self.trial_config.n_components,
            min_dist=self.trial_config.min_dist,
            random_state=self.trial_config.umap_seed
        )
        self.hdbscan_model = HDBSCAN(
            min_cluster_size=self.trial_config.min_cluster_size,
            min_samples=self.trial_config.min_samples,
            prediction_data=False
        )
        self.vectorizer_model = CountVectorizer(stop_words='english')
        self.topic_model = BERTopic(
            embedding_model=self.embedding_model,
            umap_model=self.umap_model,
            hdbscan_model=self.hdbscan_model,
            vectorizer_model=self.vectorizer_model,
            calculate_probabilities=False # for now, change during validation
        )

class TrialQueue:
    def __init__(self, tbl: lancedb.Table, tbl_output: lancedb.Table, configs: list[TrialConfig], corpus_manager: CorpusManager):
        self.configs = configs
        self.tbl = tbl
        self.tbl_output = tbl_output
        self.corpus_manager = corpus_manager

    # run queue
    def run_queue(self):
        count = 0
        for config in self.configs:
            count += 1
            print(f"RUNNING TRIAL: {count} / {len(self.configs)}")

            # get model and validation metric save paths
            model_save_path: Path = Path(config.model_save_path)

            # run trial
            trial = Trial(
                trial_config=config,
                tbl=self.tbl,
                tbl_output=self.tbl_output,
                corpus_manager=self.corpus_manager,
                model_save_path=model_save_path,
            )
            trial.run_trial()

            # clean db
            print('***** CLEANING LANCE *****')
            self.corpus_manager.clean_lancedb()
        
    # AI Generated, may need to be fixed.
    # generates every combination of trial configs for each trial config parameter (not including trial num, trial desc, or save path)
    @classmethod
    def generate_trial_configs(cls, **kwargs: Union[Any, List[Any]]) -> List[TrialConfig]:
        """
        Generates a list of TrialConfig Pydantic objects by sweeping over 
        any parameters passed as lists. Automatically populates trial_num, 
        trial_desc, and interpolates save paths.
        """
        # 1. Separate swept fields (passed as lists) from static fields
        swept_fields = []
        param_grids = {}
        
        for key, value in kwargs.items():
            # If the parameter is a list, we sweep it (excluding strings which are iterables but not lists)
            if isinstance(value, list) and not isinstance(value, str):
                swept_fields.append(key)
                param_grids[key] = value
            else:
                param_grids[key] = [value]  # Normalize static values to a list of length 1

        # 2. Generate the Cartesian product of all parameters
        keys = list(param_grids.keys())
        value_lists = [param_grids[k] for k in keys]
        
        trial_configs = []
        
        for trial_idx, combo in enumerate(itertools.product(*value_lists), start=1):
            combo_dict = dict(zip(keys, combo))
            
            # 3. Auto-generate the trial description based on SWEPT fields only
            desc_parts = []
            for field in swept_fields:
                desc_parts.append(f"{field}_{combo_dict[field]}")
            
            if desc_parts:
                trial_desc = f"trial_{trial_idx}_" + "_".join(desc_parts)
            else:
                trial_desc = f"trial_{trial_idx}_static"
                
            # 4. Handle dynamic path interpolation (so trials don't overwrite each other)
            # We allow the user to pass templates like: "models/my_model_{trial_num}.pkl"
            for path_field in ["model_save_path", "validation_metric_save_path"]:
                path_val = combo_dict.get(path_field)
                if isinstance(path_val, str):
                    combo_dict[path_field] = path_val.format(
                        trial_num=trial_idx, 
                        trial_desc=trial_desc
                    )
            
            # 5. Assemble the complete configuration dictionary
            config_payload = {
                "trial_num": trial_idx,
                "trial_desc": trial_desc,
                **combo_dict
            }
            
            # Instantiate the actual Pydantic model (this runs your Pydantic validation)
            trial_configs.append(TrialConfig(**config_payload))
            
        return trial_configs
        