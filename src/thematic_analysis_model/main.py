import lancedb as ldb
from thematic_analysis_model.config import LDB_PATH, SCRAPE_DATA_TABLE_NAME
from thematic_analysis_model.model.dclasses import Content
from thematic_analysis_model.model.scraping_pipeline import ALZConnectedScrapingPipeline, ScrapingPipeline
import pandas as pd

def main():
    # 
    db = ldb.connect(LDB_PATH)
    table = db.open_table('scrape_data_table')
    print(table.count_rows())
    print(table.schema)

    '''
    seeds1 = ScrapingPipeline.generate_seeds(prefix='https://alzconnected.org/categories/i-have-alzheimers-or-other-dementia/p', start=1, end=12, suffix='')
    seeds2 = ScrapingPipeline.generate_seeds(prefix='https://alzconnected.org/categories/i-have-younger-onset-alzheimers/p', start=1, end=10, suffix='')
    
    seeds = seeds1 + seeds2 

    scraper = ALZConnectedScrapingPipeline()
    scraper.run_pipeline(
        table=table,
        seeds=seeds,
        origin='alzconnected',
        BATCH_SIZE=5000
    )
    '''




    


if __name__ == '__main__':
    main()