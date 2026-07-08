# all classes around scraping and processing
import asyncio
import httpx
import tqdm
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod

# crawl from each index page for the forum, to retrieve valid forum posts/pages/discussions/threads
# abstract base class
class Crawler(ABC):
    def __init__(self, forum_name: str, seeds: list[str], num_crawlers: int = 20):
        self.seeds = seeds
        self.num_crawlers = num_crawlers
        self.pbar = tqdm.tqdm(total=len(seeds), desc=f'CRAWLING {forum_name}', unit='URLs')   

    async def run_crawler(self):
        # populate seed queue
        self.seed_queue: asyncio.Queue = asyncio.Queue()
        self.populate_seed_queue()

        # init crawl queue
        self.crawl_queue: asyncio.Queue = asyncio.Queue()

        # get async scraping client
        async with httpx.Client(timeout=15.0) as self.client:
            # create async task group, to act as context manager
            async with asyncio.TaskGroup() as tg:
                crawlers = []
                # create crawlers as tasks in task group
                for i in range(1, self.num_crawlers + 1):
                    crawlers.append(asyncio.create_task(self.async_crawler(id_=i)))
                
                # await for the seed queue to be emptied, as all crawling is finished
                await self.seed_queue.join()

                # close all workers
                [crawler.cancel() for crawler in crawlers]
        
        return self.crawl_queue()


    def populate_seed_queue(self):
        [self.seed_queue.put_nowait(seed) for seed in self.seeds]

    async def request_page(self, url: str) -> BeautifulSoup:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        try:
            # wait for response
            response = await self.client.get(url, headers=headers)
            if response.status_code not in [200, 301, 303]: 
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
        except Exception as e:
            print(f'Caught Exception {e} at url {url}')
            return None

    async def async_crawler(self, id_: int):
        # init method
        print(f'Initializing async crawler number: {id_}')

        while True:
            # get url 
            url: str = await self.seed_queue.get()

            # 
            try:
                # request page
                soup: BeautifulSoup = self.request_page(url=url)
                if not soup: continue

                # get crawl nodes
                crawl_nodes: list[str] = self.crawl(soup)

                # add to crawl queue
                [self.crawl_queue.put_nowait(node) for node in crawl_nodes if node]
            except Exception as e:
                print(f"💥 Unexpected parsing error at {url}: {type(e).__name__} -> {e}")
            finally:
                # task done
                self.seed_queue.task_done()
                self.pbar.update(1)


    @abstractmethod
    def crawl(self, soup:BeautifulSoup) -> list[str]:
        ...
    


# scrape each valid post/page/discussion/thread.
class Scraper:
    ...


