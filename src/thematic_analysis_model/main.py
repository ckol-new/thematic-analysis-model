import lancedb
from thematic_analysis_model.model.dclasses import SchemaContent, SchemaSentence
from thematic_analysis_model.model.scraping_pipeline import ScrapingPipeline, ALZConnectedScrapingPipeline, AlzSocietyDementiaSupportForum
from thematic_analysis_model.model.embedding_pipeline import EmbeddingPipeline
import asyncio
from sentence_transformers import SentenceTransformer

'''
# FINISHED ALREADY
config = [
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/i-have-dementia.56/page-', start=1, stop=109),
        'origin': 'AlzSocietyDementiaSupportForum/I-have-dementia',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/i-have-a-partner-with-dementia.69/page-', start=1, stop=109),
        'origin': 'AlzSocietyDementiaSupportForum/I-have-a-partner-with-dementia',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://alzconnected.org/categories/i-am-a-caregiver-(general-topics)/p', 1, 100),
        'origin': 'ALZConnected/I-Am-A-Caregiver',
        'scraper': ALZConnectedScrapingPipeline()
    }
]
'''


def main():
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

    model = SentenceTransformer('all-MiniLM-L6-v2')

    for forum in config:
        print('SCRAPING')
        asyncio.run(
            forum['scraper'].run_pipeline(
                seeds=forum['seeds'],
                table=tbl,
                origin=forum['origin']
            )
        )

        print("EMBEDDING")
        embed_pipeline = EmbeddingPipeline()
        embed_pipeline.run_pipeline(
            tbl, stbl, model
        )

    print(tbl.count_rows())
    print(stbl.count_rows())



    



if __name__ == '__main__':
    main()