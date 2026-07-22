from .data_management import Loader, Manager
from .config import CONTENT_TBL_NAME, NUM_CRAWLERS, NUM_SCRAPERS

import asyncio
import httpx
from bs4 import BeautifulSoup
from tqdm import tqdm

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

    # main entry
    async def run_pipeline(self, seeds: list[str]):
        # initiatilize async queues
        #   seed queue is for seed nodes
        #   crawl_queue is for results of crawling, to be scraped from
        #   save queue is for results of scraping, to be saved
        seed_queue = asyncio.Queue()
        crawl_queue = asyncio.Queue()
        save_queue = asyncio.Queue()

        # crawl
        asyncio.run(self.run_crawler(seeds=seeds, seed_queue=seed_queue, crawl_queue=crawl_queue))

        # scrape
        asyncio.run(self.run_scraper(crawl_queue=crawl_queue, save_queue=save_queue))


    # run crawler
    async def run_crawler(self, seeds: list[str], seed_queue: asyncio.Queue, crawl_queue: asyncio.Queue):
        ...

    # run scraper
    async def run_scraper(self, crawl_queue: asyncio.Queue, save_queue: asyncio.Queue):
        ...

    # request page
    #   Error catching
    #   If verbose is true, it tells you the errors instead of staying silent
    @classmethod
    def request_page(cls, url: str, verbose: bool = False) -> BeautifulSoup:
        soup = None
        return soup

    # abstract methods
    @classmethod
    def crawl(cls, soup: BeautifulSoup):
        ...

    @classmethod
    def scrape(cls, soup: BeautifulSoup):
        ...

# Crawler class
#   Asynchronously crawls list of seed nodes (forum index pages), generating list of crawl nodes (urls to crawl from)
#   Deduplication of crawl nodes
#   Requires you pass it the specific crawl function for its forum type
class Crawler:
    def __init__(self, seeds: list[str], seed_queue: asyncio.Queue, crawl_queue: asyncio.Queue, crawl_func,  NUM_CRAWLERS: int = NUM_CRAWLERS):
        self.seeds = seeds
        self.seed_queue = seed_queue
        self.crawl_queue = crawl_queue
        self.crawl_func = crawl_func

    # main entry 
    async def run_crawler(self):
        # poplate seed queue w/ seeds: seed queue is now full
        [self.seed_queue.put_nowait(seed) for seed in self.seeds]

        # get pbar
        self.pbar = tqdm(total=self.seed_queue.qsize(), desc='CRAWLING', unit='URLs')

        # get async client: time out set to 15
        # get taskgroup
        # init crawlers
        #   crawl until seed queue is empty, shut down, return crawl queue
        async with httpx.AsyncClient(timeout=15.0) as self.client:
            async with asyncio.TaskGroup() as tg:
                # get workers: async crawlers
                workers = [tg.create_task(self.async_crawler(id_=i)) for i in range(1, NUM_CRAWLERS + 1)]

                # await for seed queue to be cleared
                await self.seed_queue.join()

                # cancel workers
                [worker.cancel() for worker in workers]

        return self.crawl_queue

    # async crawler worker
    #   crawls, and returns crawl urls
    #   if Verbose, print out error messages
    async def async_crawler(self, id_: int, verbose: bool = False) -> str:
        # init print statement
        if verbose:
            print(f"Initializing asynchronous crawler #{id_}")

        # crawl
        while True:
            # get url
            url = self.seed_queue.get_nowait()

            try:
                # request page
                soup = await ScrapingPipeline.request_page(url=url, verbose=verbose)

                # crawl page
                # add to crawl queue
                crawl_nodes: list[str] = self.crawl_func(soup=soup)
                if len(crawl_nodes) == 0 or not crawl_nodes: continue
                [self.crawl_queue.put_nowait(crawl_node) for crawl_node in crawl_nodes if crawl_node]
            except Exception as e:
                if verbose:
                    print(f"Unknown parsing error at url: {url} -> {e}")
            finally:
                # update
                self.seed_queue.task_done()
                self.pbar.update(1)
        ...