# all classes around scraping and processing
from ..config import NUMBER_OF_CRAWLERS, NUMBER_OF_SCRAPERS
from .manage_data import Processor
import lancedb
import asyncio
from pydantic import ValidationError
import httpx
import tqdm
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
import xxhash
import uuid
import datetime
from .dclasses import Content, ContentType


# wrapper coordinates crawler and scrapers
# extend this class for forum specific scraping and crawling
class ScrapingPipelineWrapper(ABC):
    def __init__(self, tbl: lancedb.Table, forum_name: str, seeds: list[str], num_crawlers: int = NUMBER_OF_CRAWLERS, num_scrapers: int = NUMBER_OF_SCRAPERS):
        self.tbl = tbl
        self.forum_name = forum_name
        self.seeds = seeds
        self.num_crawlers = num_crawlers
        self.num_scrapers = num_scrapers
    
    async def run_pipeline(self):
        # crawl pipeline
        crawler = Crawler(forum_name=self.forum_name, seeds=self.seeds, crawl_func=self.crawl, num_crawlers=self.num_crawlers)
        crawl_queue: asyncio.Queue = await crawler.run_crawler()

        # scrape pipeline
        scraper = Scraper(tbl=self.tbl, forum_name=self.forum_name, crawl_queue=crawl_queue, scrape_func=self.scrape, num_scrapers=self.num_scrapers)
        await scraper.run_scraper()

        # finished
    
    @classmethod
    async def request_page(cls, url: str, client: httpx.AsyncClient) -> BeautifulSoup:
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
    def crawl(cls, soup: BeautifulSoup):
        ...

    @classmethod
    def scrape(cls, soup: BeautifulSoup, url: str, origin: str):
        ...



# crawl from each index page for the forum, to retrieve valid forum posts/pages/discussions/threads
# abstract base class
class Crawler:
    def __init__(self, forum_name: str, seeds: list[str], crawl_func, num_crawlers: int = 20):
        self.seeds = seeds
        self.num_crawlers = num_crawlers
        self.crawl_func = crawl_func
        self.pbar = tqdm.tqdm(total=len(seeds), desc=f'CRAWLING {forum_name}', unit='URLs')   

    async def run_crawler(self):
        # populate seed queue
        self.seed_queue: asyncio.Queue = asyncio.Queue()
        self.populate_seed_queue()

        # init crawl queue
        self.crawl_queue: asyncio.Queue = asyncio.Queue()

        # get async scraping client
        async with httpx.AsyncClient(timeout=15.0) as self.client:
            # create async task group, to act as context manager
            async with asyncio.TaskGroup() as tg:
                crawlers = []
                # create crawlers as tasks in task group
                for i in range(1, self.num_crawlers + 1):
                    crawlers.append(tg.create_task(self.async_crawler(id_=i)))

                # await for the seed queue to be emptied, as all crawling is finished
                await self.seed_queue.join()

                # cancel all tasks
                for crawler in crawlers:
                    crawler.cancel()

        
        self.pbar.close()
        return self.crawl_queue


    def populate_seed_queue(self):
        [self.seed_queue.put_nowait(seed) for seed in self.seeds]

    async def async_crawler(self, id_: int):
        # init method
        print(f'Initializing async crawler number: {id_}')

        while True:
            # get url 
            url: str = await self.seed_queue.get()

            try:
                # request page
                soup: BeautifulSoup = await ScrapingPipelineWrapper.request_page(url=url, client=self.client)
                if not soup: continue

                # get crawl nodes
                crawl_nodes: list[str] = self.crawl_func(soup=soup)
                if not crawl_nodes or len(crawl_nodes) == 0: continue

                # add to crawl queue
                [self.crawl_queue.put_nowait(node) for node in crawl_nodes if node]
            except Exception as e:
                print(f"💥 Unexpected parsing error at {url}: {type(e).__name__} -> {e}")
            finally:
                # task done
                self.seed_queue.task_done()
                self.pbar.update(1)


# scrape each valid post/page/discussion/thread.
class Scraper:
    def __init__(self, tbl: lancedb.Table, forum_name: str, crawl_queue: asyncio.Queue, scrape_func,  num_scrapers: int = 20):
        self.tbl = tbl
        self.forum_name = forum_name
        self.crawl_queue = crawl_queue
        self.num_scrapers = num_scrapers
        self.scrape_func = scrape_func
        self.scrape_queue = asyncio.Queue()
        self.pbar = tqdm.tqdm(total=self.crawl_queue.qsize(), desc=f'SCRAPING {forum_name}', unit='URLs')

    async def run_scraper(self):

        # get scrapers
        async with httpx.AsyncClient(timeout=15.0) as self.client:
            async with asyncio.TaskGroup() as tg:
                scrapers = []
                saver = tg.create_task(self.async_saver())

                for i in range(1, self.num_scrapers + 1):
                    scrapers.append(tg.create_task(self.async_scraper(id_=i)))


                # wait for scraping to finish
                await self.crawl_queue.join()

                # put sentinel value to escape saver
                self.scrape_queue.put_nowait(None)

                await self.scrape_queue.join()

                # cancel tasks
                for scraper in scrapers:
                    scraper.cancel()
                saver.cancel()



        # close pbar
        self.pbar.close()

    async def async_scraper(self, id_: int, SCRAPE_MAX_SIZE: int = 5000):
        # init
        print(f'Initializing scraper number: {id_}')

        while True:
            # check if need to save, then yield to event loop to allow saver to clear scrape queue and save
            if self.scrape_queue.qsize() >= SCRAPE_MAX_SIZE:
                await asyncio.sleep(0) # let saver work

            # get crawl node
            crawl_node = await self.crawl_queue.get()
            if not crawl_node:
                self.crawl_queue.task_done()
                break

            # scrape crawl node
            try:
                soup: BeautifulSoup = await ScrapingPipelineWrapper.request_page(url=crawl_node, client=self.client)

                # add to scrape queue
                contents: list[Content] = self.scrape_func(soup=soup, url=crawl_node, origin=self.forum_name)
                if not contents or len(contents) == 0:
                    continue

                [self.scrape_queue.put_nowait(content) for content in contents if contents ]
            except ValidationError as v:
                print(f'Validation error at {crawl_node}: {type(v).__name__} -> {v}')
            except Exception as e:
                print(f"💥 Unexpected parsing error at {crawl_node}: {type(e).__name__} -> {e}")
            finally:
                self.crawl_queue.task_done()
                self.pbar.update(1)
            
    async def async_saver(self, SAVE_BATCH_SIZE: int = 25002500):
        # init
        print(f"initializing saver")       

        save_batch = []
        while True:
            # get content
            item = await self.scrape_queue.get() 

            # once scrape queue is empty -> add to save batch
            if item is None:
                deduplicated_batch = list({content.hash_: content for content in save_batch}.values())
                try:
                    (
                        self.tbl.merge_insert(on='hash_')
                        .when_not_matched_insert_all()
                        .execute(deduplicated_batch)
                    )
                except Exception as e:
                    print(f"💥 Save failed on batch: {type(e).__name__} -> {e}")
                save_batch.clear()
                deduplicated_batch.clear()
                self.scrape_queue.task_done()
                break
            
            save_batch.append(item)
            self.scrape_queue.task_done()

            # if save batch is full, save to lancedb
            if len(save_batch) >= SAVE_BATCH_SIZE:
                # in memory de-duplication
                deduplicated_batch = list({obj.hash_: obj for obj in save_batch}.values())
                # save to lancedb
                try:
                    (
                        self.tbl.merge_insert(on='hash_')
                        .when_not_matched_insert_all()
                        .execute(deduplicated_batch)
                    )
                except Exception as e:
                    print(f"💥 Save failed on batch: {type(e).__name__} -> {e}")

                save_batch.clear()
                deduplicated_batch.clear()
                # self.scrape_queue.task_done()
        
        # Save if batch not empty
        if len(save_batch) != 0:
            # in memory de-duplication
            deduplicated_batch = list({obj.hash_: obj for obj in save_batch}.values())
            # save to lancedb
            try:
                (
                    self.tbl.merge_insert(on='hash_')
                    .when_not_matched_insert_all()
                    .execute(deduplicated_batch)
                )
            except Exception as e:
                print(f"💥 Save failed on batch: {type(e).__name__} -> {e}")

            save_batch.clear()
            deduplicated_batch.clear()
            # self.scrape_queue.task_done()
            

class ScrapingQueue:
    def __init__(self, tbl: lancedb.Table, scrape_configs: list[dict] | dict):
        self.tbl = tbl
        if type(scrape_configs) == dict: self.scrape_configs = [scrape_configs]
        else: self.scrape_configs = scrape_configs

    def run_queue(self):
        count = 1
        total = len(self.scrape_configs)
        for config in self.scrape_configs:
            print(f'********* RUNNING CONFIG: {count} / {total} *********')
            count += 1

            scraping_pipeline = config['type_scraping_pipeline'](
                tbl=self.tbl,
                forum_name=config['forum_name'],
                seeds=config['seeds'],
                num_crawlers=config['num_crawlers'],
                num_scrapers=config['num_scrapers']
            )
            asyncio.run(scraping_pipeline.run_pipeline())



# extensions of ScrapingPipelineWrapper
class ALZConnectedScrapingPipeline(ScrapingPipelineWrapper):
    def __init__(self, tbl: lancedb.Table, forum_name: str, seeds: list[str], num_crawlers: int = NUMBER_OF_CRAWLERS, num_scrapers: int = NUMBER_OF_SCRAPERS):
        super().__init__(tbl=tbl, forum_name=forum_name, seeds=seeds, num_crawlers=num_crawlers, num_scrapers=num_scrapers)
    
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
    def scrape(cls, soup: BeautifulSoup, url: str, origin: str) -> list[Content]:
        # get post
        post: Content = cls.scrape_post(soup, url, origin)
        if not post:
            return None

        parent_uuid: str = post.uuid

        # get comments
        comments: list[Content] = []
        comment_div_list = soup.find_all('div', class_='Comment')
        for comment_div in comment_div_list:
            comment: Content = cls.scrape_comment(comment_div, url, parent_uuid, origin)
            comments.append(comment)

        # return list concat
        return [post] + comments
    
    @classmethod
    def scrape_post(cls, soup: BeautifulSoup, url: str, origin: str) -> Content:
        # get post div
        post_div = soup.find('div', class_='Discussion')

        # get content
        content = cls.scrape_content(post_div)

        # get title
        title = cls.scrape_title(soup)

        # get date
        date: str = cls.scrape_date(post_div)

        # get author name
        username: str = cls.scrape_username(post_div)
        
        # misc
        hash_: str = xxhash.xxh64(url).hexdigest()
        date_accessed: str = str(datetime.date.today())
        my_uuid: str = str(uuid.uuid4())
        uuid_parent = None
        content_type = 'post'
        origin: str = origin

        # validate essentials (metadata + content)
        content: Content = Content(
            text=content,
            url=url,
            date=date,
            title=title,
            author_username=username,
            forum_origin=origin,
            hash_=hash_,
            uuid= my_uuid,
            parent_uuid=None,
            date_accessed=date_accessed,
            type_='post',
            is_processed=False
        )

        return content

    @classmethod
    def scrape_comment(cls, soup: BeautifulSoup, url: str, parent_uuid: str, origin: str) -> Content:
        # get content
        content = cls.scrape_content(soup)

        # get date
        date: str = cls.scrape_date(soup)

        # get author name
        username: str = cls.scrape_username(soup)
        
        # misc
        hash_: str = xxhash.xxh64(url).hexdigest()
        date_accessed: str = str(datetime.date.today)
        my_uuid: str = str(uuid.uuid4())
        uuid_parent = parent_uuid
        content_type: str = 'post'
        origin: str = origin

        # validate essentials (metadata + content)
        content: Content = Content(
            text=content,
            url=url,
            date=date,
            title=None,
            author_username=username,
            forum_origin=origin,
            hash_=hash_,
            uuid=my_uuid,
            parent_uuid=uuid_parent,
            date_accessed=date_accessed,
            type_='comment',
            is_processed=False
        )

        return content
        ...
    @classmethod
    def scrape_content(cls, soup: BeautifulSoup) -> str:
        # get text
        text: str = soup.get_text(separator='', strip=True)

        # clean text
        text: str = Processor.clean_text(text)

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

    @classmethod
    def scrape_title(cls, soup: BeautifulSoup):
        title = soup.find('title')
        if not title:
            return None

        return title.get_text()

class DementiaSupportForumScrapingPipeline(ScrapingPipelineWrapper):
    def __init__(self, tbl: lancedb.Table, forum_name: str, seeds: list[str], num_crawlers: int = NUMBER_OF_CRAWLERS, num_scrapers: int = NUMBER_OF_SCRAPERS):
        super().__init__(tbl=tbl, forum_name=forum_name, seeds=seeds, num_crawlers=num_crawlers, num_scrapers=num_scrapers)

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
    def scrape(cls, soup: BeautifulSoup, url: str, origin: str) -> list[Content]:
        # get post
        post: Content= cls.scrape_post(soup, url, origin)
        if not post:
            return []

        parent_uuid: str = post.uuid

        # get comments
        comments: list[Content] = []
        comment_div_list = soup.find_all('article', class_='message--post')
        for comment_div in comment_div_list:
            # if not comment_div: continue
            comment: Content= cls.scrape_comment(comment_div, url, parent_uuid, origin)
            comments.append(comment)

        # return list concat
        return [post] + comments
    
    @classmethod
    def scrape_post(cls, soup: BeautifulSoup, url: str, origin: str) -> Content:
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
        origin: str = origin
        title: str = cls.scrape_title(soup)

        # validate essentials (metadata + content)
        content: Content = Content(
            text=content,
            url=url,
            date=date,
            title=title,
            author_username=username,
            forum_origin=origin,
            hash_=url_hash,
            uuid=my_uuid,
            parent_uuid=None,
            date_accessed=date_accessed,
            type_='post',
            is_processed=False
        )

        return content

    @classmethod
    def scrape_comment(cls, soup: BeautifulSoup, url: str, parent_uuid: str, origin: str) -> Content:

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
        title = None

        # validate essentials (metadata + content)
        content: Content = Content(
            text=content,
            url=url,
            date=date,
            title=title,
            author_username=username,
            forum_origin=origin,
            hash_=url_hash,
            uuid=my_uuid,
            parent_uuid=uuid_parent,
            date_accessed=date_accessed,
            type_='comment',
            is_processed=False
        )

        return content

    @classmethod
    def scrape_content(cls, soup: BeautifulSoup) -> str:
        post_message_div = soup.find('div', class_='bbWrapper')

        # get text
        text: str = post_message_div.get_text(separator='', strip=True)

        # clean text
        text: str = Processor.clean_text(text)

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
    def scrape_username(cls, soup: BeautifulSoup):
        username: str = soup.get('data-author')
        if not username: return None
        return str(username)
    
    @classmethod
    def scrape_title(cls, soup: BeautifulSoup) -> str:
        title = soup.find('title')
        if not title: return None
        return title.get_text()
