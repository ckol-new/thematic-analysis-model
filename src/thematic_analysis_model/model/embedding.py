import lancedb
from ..config import FILE_IO_BATCH_SIZE_DEFUALT, EMBEDDING_BATCH_SIZE_DEFUALT
from .util import shuffle_ids, get_ids_by_condition, batch_generator
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

# all classes around embedding 

class Embedder:
    def __init__(self, tbl: lancedb.Table, embed_model = SentenceTransformer):
        self.tbl = tbl
        self.embed_model = embed_model
        self.count: int = 0 # number of lines embedded
    
    # main point of entry for embedder -> runs embedding pipeline
    def embed(self, READ_BATCH_SIZE: int = FILE_IO_BATCH_SIZE_DEFUALT, EMBED_BATCH_SIZE: int = EMBEDDING_BATCH_SIZE_DEFUALT, EMBED_LIMIT: int | None = None):
        # get ids of lines to embed (limit if necessary)
        query: str = 'is_embedded = false'
        if not EMBED_LIMIT:
            ids = get_ids_by_condition(tbl=self.tbl, query=query)
        else:
            ids = get_ids_by_condition(tbl=self.tbl, query=query)[0:EMBED_LIMIT]

        pbar = tqdm(total=len(ids), desc='EMBEDDING', unit='SENTENCE')


        # for each batch -> embed batch + update bools
        #   note that batch sizes should be larger then embedding sizes, that way less read operations are required.
        for batch_df in batch_generator(ids=ids, tbl=self.tbl, columns=['sentence', 'uuid'], BATCH_SIZE=READ_BATCH_SIZE):
            docs: list[str] = batch_df['sentence'].tolist()
            uuids: list[str] = batch_df['uuid'].tolist()

            # paginate by embed batch size
            for i in range(0, len(uuids), EMBED_BATCH_SIZE):
                current_docs = docs[i:i+EMBED_BATCH_SIZE]
                current_uuids = uuids[i:i+EMBED_BATCH_SIZE]

                # embed batch + save + update bools
                self.embed_batch(docs=current_docs, uuids=current_uuids)


    # embed batch
    def embed_batch(self, docs: list[str], uuids: list[int]):
        # embed batch
        embeddings = self.embed_model.encode(docs, device='mps')

        # save + update bools
        payload = [
            {
                'uuid': id_,
                'vector': vec,
                'is_embedded': True
            } for id_, vec in zip(uuids, embeddings)
        ]
        (
            self.tbl.merge_insert(on='uuid')
            .when_matched_update_all()
            .execute(payload)
        )
