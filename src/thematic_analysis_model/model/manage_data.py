# all classes around managing data
import lancedb
from .dclasses import Sentence, Content
from .util import get_ids_by_condition, batch_generator, shuffle_ids
from ..config import FILE_IO_BATCH_SIZE_DEFUALT, MIN_SENTENCE_LEN

from tqdm import tqdm
import gc
from pathlib import Path
from datetime import timedelta
import codecs
from uuid import uuid4
import xxhash

# methods around loading the database
class Loader:
    def __init__(self, lance_path: Path | str, tbl1_name: str, tbl2_name: str):
        self.lance_path = lance_path
        self.tbl1_name = tbl1_name
        self.tbl2_name = tbl2_name
    
    # creates table with schema 
    def first_init(self, schema1: type, schema2: type):
        db = lancedb.connect(self.lance_path)
        tbl1 = db.create_table(name=self.tbl1_name, schema=schema1, mode='overwrite')
        tbl2 = db.create_table(name=self.tbl2_name, schema=schema2, mode='overwrite')
    
    # opens table
    def connect(self):
        db = lancedb.connect(self.lance_path)
        tbl1 = db.open_table(name=self.tbl1_name)
        tbl2 = db.open_table(name=self.tbl2_name)
        return db, tbl1, tbl2

# methods for processing text, and splitting to sentences
class Processor:
    def __init__(self, content_tbl: lancedb.Table, sentence_tbl: lancedb.Table):
        self.content_tbl = content_tbl
        self.sentence_tbl = sentence_tbl

    def process_content(self, BATCH_SIZE: int = FILE_IO_BATCH_SIZE_DEFUALT):
        # get unprocessed content ids
        ids = get_ids_by_condition(tbl=self.content_tbl, query='is_processed = false')

        # get usernames set
        # usernames: set = cls.get_all_usernames(content_tbl=content_tbl, BATCH_SIZE=BATCH_SIZE)

        # for unprocessed batch -> split to lines, remove usernames, validate lines
        for batch in batch_generator(ids=ids, tbl=self.content_tbl, columns=['text', 'date', 'uuid', 'url', 'type_', 'forum_origin'], BATCH_SIZE=BATCH_SIZE):
            current_sentences: list[Sentence] = []

            # get each row
            for row in batch.itertuples(index=True):
                # process usernames, replace with token

                # split text to sentences
                sentences = self.split_by_sentence(text=row.text)
                for sentence in sentences:
                    # generate 'Sentence' objects
                    sentence_obj: Sentence = Sentence(
                        sentence=sentence,
                        url=row.url,
                        date=row.date,
                        forum_origin=row.forum_origin,
                        content_origin_uuid=row.uuid,
                        uuid=str(uuid4()),
                        hash_=xxhash.xxh64(sentence).hexdigest(),
                        type_=row.type_,
                        vector=None,
                        is_embedded=False,
                        is_modelled=False,
                        is_validated=False,
                        topic=None,
                        probabilities=None
                    )
                    current_sentences.append(sentence_obj)

            # save to lance
            self.__save_batch(sentences=current_sentences, uuids=batch['uuid'].tolist())
            current_sentences.clear()
            gc.collect()
    


    # get all usernames as set, might come with performance cost???
    def get_all_usernames(self, BATCH_SIZE: int = FILE_IO_BATCH_SIZE_DEFUALT):
        usernames = set()

        # get ids
        ids = get_ids_by_condition(tbl=self.content_tbl)

        # get batches, add usernames to set in batches)
        for batch in batch_generator(ids=ids, tbl=self.content_tbl, columns=['author_username'], BATCH_SIZE=BATCH_SIZE):
            # convert to list
            usernames_list = batch['author_username'].tolist()

            # add list to set
            usernames.update(usernames_list)

        # return usernames set
        return usernames
    
    def split_by_sentence(self, text: str, MIN_SENTENCE_LEN: int = MIN_SENTENCE_LEN):
        sentences = [s.strip() for s in text.split(sep='. ') if len(s) >= MIN_SENTENCE_LEN]
        return sentences
    
    # save batch of Lines, deduplicate, update bools
    def __save_batch(self, sentences: list[Sentence], uuids: list[str]):
        # update line table
        (
            self.sentence_tbl.merge_insert(on='hash_')
            .when_not_matched_insert_all()
            .execute(sentences)
        )

        # update bools
        payload = [
            {
                'uuid': id_,
                'is_processed': True
            } for id_ in uuids
        ]
        (
            self.content_tbl.merge_insert(on='uuid')
            .when_matched_update_all()
            .execute(payload)
        )


    @classmethod
    def clean_text(cls, text: str) -> str:
        if not text:
            return None
        # two step decoding for double escape
        try:
            text = codecs.decode(text, 'unicode-escape') 
        except:
            pass
        for i in range(2):
            try:
                text = text.encode('latin-1').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                break
            
        return text 
    

    def post_process(self):
        ids = self.sentence_tbl.search().with_row_id(True).select(['_rowid']).to_arrow()['_rowid'].to_pylist()
        sequences = ['https', 'MemberPost']
        to_remove: list[str] = []
        pbar = tqdm(total=len(ids), desc='POST_PROCESSING', unit='sentence')

        # batch process
        for batch in batch_generator(ids=ids, tbl=self.sentence_tbl, columns=['sentence', 'uuid']): 
            sentences = batch['sentence'].tolist()
            uuids = batch['uuid'].tolist()
            for s, u in zip(sentences, uuids, strict=True):
                # if contains sequences to remove
                if any(seq in s for seq in sequences):
                    to_remove.append(u)
                # if too short
                if len(s) < MIN_SENTENCE_LEN:
                    to_remove.append(u)
        
        # batch delete
        DEL_BATCH_SIZE = 500
        for i in range(0, len(to_remove), DEL_BATCH_SIZE):
            current_del_batch = to_remove[i:i+DEL_BATCH_SIZE]
            formatted_ids = ", ".join(f"'{uid}'" for uid in current_del_batch)
            query = f'uuid IN ({formatted_ids})'
            self.sentence_tbl.delete(where=query)
            pbar.update(len(current_del_batch))
        
        self.sentence_tbl.compact_files()
        pbar.close()





# methods around pruning, cleaning, and diagnosing the corpus
class CorpusManager:
    def __init__(self, tbl1: lancedb.Table, tbl2: lancedb.Table):
        self.tbl1 = tbl1
        self.tbl2 = tbl2

    # helps with testing unprocessed lines
    def sample_sentences(self, num: int = 1000):
        lines = self.tbl2.search().where('forum_origin LIKE "%dementiasupportforum%"').select(['sentence']).to_arrow()['sentence'].to_pylist()
        return lines

    # reset validation flags
    def reset_validation_bool_flags(self):
        self.tbl2.update(values_sql={
        'is_validated': 'cast(false as boolean)'
        })
    
    # reset modelling + validation flags(self):
    def reset_modelling_bool_flags(self):
        self.tbl2.update(values_sql={
        'is_modelled': 'cast(false as boolean)'
        })
        self.reset_validation_bool_flags()

    # reset embedding + modelling + validating flags   
    def reset_embedding_bool_flags(self):
        self.tbl2.update(values_sql={
            'is_embedded': 'cat(false as boolean)'
        })
        self.reset_modelling_bool_flags()

    # reset processing flags
    def reset_processing_flags(self):
        self.tbl1.update(values_sql={
            'is_processed': 'cat(false as boolean)'
        })
        self.reset_embedding_bool_flags()
    
    # clean lancedb size: reduces size of lancedb
    def clean_lancedb(self, days: int = 0):

        # compact fragments
        self.tbl1.optimize(cleanup_older_than=timedelta(days=days))
        self.tbl2.optimize(cleanup_older_than=timedelta(days=days))