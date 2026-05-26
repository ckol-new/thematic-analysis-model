from lancedb import Table
from uuid import uuid4


class EmbeddingPipeline:
    def __init__(self):
       ...

    @classmethod
    def process_sentences(cls, scrape_table: Table, sentence_table: Table, BATCH_SIZE=5000):
        uuid_to_process = scrape_table.search().where('is_split = false').select(['uuid']).to_pandas()['uuid'].to_list()
        total = len(uuid_to_process)

        # paginate through ids, to get batches
        # process each batch
        for i in range(0, total, BATCH_SIZE):
            print(f'splitting {i} of {BATCH_SIZE} content objects')
            uuid_batch = uuid_to_process[i:i+BATCH_SIZE]
            quoted_uuids = ", ".join(f"'{uuid}'" for uuid in uuid_batch)
            df = scrape_table.search().where(f'uuid IN ({quoted_uuids})').select(['uuid', 'content', 'url', 'origin', 'content_type']).to_pandas()
            # iterate through df

            data_dict: list[dict] = []
            for index, series in df.iterrows():
                sentences: list[str] = series['content'].split('\n')
                # iterate through sentences
                for sentence in sentences:
                    data_dict.append(
                        {
                            'uuid': str(uuid4()),
                            'sentence': str(sentence.strip()),
                            'vector': None,
                            'url': series['url'],
                            'content_uuid': series['uuid'],
                            'is_modelled': False,
                            'origin': series['origin'],
                            'content_type': series['content_type']
                        }
                    )
            # update database
            sentence_table.add(data_dict)
            del data_dict
            
            # update is_split
            upsert_dict = [
                {
                    'uuid': my_uuid,
                    'is_split': True
                } for my_uuid in uuid_batch
            ]
            (
                scrape_table.merge_insert(on='uuid')
                .when_matched_update_all()
                .execute(upsert_dict)
            )