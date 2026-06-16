from abc import ABC, abstractmethod
from .dclasses import SchemaContent
import lancedb
from pydantic import ValidationError
import asyncio
import httpx
from tqdm import tqdm
import codecs
import uuid
import xxhash
from bs4 import BeautifulSoup
import datetime

class ScrapingPipeline(ABC):
    def __init__(self):
        ...

    @classmethod
    async def run_pipeline(cls, seeds: list[str], table: lancedb.Table, origin: str):
        # fill seed queue
        seed_queue = asyncio.Queue()
        cls.populate_seed_queue(seeds, seed_queue)
        seeds.clear()

        crawl_queue = asyncio.Queue()
        scrape_queue = asyncio.Queue()
        
        # run crawl pipeline
        await cls.run_crawl_pipeline(seed_queue, crawl_queue)

        # run scrape pipeline
        # batch save as necessary
        await cls.run_scrape_pipeline(table, crawl_queue, scrape_queue, origin)

    @classmethod
    def populate_seed_queue(cls, seeds: list[str], queue: asyncio.Queue):
        [queue.put_nowait(seed) for seed in seeds]

    
    @classmethod
    async def run_crawl_pipeline(cls, seed_queue: asyncio.Queue, crawl_queue: asyncio.Queue, num_crawler: int = 20):
        print('CRAWL BEGIN')
        # trask group of crawlers, each with a httpx.async client
        with tqdm(total=seed_queue.qsize(), desc='CRAWLING SEEDS', unit='url') as pbar:
            async with httpx.AsyncClient(timeout=15.0) as client:
                async with asyncio.TaskGroup() as tg:
                    workers = []
                    for i in range(1, num_crawler + 1):
                        workers.append(asyncio.create_task(cls.crawler(i, client, seed_queue, crawl_queue, pbar)))

                    # check for all tasks to finish
                    await seed_queue.join()

                    # shut down workers
                    for worker in workers:
                        worker.cancel()
                    
        print(f'ALL CRAWLING TASKS FINISHED')

    @classmethod
    async def crawler(cls, worker_id: int, client: httpx.AsyncClient, seed_queue: asyncio.Queue, crawl_queue: asyncio.Queue, pbar):
        print(f'Initializing crawler number: {worker_id}')
        while True:

            # check if seed queue is empty       
            url: str = await seed_queue.get()

            try:
                # request page by seed
                soup: BeautifulSoup = await cls.request_page(client, url)
                if not soup: continue

                # get crawl nodes
                crawl_nodes: list[str] = cls.crawl(soup)

                # save crawl nodes to crawl_queue
                for node in crawl_nodes:
                    await crawl_queue.put(node)               
            except ValidationError as v:
                ...
            except Exception as e:
                print(f"💥 Unexpected parsing error at {url}: {type(e).__name__} -> {e}")
            finally:
                # task done
                seed_queue.task_done()
                pbar.update(1)

    @classmethod
    async def run_scrape_pipeline(cls, table: lancedb.Table, crawl_queue: asyncio.Queue, scrape_queue: asyncio.Queue, origin: str, num_scrapers: int = 20):
        # task group of scrapers, and saver 
        with tqdm(total=crawl_queue.qsize(), desc='SCRAPING PAGES', unit='url') as pbar:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, max_redirects=3) as client:
                async with asyncio.TaskGroup() as tg:
                    print('INITIALIZING SCRAPERS')
                    scrapers = [tg.create_task(cls.scraper(i, client, crawl_queue, scrape_queue, origin, pbar)) for i in range(1, num_scrapers + 1)]
                    print('INITIALIZING SAVER')
                    saver = tg.create_task(cls.saver(table, scrape_queue))

                    # check for all scrape tasks to finish
                    await crawl_queue.join()

                    # clear scrapers 
                    for scraper in scrapers:
                        scraper.cancel()

                    # none stopper
                    await scrape_queue.put(None)

                    # check for all save tasks to finish
                    await scrape_queue.join()

                    # force save

                    # clear saver
                    saver.cancel()

        # clear old queues/data
        print(f'FINISHED SCRAPING AND SAVING')
        ...

    @classmethod
    async def scraper(cls, worker_id: int, client: httpx.AsyncClient, crawl_queue: asyncio.Queue, scrape_queue: asyncio.Queue, origin: str, pbar, SCRAPED_MAX_SIZE: int = 5000):
        print(f'initializing scraper number {worker_id}')
        while True:
            # check scrape size, if too full wait until saver flushes it
            if scrape_queue.qsize() >= SCRAPED_MAX_SIZE:
                await asyncio.sleep(0) # yield to event loop, should turn off all scrapers until saver flushes 

            # get url
            url: str = await crawl_queue.get()

            try:
                # get soup obj
                soup: BeautifulSoup = await cls.request_page(client, url)
                if not soup: continue

                # scrape content -> content dclass list
                contents: list[SchemaContent] = cls.scrape(soup, url, origin)

                # add to scrape_queue
                for content in contents:
                    await scrape_queue.put(content)
            except ValidationError as v:
                ...
            except Exception as e:
                print(f"💥 Unexpected parsing error at {url}: {type(e).__name__} -> {e}")
            finally:
                crawl_queue.task_done()
                pbar.update(1)
            
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

    @classmethod
    async def saver(cls, table: lancedb.Table, scrape_queue: asyncio.Queue, LANCE_BATCH_SIZE: int = 2500):
        print("INITIALIZING SAVER")
        batch = []

        while True:
            item = await scrape_queue.get()

            if item is None:
                # in memory de-duplication
                deduplicated_batch = list({obj.url_hash: obj for obj in batch}.values())
                (
                    table.merge_insert(on='url_hash')
                    .when_not_matched_insert_all()
                    .execute(deduplicated_batch)
                )
                batch.clear()
                deduplicated_batch.clear()
                scrape_queue.task_done()
                break

            batch.append(item)
            scrape_queue.task_done()

            if len(batch) >= LANCE_BATCH_SIZE:
                # in memory de-duplication
                deduplicated_batch = list({obj.url_hash: obj for obj in batch}.values())
                # save to lancedb
                (
                    table.merge_insert(on='url_hash')
                    .when_not_matched_insert_all()
                    .execute(batch)
                )
                batch.clear()
                deduplicated_batch.clear()



    # implement in subclass
    @classmethod
    def crawl(cls, soup: BeautifulSoup) -> list[str]:
        # get all valid posts
        ...

    #implement in subclass
    @classmethod
    def scrape(cls, soup: BeautifulSoup, url: str, origin: str) -> list[SchemaContent]:
        ...
    # all abstract methods
    @classmethod
    def scrape_date(cls, soup: BeautifulSoup) -> str:
        ...
    @classmethod
    def scrape_username(cls, soup: BeautifulSoup) -> str:
        ...
    @classmethod
    def scrape_post(cls, soup: BeautifulSoup) -> str:
        ...
    @classmethod
    def scrape_comment(cls, soup: BeautifulSoup) -> str:
        ...

    @classmethod
    def clean_text(cls, text: str) -> str:
        if not text:
            return None
        # two step decoding for double escape
        try:
            text = codecs.decode(text, 'unicode-escape') 
        except:
            pass
        for i in range(2):
            try:
                text = text.encode('latin-1').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                break
            
        return text 
        ...
    
    @classmethod
    def seed_generator(cls, prefix: str, start: int, stop: int, suffix: str = ''):
        seeds = []
        for i in range(start, stop):
            seed = prefix + str(i) + suffix
            seeds.append(seed)
        return seeds
    

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

    @classmethod
    def scrape(cls, soup: BeautifulSoup, url: str, origin: str) -> list[SchemaContent]:
        # get post
        post: SchemaContent = cls.scrape_post(soup, url, origin)
        if not post:
            return None

        parent_uuid: str = post.uuid

        # get comments
        comments: list[SchemaContent] = []
        comment_div_list = soup.find_all('div', class_='Comment')
        for comment_div in comment_div_list:
            comment: SchemaContent = cls.scrape_comment(comment_div, url, parent_uuid, origin)
            comments.append(comment)

        # return list concat
        return [post] + comments
    
    @classmethod
    def scrape_post(cls, soup: BeautifulSoup, url: str, origin: str) -> SchemaContent:
        # get post div
        post_div = soup.find('div', class_='Discussion')

        # get content
        content = cls.scrape_content(post_div)

        # get date
        date: str = cls.scrape_date(post_div)

        # get author name
        username: str = cls.scrape_username(post_div)
        
        # misc
        url_hash: str = xxhash.xxh64(url).hexdigest()
        date_accessed: str = str(datetime.date.today())
        my_uuid: str = str(uuid.uuid4())
        uuid_parent = None
        content_type: str = 'post'
        origin: str = origin

        # validate essentials (metadata + content)
        content: SchemaContent = SchemaContent(
            url=url,
            url_hash=url_hash,
            uuid=my_uuid,
            parent_uuid=uuid_parent,
            date=date,
            date_accessed=date_accessed,
            origin=origin,
            username=username,
            content=content,
            content_type=content_type,
            is_split=False
        )

        return content

    @classmethod
    def scrape_comment(cls, soup: BeautifulSoup, url: str, parent_uuid: str, origin: str) -> SchemaContent:
        # get content
        content = cls.scrape_content(soup)

        # get date
        date: str = cls.scrape_date(soup)

        # get author name
        username: str = cls.scrape_username(soup)
        
        # misc
        url_hash: str = xxhash.xxh64(url).hexdigest()
        date_accessed: str = str(datetime.date.today)
        my_uuid: str = str(uuid.uuid4())
        uuid_parent = parent_uuid
        content_type: str = 'post'
        origin: str = origin

        # validate essentials (metadata + content)
        content: SchemaContent = SchemaContent(
            url=url,
            url_hash=url_hash,
            uuid=my_uuid,
            parent_uuid=uuid_parent,
            date=date,
            date_accessed=date_accessed,
            origin=origin,
            username=username,
            content=content,
            content_type=content_type,
            is_split=False
        )

        return content
        #
        ...
    @classmethod
    def scrape_content(cls, soup: BeautifulSoup) -> str:
        # get text
        text: str = soup.get_text(separator='', strip=True)

        # clean text
        text: str = cls.clean_text(text)

        # validate text
        if not text or len(text) <= 5:
            return None

        # return text
        return text
        ...
    @classmethod
    def scrape_date(cls, soup: BeautifulSoup) -> str:
        time_div = soup.find('time')
        if not time_div: return None
        date = time_div.get('title')
        if not date: return None
        return str(date)
        
    @classmethod
    def scrape_username(cls, soup):
        username_div = soup.find('a', class_='Username js-userCard')
        if not username_div:
            return None
        username = username_div.text
        if not username: return None
        return str(username)

class AlzSocietyDementiaSupportForum(ScrapingPipeline):
    def __init__(self):
        super().__init__()

    # crawl page
    @classmethod
    def crawl(cls, soup: BeautifulSoup) -> list[str]:
        links = set()
        list_a = soup.find_all('a')
        if not list_a: return []
        for link in list_a:
            href = link.get('href')
            if not href: continue
            if '/threads/' in href:
                if href.startswith('https'):
                    links.add(href)
                else: 
                    l = 'https://forum.alzheimers.org.uk' + href
                    links.add(l)

        if len(list(links)) == 0: return []
        return list(links)

    @classmethod
    def scrape(cls, soup: BeautifulSoup, url: str, origin: str) -> list[SchemaContent]:
        # get post
        post: SchemaContent = cls.scrape_post(soup, url, origin)
        if not post:
            return []

        parent_uuid: str = post.uuid

        # get comments
        comments: list[SchemaContent] = []
        comment_div_list = soup.find_all('article', class_='message--post')
        for comment_div in comment_div_list:
            # if not comment_div: continue
            comment: SchemaContent = cls.scrape_comment(comment_div, url, parent_uuid, origin)
            comments.append(comment)

        # return list concat
        return [post] + comments
    
    @classmethod
    def scrape_post(cls, soup: BeautifulSoup, url: str, origin: str) -> SchemaContent:
        # get post div
        post_div = soup.find('article', class_='message-threadStarterPost')
        if not post_div: return None

        # get content
        content = cls.scrape_content(post_div)

        # get date
        date: str = cls.scrape_date(post_div)

        # get author name
        username: str = cls.scrape_username(post_div)
        
        # misc
        url_hash: str = xxhash.xxh64(url).hexdigest()
        date_accessed: str = str(datetime.date.today())
        my_uuid: str = str(uuid.uuid4())
        uuid_parent = None
        content_type: str = 'post'
        origin: str = origin

        # validate essentials (metadata + content)
        content: SchemaContent = SchemaContent(
            url=url,
            url_hash=url_hash,
            uuid=my_uuid,
            parent_uuid=uuid_parent,
            date=date,
            date_accessed=date_accessed,
            origin=origin,
            username=username,
            content=content,
            content_type=content_type,
            is_split=False
        )

        return content

    @classmethod
    def scrape_comment(cls, soup: BeautifulSoup, url: str, parent_uuid: str, origin: str) -> SchemaContent:

        # get content
        content = cls.scrape_content(soup)

        # get date
        date: str = cls.scrape_date(soup)

        # get author name
        username: str = cls.scrape_username(soup)
        
        # misc
        url_hash: str = xxhash.xxh64(url).hexdigest()
        date_accessed: str = str(datetime.date.today)
        my_uuid: str = str(uuid.uuid4())
        uuid_parent = parent_uuid
        content_type: str = 'post'
        origin: str = origin

        # validate essentials (metadata + content)
        content: SchemaContent = SchemaContent(
            url=url,
            url_hash=url_hash,
            uuid=my_uuid,
            parent_uuid=uuid_parent,
            date=date,
            date_accessed=date_accessed,
            origin=origin,
            username=username,
            content=content,
            content_type=content_type,
            is_split=False
        )

        return content

    @classmethod
    def scrape_content(cls, soup: BeautifulSoup) -> str:
        post_message_div = soup.find('div', class_='bbWrapper')

        # get text
        text: str = post_message_div.get_text(separator='', strip=True)

        # clean text
        text: str = cls.clean_text(text)

        # validate text
        if not text or len(text) <= 5:
            return None

        # return text
        return text

    @classmethod
    def scrape_date(cls, soup: BeautifulSoup) -> str:
        time_div = soup.find('time')
        if not time_div: return None
        date = time_div.get_text()
        if not date: return None
        return str(date)

    @classmethod
    def scrape_username(cls, soup):
        username: str = soup.get('data-author')
        if not username: return None
        return str(username)