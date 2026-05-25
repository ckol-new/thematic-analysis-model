from lancedb import Table
from .dclasses import Content
from uuid import uuid4


class EmbeddingPipeline:
    def __init__(self):
       ...

    @classmethod
    def process_sentences(cls, scrape_table: Table, sentence_table: Table, BATCH_SIZE=5000):
        # get metadata of relevant uuids
        metadata_to_split = scrape_table.search().where('is_split = false').select(['metadata']).to_list()
        total = len(metadata_to_split)

        for i in range(0, total, BATCH_SIZE):
            # get batch
            batch_metadata = metadata_to_split[i:i+BATCH_SIZE]
            # update is_split
            upsert_data = [
                {
                    'metadata': metadata,
                    'is_split': True
                } for metadata in batch_metadata
            ]
            (
                scrape_table.merge_insert(on='')
            )

            # get batch df
            batch_df = scrape_table.search().where(f'metadata.uuid IN ({','.join(map(lambda x: str(x['uuid']), batch_metadata))})').select(['content', 'metadata']).to_pandas()

            # iterate through batch df
