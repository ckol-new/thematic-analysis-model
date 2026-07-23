from .data_management import Loader, Manager
from .config import SENTENCE_TBL_NAME, EMBED_BATCH_SIZE

import numpy as np
from tqdm import tqdm

# embedding data
#   Class for embedding sentences
class Embedder:
    def __init__(self, loader: Loader, manager: Manager):
        self.loader = loader
        self.manager = manager

        # load model
        self.embedding_model = self.loader.load_embedding_model() # loads default embedding model

    # main entry
    def run_embedder(self, EMBED_BATCH_SIZE: int = EMBED_BATCH_SIZE):
        # get batches of unembedded sentences
        # embed batches
        # save batches + update bools
        pbar = tqdm(
            total=self.manager.get_num_match_condition(tbl_name=SENTENCE_TBL_NAME, condition='is_embedded = false'),
            desc='EMBEDDING',
            unit='sentences'
            )
        for batch in self.manager.batch_generator(
            tbl_name=SENTENCE_TBL_NAME,
            condition="is_embedded = false",
            columns=['sentence', 'uuid_']
            ):
            sentences = batch['sentence'].tolist()
            uuids = batch['uuid_'].tolist()

            # paginate to embed in batches
            for i in range(0, len(uuids), EMBED_BATCH_SIZE):
                current_docs = sentences[i:i+EMBED_BATCH_SIZE]
                current_uuids = uuids[i:i+EMBED_BATCH_SIZE]

                # embed
                embeddings = self.embed_batch(docs=current_docs)

                # save + update bools
                data = [
                    {
                        'uuid_': uuid,
                        'embedding': list(embedding),
                        'is_embedded': True
                    } for uuid, embedding in zip(current_uuids, list(embeddings), strict=True)
                ]

                self.manager.matched_update(
                    tbl_name=SENTENCE_TBL_NAME,
                    key='uuid_',
                    data=data
                )
                pbar.update(len(uuids))

        pbar.close()
                                            

    # embeds batch of sentences
    def embed_batch(self, docs: list[str]) -> np.ndarray:
        # embed
        return self.embedding_model.encode(docs, device='mps', convert_to_numpy=True)