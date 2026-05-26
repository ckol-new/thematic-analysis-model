from bertopic import BERTopic
from pathlib import Path
from lancedb import Table
import safetensors 
import numpy as np

class TopicModeller:
    def __init__(self, embedding_model, vectorizer_model, umap_model, hdbscan_model):
        self.embedding_model = embedding_model
        self.vectorizer_model = vectorizer_model
        self.umap_model = umap_model
        self.hdbscan_model = hdbscan_model 

        self.merged_model: BERTopic = None

    def run_model(self, table: Table, BATCH_SIZE: int = 200000):
        # get batches, only if not already modelled
        batches = table.search().where('is_modelled = false').select(['uuid', 'sentence', 'vector']).to_batches(batch_size=BATCH_SIZE)
        submodels: list[BERTopic] = []

        # batch process
        for batch in batches:
            # model batch, add to submodels
            df = batch.to_pandas()
            ids = df['uuid'].to_list()
            docs = df['sentence'].to_list()
            embeddings = np.vstack(df['vector'].to_list())

            submodel = BERTopic(
                embedding_model=self.embedding_model,
                vectorizer_model=self.vectorizer_model,
                umap_model=self.umap_model,
                hdbscan_model=self.hdbscan_model,
                verbose=True
            )
            submodel.fit_transform(docs, embeddings)
            submodels.append(submodel)

            # update all is_modelled flag in db
            upsert_dict = [
                {
                    'uuid': my_uuid,
                    'is_modelled': True
                } for my_uuid in ids
            ]
            (
                table.merge_insert(on='uuid')
                .when_matched_update_all()
                .execute(upsert_dict)
            )

        # tournament merge models together
        merged_model = self.tournament_merge_models(submodels)
        del submodels

    # merge models, return merged model
    def tournament_merge_models(self, submodels: list[BERTopic]) -> BERTopic:
        if not submodels:
            raise ValueError('submodels cannot be empty')
        
        round_num = 1
        current_models = list(submodels)

        while len(current_models) > 1:
            next_round_models = []

            # step through current models in pairs of two, 
            for i in range(0, len(current_models), 2):
                if i + 1 < len(current_models):
                    model1 = current_models[i]
                    model2 = current_models[i+1]

                    merged = BERTopic.merge_models([model1, model2])
                    next_round_models.append(merged)

                else:
                    next_round_models.append(current_models[i])

            current_models = next_round_models
            rount_num += 1
        
        return current_models[0]

    # save_model: safe tensors
    def save_merged_model(self, spath: Path):
        self.merged_model.save(path=spath, serialization='safetensors')

    @classmethod
    def load_merged_model(self, spath=Path) -> BERTopic:
        return BERTopic.load(spath, 'all-MiniLM-L6-v2')
