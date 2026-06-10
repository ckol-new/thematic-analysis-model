import lancedb
from thematic_analysis_model.model.dclasses import SchemaContent, SchemaSentence
from thematic_analysis_model.model.scraping_pipeline import ScrapingPipeline, ALZConnectedScrapingPipeline
import asyncio

def main():
    db = lancedb.connect('database')
    # tbl = db.create_table('content', schema=SchemaContent, mode='overwrite')
    # stbl = db.create_table('sentence', schema=SchemaSentence, mode='overwrite')

    tbl = db.open_table('content')
    stbl = db.open_table('sentence')

    scraping_pipeline = ALZConnectedScrapingPipeline()
    asyncio.run(
        scraping_pipeline.run_pipeline(
            ScrapingPipeline.seed_generator('https://alzconnected.org/categories/i-have-alzheimers-or-other-dementia/p', 1, 13, '')
        )
    )

if __name__ == '__main__':
    main()