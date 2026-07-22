from .data_management import Loader, Manager
from .config import CONTENT_TBL_NAME, NUM_CRAWLERS, NUM_SCRAPERS, SAVER_BATCH_SIZE
from .dataclasses import Content

import asyncio
from pydantic import ValidationError
import httpx
from bs4 import BeautifulSoup
from tqdm import tqdm

# Web scraping and crawling. Text processing. Validation
#   Scraping is Asynchronous

# ScrapingPipeline acts as a wrapper, to run both Crawlers and Scrapers, with relevant methods for each forum
#   Extend the ScrapingPipeline to contain relevant methods for each forum

class ScrapingPipeline:
    def __init__(self, loader: Loader, manager: Manager, num_crawlers: int, num_scrapers: int, verbose: bool = False):
        self.forum_origin = None
        self.loader = loader
        self.manager = manager
        self.content_tbl = self.loader.connect(name=CONTENT_TBL_NAME)

        self.num_crawlers = num_crawlers
        self.num_scrapers = num_scrapers
        self.verbose = verbose

    # main entry
    async def run_pipeline(self, seeds: list[str], verbose: bool = False):
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
        crawler = Crawler(
            forum_origin=self.forum_origin,
            seeds=seeds,
            seed_queue=seed_queue,
            crawl_queue=crawl_queue,
            crawl_func=self.crawl(), # subclasses own implementation
            NUM_CRAWLERS=self.num_crawlers
        )
        # populates mutable crawl queue as it runs
        crawler.run_crawler(
            verbose=self.verbose
        )

    # run scraper
    async def run_scraper(self, crawl_queue: asyncio.Queue, save_queue: asyncio.Queue):
        ...

    # request page
    #   Error catching
    #   If verbose is true, it tells you the errors instead of staying silent
    @classmethod
    async def request_page(cls, url: str, client: httpx.AsyncClient, verbose: bool = False, headers: dict | None = None) -> BeautifulSoup:
        if not headers:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }

        try:
            response = await client.get(url=url, headers=headers)

            if verbose:
                if response.status_code not in [200, 301, 303]:
                    print(f"Issue with response status at page: {url} -> {response.status_code}")

            soup = BeautifulSoup(response.text, 'html.parser')

            return soup
        
        # error catch/process
        # AI generated
        except BaseException as e:
            if verbose:
                print(f'💥 Caught at {url}! Exception Type: {type(e).__name__} -> Message: {e}')
        
            # CRITICAL: If it is a CancelledError, you MUST re-raise it so the 
            # event loop can clean up the task properly.
            if type(e).__name__ == "CancelledError":
                raise
        except Exception as e:
            if verbose:
                print(f"Error in requesting page: {url} -> {e}")


# Crawler class
#   Asynchronously crawls list of seed nodes (forum index pages), generating list of crawl nodes (urls to crawl from)
#   Deduplication of crawl nodes
#   Requires you pass it the specific crawl function for its forum type
class Crawler:
    def __init__(self, forum_origin: str, seeds: list[str], seed_queue: asyncio.Queue, crawl_queue: asyncio.Queue, crawl_func,  NUM_CRAWLERS: int = NUM_CRAWLERS):
        self.forum_origin = forum_origin
        self.seeds = seeds
        self.seed_queue = seed_queue
        self.crawl_queue = crawl_queue
        self.crawl_func = crawl_func

    # main entry 
    async def run_crawler(self, verbose: bool = False):
        # poplate seed queue w/ seeds: seed queue is now full
        [self.seed_queue.put_nowait(seed) for seed in self.seeds]

        # get pbar
        self.pbar = tqdm(total=self.seed_queue.qsize(), desc=f'CRAWLING {self.forum_origin}', unit='URLs')

        # get async client: time out set to 15
        # get taskgroup
        # init crawlers
        #   crawl until seed queue is empty, shut down, return crawl queue
        async with httpx.AsyncClient(timeout=15.0) as self.client:
            async with asyncio.TaskGroup() as tg:
                # get workers: async crawlers
                workers = [tg.create_task(self.async_crawler(id_=i, verbose=verbose)) for i in range(1, NUM_CRAWLERS + 1)]

                # await for seed queue to be cleared
                await self.seed_queue.join()

                # cancel workers
                [worker.cancel() for worker in workers]

        self.pbar.close()

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


# Scraper
#   Asynchronously scrape, error catch, deduplicate
class Scraper:
    def __init__(self, forum_origin: str, crawl_queue: asyncio.Queue, save_queue: asyncio.Queue, scrape_func, NUM_SCRAPERS: int = NUM_SCRAPERS):
        self.forum_origin = forum_origin
        self.crawl_queue = crawl_queue
        self.save_queue = save_queue
        self.scrape_func = scrape_func
        self.NUM_SCRAPERS = NUM_SCRAPERS

    # main entry
    async def run_scraper(self, verbose: bool = False):
        # get pbar
        self.pbar = tqdm(total=self.crawl_queue.qsize(), desc=f'SCRAPING {self.forum_origin}', unit='URLs')

        # get async client
        # get task group
        # get workers
        async with httpx.AsyncClient(timeout=15.0) as self.client:
            async with asyncio.TaskGroup() as tg:
                # get scraper workers
                workers = [tg.create_task(self.async_scraper(i)) for i in range(1, NUM_SCRAPERS + 1)]
                saver = tg.create_task(self.async_saver())

                # await for scraping to be finished
                await self.crawl_queue.join()
                # add sentinel value to tell saver to stop
                self.save_queue.put_nowait(None)

                # await for saving to be finished
                await self.save_queue.join()

                # cancel workers
                [worker.cancel() for worker in workers]
                saver.cancel()

        self.pbar.close()

    # asynchronous scraper
    async def async_scraper(self, id_: int, verbose: bool = False):
        if verbose:
            print(f"Initializing asynchronous scraper number {id_}")

        # until cancel, run scraper
        while True:
            # get url from crawl queue
            url: str = self.crawl_queue.get_nowait()

            try:
                # request page and add to save queue
                soup = await ScrapingPipeline.request_page(url=url, verbose=verbose)
                contents: list[Content] = self.scrape_func(soup=soup) # scrape function of scraping pipeline subclass
                if len(contents) == 0 or not contents:
                    continue
                [self.save_queue.put_nowait(content) for content in contents if content]

            except ValidationError as v:
                if verbose:
                    print(f"Validation error at url: {url} -> {v}")
            except Exception as e:
                if verbose:
                    print(f"Exception at url: {url} -> {e}")
            finally:
                self.crawl_queue.task_done()
                self.pbar.update(1)
        ...
    
    # asyncrhonous saver
    async def async_saver(self, SAVE_BATCH_SIZE: int = SAVER_BATCH_SIZE, verbose: bool = False):
        if verbose:
            print('Initializing saver')

        ...