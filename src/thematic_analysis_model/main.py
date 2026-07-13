import asyncio
from thematic_analysis_model.config import *
from thematic_analysis_model.scrape_config import ALZConnected_total
from thematic_analysis_model.model.manage_data import Loader, CorpusManager, Processor
from thematic_analysis_model.model.scraping import ALZConnectedScrapingPipeline, DementiaSupportForumScrapingPipeline, Crawler, ScrapingQueue
from thematic_analysis_model.model.embedding import Embedder
from thematic_analysis_model.model.dclasses import Sentence, Content
from thematic_analysis_model.model.util import seed_generator

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
    '''
    print(ptbl.count_rows())

    # scrape
    scrape_queue = ScrapingQueue(
        tbl=ptbl,
        scrape_configs=ALZConnected_total
    )
    scrape_queue.run_queue()
    print(ptbl.count_rows())
    '''

    '''
    processor = Processor(content_tbl=ptbl, sentence_tbl=stbl)
    processor.process_content()
    print(stbl.count_rows())

    processor.post_process()
    print(stbl.count_rows())
    '''

    '''
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    embedder = Embedder(tbl=stbl, embed_model=embed_model)
    embedder.embed()
    '''







    
   



    

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