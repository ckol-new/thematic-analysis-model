import asyncio
from thematic_analysis_model.config import *
from thematic_analysis_model.scrape_config import ALZConnected_total
from thematic_analysis_model.model.manage_data import Loader, CorpusManager, Processor
from thematic_analysis_model.model.scraping import ALZConnectedScrapingPipeline, DementiaSupportForumScrapingPipeline, Crawler, ScrapingQueue
from thematic_analysis_model.model.embedding import Embedder
from thematic_analysis_model.model.modelling import Modeller, Validator, Trial, TrialQueue
from thematic_analysis_model.model.dclasses import Sentence, Content, TrialConfig
from thematic_analysis_model.model.util import seed_generator
from thematic_analysis_model.model_config import topic_model, embed_model

from sentence_transformers import SentenceTransformer

import pprint

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


    config1 = TrialConfig(
        trial_num=1,
        trial_desc='testing',
        model_save_path=str((MODEL_SAVE_PATH_BASE / 'model1_test').resolve()),
        validation_metric_save_path=str((VALIDATION_SAVE_PATH_BASE / 'model1_test').resolve()),
        embedding_model=EMBEDDING_MODEL_NAME,
        n_neighbours=15,
        n_components=2,
        min_cluster_size=5,
        min_samples=None
    )
    config2 = TrialConfig(
        trial_num=2,
        trial_desc='testing',
        model_save_path=str((MODEL_SAVE_PATH_BASE / 'model2_test').resolve()),
        validation_metric_save_path=str((VALIDATION_SAVE_PATH_BASE / 'model2_test').resolve()),
        embedding_model=EMBEDDING_MODEL_NAME,
        n_neighbours=15,
        n_components=2,
        min_cluster_size=10,
        min_samples=None
    )
    config3 = TrialConfig(
        trial_num=3,
        trial_desc='testing',
        model_save_path=str((MODEL_SAVE_PATH_BASE / 'model3_test').resolve()),
        validation_metric_save_path=str((VALIDATION_SAVE_PATH_BASE / 'model3_test').resolve()),
        embedding_model=EMBEDDING_MODEL_NAME,
        n_neighbours=15,
        n_components=2,
        min_cluster_size=15,
        min_samples=None
    )
    config4 = TrialConfig(
        trial_num=4,
        trial_desc='testing',
        model_save_path=str((MODEL_SAVE_PATH_BASE / 'model4_test').resolve()),
        validation_metric_save_path=str((VALIDATION_SAVE_PATH_BASE / 'model4_test').resolve()),
        embedding_model=EMBEDDING_MODEL_NAME,
        n_neighbours=15,
        n_components=2,
        min_cluster_size=20,
        min_samples=None
    )
    config5 = TrialConfig(
        trial_num=5,
        trial_desc='testing',
        model_save_path=str((MODEL_SAVE_PATH_BASE / 'model5_test').resolve()),
        validation_metric_save_path=str((VALIDATION_SAVE_PATH_BASE / 'model5_test').resolve()),
        embedding_model=EMBEDDING_MODEL_NAME,
        n_neighbours=15,
        n_components=2,
        min_cluster_size=25,
        min_samples=None
    )
    configs = [config1, config2, config3, config4, config5]

    queue = TrialQueue(
        tbl=stbl,
        configs=configs,
        corpus_manager=corpus_manager
    )
    queue.run_queue()
    
    corpus_manager.clean_lancedb(days=1) # optimize storage


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