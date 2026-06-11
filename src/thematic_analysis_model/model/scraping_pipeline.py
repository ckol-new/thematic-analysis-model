from abc import ABC, abstractmethod
from .dclasses import SchemaContent
import lancedb
import asyncio
import httpx
import uuid
import xxhash
from bs4 import BeautifulSoup
import datetime

class ScrapingPipeline(ABC):
    def __init__(self):
        ...

    @classmethod
    async def run_pipeline(cls, seeds: list[str], table: lancedb.Table):
        # fill seed queue
        seed_queue = asyncio.Queue()
        cls.populate_seed_queue(seeds, seed_queue)
        seeds.clear()

        crawl_queue = asyncio.Queue()
        scrape_queue = asyncio.Queue()
        
        # run crawl pipeline
        await cls.run_crawl_pipeline(seed_queue, crawl_queue)
        print(crawl_queue.qsize())

        # run scrape pipeline
        # cls.run_scrape_pipeline(table, crawl_queue, scrape_queue)
        # batch save as necessary
        ...

    @classmethod
    def populate_seed_queue(cls, seeds: list[str], queue: asyncio.Queue):
        [queue.put_nowait(seed) for seed in seeds]

    
    @classmethod
    async def run_crawl_pipeline(cls, seed_queue: asyncio.Queue, crawl_queue: asyncio.Queue, num_crawler: int = 20):
        print('CRAWL BEGIN')
        # trask group of crawlers, each with a httpx.async client
        async with httpx.AsyncClient() as client:
            async with asyncio.TaskGroup() as tg:
                workers = []
                for i in range(1, num_crawler + 1):
                    workers.append(asyncio.create_task(cls.crawler(i, client, seed_queue, crawl_queue)))

                # check for all tasks to finish
                await seed_queue.join()

                # shut down workers
                for worker in workers:
                    worker.cancel()
                
        print(f'ALL CRAWLING TASKS FINISHED')
        # clear old queues

    @classmethod
    async def crawler(cls, worker_id: int, client: httpx.AsyncClient, seed_queue: asyncio.Queue, crawl_queue: asyncio.Queue):
        print(f'Initializing crawler number: {worker_id}')
        while True:
            # check if seed queue is empty       
            url: str = await seed_queue.get()

            # request page by seed
            soup: BeautifulSoup = await cls.request_page(client, url)

            # get crawl nodes
            crawl_nodes: list[str] = cls.crawl(soup)

            # save crawl nodes to crawl_queue
            for node in crawl_nodes:
                await crawl_queue.put(node)               
                print(f'added node: {node}')

            # task done
            seed_queue.task_done()

        ...

    @classmethod
    async def run_scrape_pipeline(cls, table: lancedb.Table, crawl_queue: asyncio.Queue, scrape_queue: asyncio.Queue, num_scrapers: int = 15):
        # task group of scrapers, and saver 
        async with httpx.AsyncClient() as client:
            async with asyncio.TaskGroup as tg:
                scrapers = [cls.scraper(worker_id=i) for i in range(1, num_scrapers + 1)]
                saver = cls.saver()

                # check for all scrape tasks to finish
                await crawl_queue.join()
                # clear scrapers 
                for scraper in scrapers:
                    scraper.cancel()

                # check for all save tasks to finish
                await scrape_queue.join()
                # clear saver
                saver.clear()

        # clear old queues/data
        print(f'FINISHED SCRAPING AND SAVING')
        ...

    @classmethod
    async def scraper(cls, worker_id: int, client: httpx.AsyncClient, crawl_queue: asyncio.Queue, scrape_queue: asyncio.Queue, SCRAPED_MAX_SIZE: int = 2500):
        print(f'initializing scraper number {worker_id}')
        while True:
            # get url
            url: str = await crawl_queue.get()

            # get soup obj
            soup: BeautifulSoup = await cls.request_page(client, url)

            # scrape content -> content dclass list
            content: SchemaContent = cls.scrape(soup)

            # check scrape size, if too full wait until saver flushes it
            if scrape_queue.qsize() >= SCRAPED_MAX_SIZE:
                await asyncio.sleep(0) # yield to event loop, should turn off all scrapers until saver flushes 

            # add to scrape_queue
            await scrape_queue.put(content)
            crawl_queue.task_done()
            
        ...

    @classmethod
    async def request_page(cls, client: httpx.AsyncClient, url: str) -> BeautifulSoup:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        try:
            # wait for response
            response = await client.get(url, headers=headers)
            print(response.status_code)

            # get text
            html = response.text

            # get soup
            soup = BeautifulSoup(html, 'html.parser')

            # return
            return soup

        # error catch/process
        except BaseException as e:
            print(f'💥 Caught at {url}! Exception Type: {type(e).__name__} -> Message: {e}')
        
            # CRITICAL: If it is a CancelledError, you MUST re-raise it so the 
            # event loop can clean up the task properly.
            if type(e).__name__ == "CancelledError":
                raise
                
            return None

    @classmethod
    async def saver(cls, table: lancedb.Table, scrape_queue: asyncio.Queue, LANCE_BATCH_SIZE: int = 1000):
        batch = []

        while True:
            item = await scrape_queue.get()
            batch.append(item)
            scrape_queue.task_done()

            if len(batch) >= LANCE_BATCH_SIZE:
                # save to lancedb
                table.add(batch)



    # implement in subclass
    @classmethod
    def crawl(cls, soup: BeautifulSoup) -> list[str]:
        # get all valid posts
        ...

    #implement in subclass
    @classmethod
    def scrape(cls, soup: BeautifulSoup, url: str, origin: str) -> SchemaContent:
        ...
    # all abstract methods
    @classmethod
    def scrape_date(cls, soup: BeautifulSoup) -> str:
        ...
    @classmethod
    def scrape_username(cls, soup: BeautifulSoup) -> str:
        ...
    @classmethod
    def scrape_post_content(cls, soup: BeautifulSoup) -> str:
        ...
    @classmethod
    def scrape_comment_content(cls, soup: BeautifulSoup) -> str:
        ...
    

class ALZConnectedScrapingPipeline(ScrapingPipeline):
    def __init__(self):
        super().__init__()


    # crawl page
    @classmethod
    def crawl(cls, soup: BeautifulSoup) -> list[str]:
        links = set()
        for link in soup.find_all('a'):
            href = link.get('href')
            if '/discussion/' in href:
                links.add(href)
        return list(links)