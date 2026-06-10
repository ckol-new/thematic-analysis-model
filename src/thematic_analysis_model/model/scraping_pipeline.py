from abc import ABC, abstractmethod
import asyncio
import httpx
from bs4 import BeautifulSoup

class ScrapingPipeline(ABC):
    def __init__(self):
        pass

    @classmethod
    async def run_pipeline(cls, seeds: list[str]):
        NUM_CRAWLERS = 15
        NUM_SCRAPERS = 15

        crawl_nodes: set = set()
        seed_queue = asyncio.Queue()
        [seed_queue.put_nowait(seed) for seed in seeds]
        # task group for crawling
        headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(headers=headers, timeout=15) as client:
            async with asyncio.TaskGroup() as tg:
                for i in range(NUM_CRAWLERS):
                    tg.create_task(cls.crawler(i, seed_queue, client, crawl_nodes))

        print('CRAWLING COMPLETE')

        print(len(crawl_nodes))
        # scraping task group

    @classmethod
    async def request_page(cls, client: httpx.AsyncClient, url: str) -> str:
        try:
            response = await client.get(url)
            html = response.text
            return html
        except httpx.ReadTimeout as e:
            print(f'Error in requesting {url} with timeout error {e}')
        except Exception as e:
            print(f'Error in requesting {url} with error {e}')

    @classmethod
    async def crawler(cls, worker_id: int,  seeds: asyncio.Queue, client: httpx.AsyncClient, crawl_nodes: set):
        print(f'Starting crawler {worker_id}')

        while True:
            try:
                url = seeds.get_nowait()
            except asyncio.QueueEmpty as e:
                print(f'Crawler {worker_id} has finished')
                break
                
            try:
                html = await ScrapingPipeline.request_page(client, url)
                soup = BeautifulSoup(html, 'html.parser')
                crawl_output = ScrapingPipeline.crawl(soup)
                print(crawl_output)
                for i in crawl_output:
                    crawl_nodes.add(i)

            except Exception as e:
                print(f'Crawler {worker_id} has failed at {url} exception {e}')
            finally: 
                seeds.task_done()
    
    @classmethod
    def seed_generator(cls, prefix: str, start: int, end: int, suffix: str) -> list[str]:
        seeds = []
        for i in range(start, end + 1):
            seed = f'{prefix}{i}{suffix}'
            seeds.append(seed)
        return seeds


    @classmethod
    def crawl(cls, soup: BeautifulSoup) -> list[str]: 
        ...





class ALZConnectedScrapingPipeline(ScrapingPipeline):
    def __init__(self):
        super().__init__()

    def crawl(cls, soup: BeautifulSoup) -> list[str]:
        links = set()
        for link in soup.find_all('a'):
            href = link.get('href')
            if '/discussion/' in href:
                links.add(href)
        return list(links)

