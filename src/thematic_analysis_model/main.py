import lancedb
from thematic_analysis_model.model.dclasses import SchemaContent, SchemaSentence
from thematic_analysis_model.model.scraping_pipeline import ScrapingPipeline, ALZConnectedScrapingPipeline, AlzSocietyDementiaSupportForum
from thematic_analysis_model.model.embedding_pipeline import EmbeddingPipeline
import asyncio
from sentence_transformers import SentenceTransformer

'''
# FINISHED ALREADY

'''
def main():
    db = lancedb.connect('database')

    tbl = db.open_table('content')
    stbl = db.open_table('sentence')

    print(tbl.count_rows())
    print(stbl.count_rows())

def main1():
    db = lancedb.connect('database')

    '''
    tbl = db.create_table('content', schema=SchemaContent, mode='overwrite')
    stbl = db.create_table('sentence', schema=SchemaSentence, mode='overwrite')
    tbl.create_scalar_index('url_hash')
    stbl.create_scalar_index('sentence_hash')
    '''

    tbl = db.open_table('content')
    stbl = db.open_table('sentence')

    print(tbl.count_rows())
    print(stbl.count_rows())

    model = SentenceTransformer('all-MiniLM-L6-v2', device='mps')
    ep = EmbeddingPipeline()
    ep.run_embedding_pipeline(
        stbl, model
    )

    '''
    for forum in DementiaSupportForum:
        print(f"PROCESSING {forum['origin']}")
        asyncio.run(
            forum['scraper'].run_pipeline(
                seeds=forum['seeds'],
                table=tbl,
                origin=forum['origin']
            )
        )

        embed_pipeline = EmbeddingPipeline()
        embed_pipeline.run_processing_pipeline(
            tbl, stbl
        )
    '''

    print(tbl.count_rows())
    print(stbl.count_rows())



    



if __name__ == '__main__':
    main()