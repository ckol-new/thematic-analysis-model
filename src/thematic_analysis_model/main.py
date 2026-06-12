import lancedb
from thematic_analysis_model.model.dclasses import SchemaContent, SchemaSentence
from thematic_analysis_model.model.scraping_pipeline import ScrapingPipeline, ALZConnectedScrapingPipeline
from thematic_analysis_model.model.embedding_pipeline import EmbeddingPipeline
import asyncio
from sentence_transformers import SentenceTransformer

def main():
    db = lancedb.connect('database')

    tbl = db.create_table('content', schema=SchemaContent, mode='overwrite')
    stbl = db.create_table('sentence', schema=SchemaSentence, mode='overwrite')
    tbl.create_scalar_index('url_hash')
    stbl.create_scalar_index('sentence_hash')

    # tbl = db.open_table('content')
    # stbl = db.open_table('sentence')

    seeds = [
        'https://alzconnected.org/categories/i-have-alzheimers-or-other-dementia',
        'https://alzconnected.org/categories/i-have-alzheimers-or-other-dementia/p2',
        'https://alzconnected.org/categories/i-have-alzheimers-or-other-dementia/p3'
    ]
    pipeline = ALZConnectedScrapingPipeline()
    asyncio.run(pipeline.run_pipeline(
        seeds=seeds,
        table=tbl,
        origin='alzconnected/i-have-alzheimers-or-other-dementia'
    ))

    print(tbl.count_rows())
    df = tbl.search().select(['url_hash']).to_pandas()
    print(df.head(100))

    model = SentenceTransformer('all-MiniLM-L6-v2')
    embed_pipeline = EmbeddingPipeline()
    embed_pipeline.run_pipeline(
        tbl, stbl, model
    )


    '''
    embed_pipeline = EmbeddingPipeline()

    embed_pipeline.run_embedding_pipeline(
        stbl,
        model
    )
    '''

    df = stbl.search().select(['sentence', 'is_embedded']).to_pandas()
    print(df.head(100))
    print(stbl.count_rows())



if __name__ == '__main__':
    main()