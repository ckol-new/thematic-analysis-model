from lancedb import Table
from tqdm import tqdm
import asyncio
import xxhash
import uuid
from asyncio import Queue
from sentence_transformers import SentenceTransformer
from .dclasses import SchemaContent, SchemaSentence

# embedding pipeline
class EmbeddingPipeline:
    def __init__(self):
        pass

    @classmethod
    def run_pipeline(cls, tbl: Table, stbl: Table, model: SentenceTransformer, PROCESS_BATCH_SIZE: int = 5000,  EMBED_BATCH_SIZE: int = 1000):
        # process/split text (async + sync)
        cls.run_processing_pipeline(tbl, stbl, PROCESS_BATCH_SIZE)

        # generate embeddings (sync)
        cls.run_embedding_pipeline(stbl, model, EMBED_BATCH_SIZE)
        ...

    @classmethod
    def run_processing_pipeline(cls, tbl: Table, stbl: Table, BATCH_SIZE: int = 5000):
        count = 0
        total = tbl.count_rows(filter='is_split = false')
        pbar = tqdm(total=total, desc='PROCESSING POSTS', unit='posts')
        while True:
            content_list: list[SchemaContent]= tbl.search().where('is_split = false').limit(BATCH_SIZE).to_pydantic(SchemaContent)

            pbar.update(len(content_list)) # update progress bar

            # check if finished
            if len(content_list) == 0:
                print("FINISHED PROCESSING TEXT")
                break

            # update flags
            uuids = [i.uuid for i in content_list]
            upsert_dict = [{'uuid': my_uuid, 'is_split': True} for my_uuid in uuids]
            (
                tbl.merge_insert(on='uuid')
                .when_matched_update_all()
                .execute(upsert_dict)
            )

            # split each sentence
            split_sentences: list[SchemaSentence] = []
            for content in content_list:
                split_result: list[SchemaSentence] = cls.process_content(content)
                split_sentences.extend(split_result)

            # save w/o duplicates
            (
                stbl.merge_insert(on='sentence_hash')
                .when_not_matched_insert_all()
                .execute(split_sentences)
            )           


    @classmethod
    def run_embedding_pipeline(cls, stbl: Table, model: SentenceTransformer, READ_CHUNK_SIZE: int = 50000, EMBED_BATCH_SIZE: int = 4096):
        total = stbl.count_rows(filter="is_embedded = false")
        pbar = tqdm(total=total, desc='EMBEDDING', unit='sentence')
        while True:
            # get sentence batch
            batch_df = stbl.search().where('is_embedded = false').limit(READ_CHUNK_SIZE).select(['sentence', 'sentence_uuid']).to_pandas()

            # check to break loop
            if batch_df.empty:
                print('FINISHED EMBEDDING')
                break

            docs = batch_df['sentence'].to_list()
            uuids = batch_df['sentence_uuid'].to_list()
            del batch_df

            for i in range(0, len(docs), EMBED_BATCH_SIZE):
                # embed batch
                embeddings = model.encode(docs[i:i+EMBED_BATCH_SIZE])

                # save to db
                payload = [{'sentence_uuid': s_uuid, 'vector': vec, 'is_embedded': True} for s_uuid, vec in zip(uuids[i:i+EMBED_BATCH_SIZE], embeddings)]
                (
                    stbl.merge_insert(on='sentence_uuid')
                    .when_matched_update_all()
                    .execute(payload)
                )

                pbar.update(len(embeddings))
                






            

    @classmethod
    def process_content(cls, content: SchemaContent) -> list[SchemaSentence]:
        # split text
        split_text: list[str] = cls.split_text(content.content)
        if not split_text:
            return []

        # generate list of SchemaSentence
        sentences: list[SchemaSentence] = []
        for sentence in split_text:
            if len(sentence) < 3:
                continue

            s_hash = str(xxhash.xxh64(sentence).hexdigest())
            s_uuid = str(uuid.uuid4())
            
            s_sentence: SchemaSentence = SchemaSentence(
                url=content.url,
                url_hash=content.url_hash,
                content_uuid=content.uuid,
                sentence=sentence,
                sentence_hash=s_hash,
                sentence_uuid=s_uuid,
                date=content.date,
                vector=None,
                is_embedded=False,
                is_modelled=False
            )

            sentences.append(s_sentence)

        if len(sentences) == 0:
            return []

        return sentences
        ...


    @classmethod
    def split_text(cls, text: str) -> list[str]:
        # split content into sentences
        split_txt = text.split(sep='. ')
        split_txt = [sentence.rstrip() for sentence in split_txt]
        return split_txt


        