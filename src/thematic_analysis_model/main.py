# main file
from thematic_analysis_model.model.config import *
from thematic_analysis_model.model.data_management import Loader, Manager
from thematic_analysis_model.model.scraping import alzconnectedScrapingPipeline, ScrapingPipeline

import asyncio

def scrape():
    loader = Loader()
    loader.first_init() # reset on tests
    manager = Manager(loader=loader)

    print(type(loader))
    pipeline = alzconnectedScrapingPipeline(
        loader=loader,
        manager=manager,
        num_crawlers=NUM_CRAWLERS,
        num_scrapers=NUM_SCRAPERS,
        forum_origin='alzconnected',
        verbose=True
    )
    seeds = ScrapingPipeline.seed_generator(
        prefix="https://alzconnected.org/categories/i-have-alzheimers-or-other-dementia/p",
        start=1,
        stop=3,
        suffix=""
    )
    asyncio.run(pipeline.run_pipeline(seeds))

    print(loader.connect(name='content').count_rows())


def main():
    loader = Loader() # loader is composed into classes that need table access directly. 

    # test 



if __name__ == "__main__":
    scrape()