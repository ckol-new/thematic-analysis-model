import asyncio
from thematic_analysis_model.config import *
from thematic_analysis_model.model.manage_data import Loader, CorpusManager
from thematic_analysis_model.model.scraping import ALZConnectedScrapingPipeline
from thematic_analysis_model.model.dclasses import Line, Content

import pprint

def main():
    # load database
    loader = Loader(
        lance_path=LANCE_PATH,
        tbl1_name=CONTENT_TBL_NAME,
        tbl2_name=LINE_TBL_NAME
    )
    loader.first_init(schema1=Content, schema2=Line)
    db, ptbl, ltbl = loader.connect()
    print(ptbl.count_rows())

    seeds = [
        'https://alzconnected.org/categories/i-have-younger-onset-alzheimers/p1'
        'https://alzconnected.org/categories/i-have-younger-onset-alzheimers/p2'
        'https://alzconnected.org/categories/i-have-younger-onset-alzheimers/p3'
    ]

    scraping_pipeline = ALZConnectedScrapingPipeline(
        tbl=ptbl,
        seeds=seeds,
        forum_name='ALZConnected_EarlyOnset'
    )
    asyncio.run(scraping_pipeline.run_pipeline())
    print(ptbl.count_rows())
    print(ptbl.count_rows(filter='title IS NULL'))
    df = ptbl.search().where('title IS NULL').select(['url', 'title']).to_pandas()
    print(df.head())



if __name__ == '__main__':
    main()