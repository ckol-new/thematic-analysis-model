from lancedb import Table
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
    def run_pipeline(cls, tbl: Table, stbl: Table, model: SentenceTransformer, READ_BATCH_SIZE: int = 5000, WRITE_BATCH_SIZE: int = 4000, EMBED_BATCH_SIZE: int = 1000):
        # process/split text (async + sync)

        # generate embeddings (sync)
        ...

    @classmethod
    def run_processing_pipeline(cls, tbl: Table, stbl: Table, BATCH_SIZE: int = 5000):
        count = 0
        while True:
            count += 1 
            print(f'processing batch {count}') 
            content_list: list[SchemaContent ]= tbl.search().where('is_split = false').limit(BATCH_SIZE).to_pydantic(SchemaContent)
            print(len(content_list))

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
            print('updated flags')

            # split each sentence
            split_sentences: list[SchemaSentence] = []
            for content in content_list:
                split_result: list[SchemaSentence] = cls.process_content(content)
                split_sentences.extend(split_result)
            print('split sentences')

            # save w/o duplicates
            (
                stbl.merge_insert(on='sentence_hash')
                .when_not_matched_insert_all()
                .execute(split_sentences)
            )           
            print('saved')


    @classmethod
    def run_embedding_pipeline(cls, stbl: Table, model: SentenceTransformer, EMBED_BATCH_SIZE: int = 1000):
        ...

            

    @classmethod
    def process_content(cls, content: SchemaContent) -> list[SchemaSentence]:
        print('process content')
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

        print(len(sentences))

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


    @classmethod
    def embed_text(cls, text: str, model: SentenceTransformer):
        ...