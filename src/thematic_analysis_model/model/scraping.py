from .data_management import Loader, Manager
from .config import CONTENT_TBL_NAME

import asyncio
from bs4 import BeautifulSoup

# Web scraping and crawling. Text processing. Validation
#   Scraping is Asynchronous

# ScrapingPipeline acts as a wrapper, to run both Crawlers and Scrapers, with relevant methods for each forum
#   Extend the ScrapingPipeline to contain relevant methods for each forum

class ScrapingPipeline:
    def __init__(self, loader: Loader, manager: Manager, num_crawlers: int, num_scrapers: int):
        self.loader = loader
        self.manager = manager
        self.content_tbl = self.loader.connect(name=CONTENT_TBL_NAME)

        self.num_crawlers = num_crawlers
        self.num_scrapers = num_scrapers

    # entire pipeline
    async def run_pipeline(self, seeds: list[str]):
        # initiatilize async queues
        #   seed queue is for seed nodes
        #   crawl_queue is for results of crawling, to be scraped from
        #   save queue is for results of scraping, to be saved
        seed_queue = asyncio.Queue()
        crawl_queue = asyncio.Queue()
        save_queue = asyncio.Queue()

        # crawl
        asyncio.run(self.run_crawler(seeds=seeds, seed_queue=seed_queue))

        # scrape
        asyncio.run(self.run_scraper(crawl_queue=crawl_queue, save_queue=save_queue))


    # run crawler
    async def run_crawler(self, seeds: list[str], seed_queue: asyncio.Queue):
        ...

    # run scraper
    async def run_scraper(self, crawl_queue: asyncio.Queue, save_queue: asyncio.Queue):
        ...


    # abstract methods
    @classmethod
    def crawl(cls, soup: BeautifulSoup):
        ...

    @classmethod
    def scrape(cls, soup: BeautifulSoup):
        ...
