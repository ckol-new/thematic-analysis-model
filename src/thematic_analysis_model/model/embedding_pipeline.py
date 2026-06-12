from lancedb import Table
import asyncio
from asyncio import Queue
from sentence_transformers import SentenceTransformer

# embedding pipeline
class EmbeddingPipeline:
    def __init__(self):
        pass

    @classmethod
    async def run_pipeline(cls, tbl: Table, stbl: Table, model: SentenceTransformer, READ_BATCH_SIZE: int = 5000, WRITE_BATCH_SIZE: int = 4000, EMBED_BATCH_SIZE: int = 1000):
        # process/split text (async + sync)

        # generate embeddings (sync)

        ...

    @classmethod
    async def run_processing_pipeline(cls, tbl: Table, stbl: Table, READ_BATCH_SIZE: int = 5000, WRITE_BATCH_SIZE: int = 4000):
        # init queues
        read_queue: Queue = Queue()
        write_queue: Queue = Queue() 

        # task group
        # async reads

        # sync writes
        ...

    @classmethod
    def run_embedding_pipeline(cls, stbl: Table, model: SentenceTransformer, EMBED_BATCH_SIZE: int = 1000):
        # generate batches

        # paginate process each batch
        ...

    @classmethod
    async def reader(cls, worker_id: int, tbl: Table, read_queue: Queue, write_queue: Queue):
        print(f"Initializing reader {worker_id}")

        # main while loop
            # check write queue size, pause if necessary

            # split sentence

            # add to write queue
        
    @classmethod
    async def writer(cls, worker_id: int, stbl: Table, write_queue: Queue):
        print(f"Initializing writer {worker_id}")

        # main while loop
            # add to batch

            # if end of write_queue -> write
            # if batchsize met -> write
                # deduplicate within batch (in memory)

                # merge-insert to prevent duplicates between batches

                # clear old lists

    @classmethod
    def split_text(cls, text: str) -> list[str]:
        # split content into sentences
        ...

    @classmethod
    def embed_text(cls, text: str, model: SentenceTransformer):
        ...