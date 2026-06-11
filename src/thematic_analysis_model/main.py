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

    seeds = [
        'https://alzconnected.org/categories/i-have-alzheimers-or-other-dementia',
        'https://alzconnected.org/categories/i-have-alzheimers-or-other-dementia/p2',
        'https://alzconnected.org/categories/i-have-alzheimers-or-other-dementia/p3'
    ]
    pipeline = ALZConnectedScrapingPipeline()
    asyncio.run(pipeline.run_pipeline(
        seeds=seeds,
        table=tbl
    ))


if __name__ == '__main__':
    main()