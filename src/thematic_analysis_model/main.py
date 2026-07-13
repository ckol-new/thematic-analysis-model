import asyncio
from thematic_analysis_model.config import *
from thematic_analysis_model.model.manage_data import Loader, CorpusManager, Processor
from thematic_analysis_model.model.scraping import ALZConnectedScrapingPipeline, DementiaSupportForumScrapingPipeline, Crawler
from thematic_analysis_model.model.embedding import Embedder
from thematic_analysis_model.model.dclasses import Sentence, Content
from thematic_analysis_model.model.util import seed_generator

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

    seeds = seed_generator(
        prefix='https://alzconnected.org/categories/i-have-younger-onset-alzheimers/p',
        start=1,
        stop=5,
        suffix=''
    )

    scraping_pipeline = ALZConnectedScrapingPipeline(
        tbl=ptbl,
        forum_name='alzconnected_earlyonset',
        seeds=seeds
    )

    asyncio.run(scraping_pipeline.run_pipeline())
    print(ptbl.count_rows())

    print(stbl.count_rows())
    processor = Processor(
        content_tbl=ptbl,
        sentence_tbl=stbl
    )
    processor.process_content()
    print(stbl.count_rows())
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