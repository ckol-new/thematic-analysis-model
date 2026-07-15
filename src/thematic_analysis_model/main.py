import asyncio
from thematic_analysis_model.config import *
from thematic_analysis_model.scrape_config import ALZConnected_total, DementiaSupportForum_TOTAL
from thematic_analysis_model.model.manage_data import Loader, CorpusManager, Processor
from thematic_analysis_model.model.scraping import ALZConnectedScrapingPipeline, DementiaSupportForumScrapingPipeline, Crawler, ScrapingQueue
from thematic_analysis_model.model.embedding import Embedder
from thematic_analysis_model.model.modelling import Modeller, Validator, Trial, TrialQueue
from thematic_analysis_model.model.dclasses import Sentence, Content, TrialConfig
from thematic_analysis_model.model.util import seed_generator
from thematic_analysis_model.model_config import topic_model, embed_model

from sentence_transformers import SentenceTransformer

import pprint

def scraping_a():
    configs = ALZConnected_total + DementiaSupportForum_TOTAL
    # load database
    loader = Loader(
        lance_path=LANCE_PATH,
        tbl1_name=CONTENT_TBL_NAME,
        tbl2_name=LINE_TBL_NAME
    )
    # loader.first_init(schema1=Content, schema2=Sentence)
    db, ptbl, stbl = loader.connect()
    corpus_manager = CorpusManager(tbl1=ptbl, tbl2=stbl)

    # 


def main():
    # load database
    loader = Loader(
        lance_path=LANCE_PATH,
        tbl1_name=CONTENT_TBL_NAME,
        tbl2_name=LINE_TBL_NAME
    )
    # loader.first_init(schema1=Content, schema2=Sentence)
    db, ptbl, stbl = loader.connect()

    corpus_manager = CorpusManager(tbl1=ptbl, tbl2=stbl)

    configs = TrialQueue.generate_trial_configs(
        model_save_path='models/fine-tuning/{trial_desc}',
        validation_metric_save_path='validation_metrics/fine-tuning/{trial_desc}',
        embedding_model='all-MiniLM-L6-v2',
        n_neighbours=15,
        n_components=5,
        min_cluster_size=[20, 25, 27, 30, 32, 35, 37, 40],
        min_samples=None
    )

    queue = TrialQueue(
        tbl=stbl,
        configs=configs,
        corpus_manager=corpus_manager
    )
    queue.run_queue()


def reset():
    # load database
    loader = Loader(
        lance_path=LANCE_PATH,
        tbl1_name=CONTENT_TBL_NAME,
        tbl2_name=LINE_TBL_NAME
    )
    loader.first_init(schema1=Content, schema2=Sentence)
    db, p, s = loader.connect()
    print(p.count_rows())
    print(s.count_rows())

def clean_db():
    # current lance
    loader = Loader(LANCE_PATH, CONTENT_TBL_NAME, LINE_TBL_NAME)
    db, tbl1, tbl2 = loader.connect()
    manager = CorpusManager(tbl1,tbl2)
    manager.clean_lancedb(0)

    # old lance
    loader2 = Loader(Path.cwd() / 'database', 'content', 'sentence')
    db, tbl1, tbl2 = loader2.connect()
    manager2 = CorpusManager(tbl1,tbl2)
    manager.clean_lancedb(0)







    
   



    

def debug():
    main()

def eg_debug():
    try:
        main()
    except* Exception as eg:
        for exc in eg.exceptions:
            import traceback
            traceback.print_exception(type(exc), exc, exc.__traceback__)

if __name__ == '__main__':
    debug()