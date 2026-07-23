# main file
from thematic_analysis_model.model.config import *
from thematic_analysis_model.model.data_management import Loader, Manager
from thematic_analysis_model.model.scraping import alzconnectedScrapingPipeline, dementiasupportforumScrapingPipeline,  ScrapingPipeline, Processor

import pprint
import asyncio

def scrape():
    loader = Loader()
    loader.first_init() # reset on tests
    manager = Manager(loader=loader)

    pipeline = dementiasupportforumScrapingPipeline(
        loader=loader,
        manager=manager,
        num_crawlers=NUM_CRAWLERS,
        num_scrapers=NUM_SCRAPERS,
        forum_origin='dementiasupportforum',
        verbose=True
    )
    seeds = ScrapingPipeline.seed_generator(
        prefix="https://forum.alzheimers.org.uk/forums/i-have-dementia.56/page-",
        start=1,
        stop=10,
        suffix=""
    )
    asyncio.run(pipeline.run_pipeline(seeds))

    print(loader.connect(name='content').count_rows())

    processor = Processor(
        manager=manager
    )
    processor.run_processor()
    print(loader.connect(name='sentence').count_rows())


def main():
    loader = Loader() # loader is composed into classes that need table access directly. 
    manager = Manager(loader=loader) # manager gives classes access to the table, to update or retrieve data.

    sentences = manager.retrieve_column_list('sentence', columns=['sentence'])
    pprint.pprint(sentences)



if __name__ == "__main__":
    main()