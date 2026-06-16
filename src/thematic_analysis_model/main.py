import lancedb
from thematic_analysis_model.model.dclasses import SchemaContent, SchemaSentence
from thematic_analysis_model.model.scraping_pipeline import ScrapingPipeline, ALZConnectedScrapingPipeline, AlzSocietyDementiaSupportForum
from thematic_analysis_model.model.embedding_pipeline import EmbeddingPipeline
import asyncio
from sentence_transformers import SentenceTransformer

'''
# FINISHED ALREADY
DementiaSupportForum = [
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/i-have-dementia.56/page-', start=1, stop=109),
        'origin': 'AlzSocietyDementiaSupportForum/I-have-dementia',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/i-have-a-partner-with-dementia.69/page-', start=1, stop=617),
        'origin': 'AlzSocietyDementiaSupportForum/I-have-a-partner-with-dementia',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/i-have-dementia.56/page-', start=1, stop=1467),
        'origin': 'AlzSocietyDementiaSupportForum/i-have-dementia',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/younger-people-with-dementia-and-their-carers.27/page-', start=1, stop=137),
        'origin': 'AlzSocietyDementiaSupportForum/younger-people-with-dementia-and-their-carers',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/lgbt-people-with-dementia-and-carers.46/page-', start=1, stop=7),
        'origin': 'AlzSocietyDementiaSupportForum/lgbt-people-with-dementia-and-carers',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/memory-concerns-and-seeking-a-diagnosis.26/page-', start=1, stop=108),
        'origin': 'AlzSocietyDementiaSupportForum/memory-concerns-and-seeking-a-diagnosis',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/recently-diagnosed-and-early-stages-of-dementia.71/page-', start=1, stop=87),
        'origin': 'AlzSocietyDementiaSupportForum/recently-diagnosed-and-early-stages-of-dementia',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/middle-later-stages-of-dementia.72/page-', start=1, stop=237),
        'origin': 'AlzSocietyDementiaSupportForum/middle-later-stages-of-dementia',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/middle-later-stages-of-dementia.72/page-', start=1, stop=237),
        'origin': 'AlzSocietyDementiaSupportForum/middle-later-stages-of-dementia',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/end-of-life-care.73/page-', start=1, stop=90),
        'origin': 'AlzSocietyDementiaSupportForum/end-of-life-care',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/after-dementia-%E2%80%94-dealing-with-loss.28/page-', start=1, stop=125),
        'origin': 'AlzSocietyDementiaSupportForum/after-dementia-dealing-with-loss',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/legal-and-financial-issues.60/page-', start=1, stop=361),
        'origin': 'AlzSocietyDementiaSupportForum/legal-and-financial-issues',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/health-and-wellbeing.75/page-', start=1, stop=31),
        'origin': 'AlzSocietyDementiaSupportForum/health-and-wellbeing',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/coronavirus-covid-19.83/page-', start=1, stop=30),
        'origin': 'AlzSocietyDementiaSupportForum/coronavirus-covid-19',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/equipment-and-technology.77/page-2', start=1, stop=30),
        'origin': 'AlzSocietyDementiaSupportForum/equipment-and-technology',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/equipment-and-technology.77/page-', start=1, stop=30),
        'origin': 'AlzSocietyDementiaSupportForum/health-and-wellbeing',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/books-film-and-music.76/page-', start=1, stop=12),
        'origin': 'AlzSocietyDementiaSupportForum/books-film-and-music',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/innovation-and-research.35/page-2', start=1, stop=47),
        'origin': 'AlzSocietyDementiaSupportForum/innovation-and-research',
        'scraper': AlzSocietyDementiaSupportForum()
    },
]
AllALZConnected = [
    {
        'seeds': ScrapingPipeline.seed_generator('https://forum.alzheimers.org.uk/forums/i-have-a-partner-with-dementia.69/page-', start=1, stop=109),
        'origin': 'AlzSocietyDementiaSupportForum/I-have-a-partner-with-dementia',
        'scraper': AlzSocietyDementiaSupportForum()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://alzconnected.org/categories/i-am-a-caregiver-(general-topics)/p', 1, 100),
        'origin': 'ALZConnected/I-Am-A-Caregiver',
        'scraper': ALZConnectedScrapingPipeline()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://alzconnected.org/categories/spouses-or-partners/p', 1, 100),
        'origin': 'ALZConnected/Caring-For-Spouse-Or-Partner',
        'scraper': ALZConnectedScrapingPipeline()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://alzconnected.org/categories/caring-for-a-parent/p', 1, 100),
        'origin': 'ALZConnected/Caring-For-A-Parent',
        'scraper': ALZConnectedScrapingPipeline()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://alzconnected.org/categories/i-am-a-caregiver-(general-topics)/p', 1, 100),
        'origin': 'ALZConnected/I-Am-A-Caregiver',
        'scraper': ALZConnectedScrapingPipeline()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://alzconnected.org/categories/caring-long-distance/p', 1, 8),
        'origin': 'ALZConnected/Caring-Long-Distance',
        'scraper': ALZConnectedScrapingPipeline()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://alzconnected.org/categories/supporting-those-who-have-lost-someone/p', 1, 7),
        'origin': 'ALZConnected/Supporting-Someone-Who-Has-Lost-Someone',
        'scraper': ALZConnectedScrapingPipeline()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://alzconnected.org/categories/i-have-alzheimers-or-other-dementia/p', 1, 13),
        'origin': 'ALZConnected/I-Have-Alzheimers-Or-Other-Dementia',
        'scraper': ALZConnectedScrapingPipeline()
    },
    {
        'seeds': ScrapingPipeline.seed_generator('https://alzconnected.org/categories/i-have-younger-onset-alzheimers/p', 1, 10),
        'origin': 'ALZConnected/I-Am-Living-With-Younger-Onset-Alzheimers',
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