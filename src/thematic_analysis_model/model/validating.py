from .data_management import Loader, Manager
from .dataclasses import TrialConfig, ValidationMetric, ModelOutput
from .config import SENTENCE_TBL_NAME, VALIDATING_BATCH_SIZE, FILE_IO_BATCH_SIZE
from thematic_analysis_model.view.visualizing import Visualizer

from bertopic import BERTopic
from tqdm import tqdm
import hdbscan
from sklearn.metrics.pairwise import cosine_similarity
import gc
import numpy as np

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

        # generate visualizations/figures
        topic_map, doc_map, heatmap, hierarchy_map = self.get_visualizations()

        # save model output
        if not self.trial_config: 
            return validation_metric, topic_map, doc_map, heatmap, hierarchy_map
        else:
            model_output = ModelOutput(
                name=self.trial_config.trial_name,
                batch_name=self.trial_config.batch_name,
                trial_config=self.trial_config,
                validation_metrics=validation_metric,
                topic_map=topic_map.to_json(),
                document_map=doc_map.to_json(),
                heatmap=heatmap.to_json(),
                hierarchy_map=hierarchy_map.to_json()
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
                    'reduced_embedding': red_embedding,
                    'topic': topic,
                    'probabilities': prob,
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

    # gets visualizations using functions from Visualizer
    def get_visualizations(self):
        # get topic map
        topic_map = self.visualizer.visualize_topic_map(model=self.model)

        # get document map
        doc_map = self.visualizer.visualize_document_map(model=self.model, manager=self.manager)

        # get heatmap
        heatmap = self.visualizer.visualize_topic_heatmap(model=self.model)

        # get topic hierarchy
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

