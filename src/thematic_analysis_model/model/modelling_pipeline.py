from lancedb import Table
from pathlib import Path
from lancedb.permutation import permutation_builder
from lancedb.permutation import Permutation
from torch.utils.data import DataLoader
from bertopic import BERTopic
from tqdm import tqdm


# main modelling class
class TopicModeller():
    def __init__(self):
        ...
    
    # run pipeline
    @classmethod
    def run_pipeline(cls, table: Table, save_model_path: Path, topic_model: BERTopic | None = None, load_model_path: Path | None = None, BATCH_SIZE: int = 50000, SAVE_INTERVAL: int = 10):
        # shuffle and get batches
        batch_generator = cls.shuffle_into_batch_generator(table, BATCH_SIZE=BATCH_SIZE)

        # check if you have to load model
        new_model: bool = False
        if load_model_path:
            topic_model = BERTopic.load(load_model_path)
        elif not topic_model:
            print('Failed to load model, or you failed to pass model')
            return
        else:
            new_model = True # signals that this is a completely fresh model

        # process batches
        count: int = 0
        total = table.count_rows(filter="is_modelled = false")
        pbar = tqdm(total=total, desc='MODELLING', unit='batch')

        for batch in batch_generator:
            # if firt batch, need to .fit()
            if new_model is True:
                topic_model = cls.model_first_batch(batch, topic_model)
                new_model = False # set to false for next time
            else:
                topic_model = cls.model_batch(table, batch, topic_model)

            count += 1
            pbar.update(BATCH_SIZE)

            if count % SAVE_INTERVAL == 0:
                topic_model.save(save_model_path, serialization='safetensors', save_embedding_model='all-MiniLM-L6-v2', save_ctfidf=True)


        # final save
        topic_model.save(save_model_path, serialization='safetensors', save_embedding_model='all-MiniLM-L6-v2', save_ctfidf=True)


    # get shuffled batches
    @classmethod
    def shuffle_into_batch_generator(cls, table: Table, BATCH_SIZE: int):
        # get permutation table
        permutation_tbl = (
            permutation_builder(table)
            .filter("is_modelled = false")
            .shuffle()
            .execute()
        )

        # get permutation
        permutation = (
            Permutation.from_tables(table, permutation_table=permutation_tbl)
            .select_columns(['sentence_hash', 'sentence', 'vector'])
            .with_format('arrow')
        )
        
        # get torch data loader
        loader = DataLoader(
            permutation,
            batch_size=BATCH_SIZE,
            collate_fn=lambda x: x
        )

        return loader
        
        ...


    @classmethod
    def model_first_batch(cls, table, batch, topic_model: BERTopic):
        # get docs, get embeddings
        ids = batch['sentence_hash'].to_pylist()
        docs = batch['sentence'].to_pylist()
        embeddings = batch['vector'].to_pylist()

        # update model
        topic_model.fit(docs, embeddings=embeddings)

        # update flags
        cls.update_flags(table, ids)

        return topic_model

    # model batch
    @classmethod
    def model_batch(cls, table, batch, topic_model: BERTopic):
        # get docs, get embeddings
        ids = batch['sentence_hash'].to_pylist()
        docs = batch['sentence'].to_pylist()
        embeddings = batch['vector'].to_pylist()

        # update model
        topic_model.partial_fit(docs, embeddings)

        # update flags
        cls.update_flags(table, ids)

        return topic_model
        ...

    @classmethod
    def update_flags(cls, table: Table, ids):
        upsert_dict = [
            {
                'sentence_hash': my_id,
                'is_modelled': True
            } for my_id in ids
        ]

        (
            table.merge_insert(on='sentence_hash')
            .when_matched_update_all()
            .execute(upsert_dict)
        )
