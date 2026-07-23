from .data_management import Loader, Manager
from .config import CONTENT_TBL_NAME, SENTENCE_TBL_NAME, NUM_CRAWLERS, NUM_SCRAPERS, SAVER_BATCH_SIZE, FILE_IO_BATCH_SIZE, MIN_SENTENCE_LENGTH, MAX_SENTENCE_LENGTH
from .dataclasses import Content, Metadata, Sentence

import asyncio
import re
from pydantic import ValidationError
import httpx
from bs4 import BeautifulSoup
from tqdm import tqdm
import gc
import xxhash
import datetime
import uuid
import codecs

# Web scraping and crawling. Text processing. Validation
#   Scraping is Asynchronous

# ScrapingPipeline acts as a wrapper, to run both Crawlers and Scrapers, with relevant methods for each forum
#   Extend the ScrapingPipeline to contain relevant methods for each forum

class ScrapingPipeline:
    def __init__(self, loader: Loader, manager: Manager, num_crawlers: int, num_scrapers: int, forum_origin: str, verbose: bool = False):
        self.forum_origin = forum_origin
        self.loader = loader
        self.manager = manager
        self.content_tbl = self.loader.connect(name=CONTENT_TBL_NAME)

        self.num_crawlers = num_crawlers
        self.num_scrapers = num_scrapers
        self.verbose = verbose

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
        await self.run_crawler(seeds=seeds, seed_queue=seed_queue, crawl_queue=crawl_queue)

        # scrape
        await self.run_scraper(crawl_queue=crawl_queue, save_queue=save_queue)


    # run crawler
    async def run_crawler(self, seeds: list[str], seed_queue: asyncio.Queue, crawl_queue: asyncio.Queue):
        crawler = Crawler(
            forum_origin=self.forum_origin,
            seeds=seeds,
            seed_queue=seed_queue,
            crawl_queue=crawl_queue,
            crawl_func=self.crawl, # subclasses own implementation
            NUM_CRAWLERS=self.num_crawlers
        )
        # populates mutable crawl queue as it runs
        await crawler.run_crawler(
            verbose=self.verbose
        )

    # run scraper
    async def run_scraper(self, crawl_queue: asyncio.Queue, save_queue: asyncio.Queue):
        scraper = Scraper(
            forum_origin=self.forum_origin,
            manager=self.manager,
            crawl_queue=crawl_queue,
            save_queue=save_queue,
            scrape_func=self.scrape,
            NUM_SCRAPERS=self.num_scrapers
        )
        await scraper.run_scraper(verbose=self.verbose)
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

    @classmethod
    def seed_generator(cls, prefix: str, start: int, stop: int, suffix: str) -> list[str]:
        return [str(prefix + str(i) + suffix) for i in range(start, stop + 1)]

    @classmethod
    def crawl(cls, soup):
        ...

    @classmethod
    def scrape(cls, soup, url, origin):
        ...



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
        try:
            while True:
                # get url
                url = await self.seed_queue.get()

                try:
                    # request page
                    soup = await ScrapingPipeline.request_page(url=url, client=self.client, verbose=verbose)
                    if not soup:
                        continue

                    # crawl page
                    # add to crawl queue
                    crawl_nodes: list[str] = self.crawl_func(soup=soup)
                    if not crawl_nodes: continue
                    elif len(crawl_nodes) == 0: continue
                    [self.crawl_queue.put_nowait(crawl_node) for crawl_node in crawl_nodes if crawl_node]
                except Exception as e:
                    if verbose:
                        print(f"Unknown parsing error at url: {url} -> {e}")
                finally:
                    # update
                    self.seed_queue.task_done()
                    self.pbar.update(1)
        except asyncio.CancelledError:
            return

# Scraper
#   Asynchronously scrape, error catch, deduplicate
class Scraper:
    def __init__(self, forum_origin: str, manager: Manager, crawl_queue: asyncio.Queue, save_queue: asyncio.Queue, scrape_func, NUM_SCRAPERS: int = NUM_SCRAPERS):
        self.forum_origin = forum_origin
        self.manager = manager
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
                workers = [tg.create_task(self.async_scraper(i, verbose=verbose)) for i in range(1, NUM_SCRAPERS + 1)]
                saver = tg.create_task(self.async_saver(SAVE_BATCH_SIZE=SAVER_BATCH_SIZE, verbose=verbose))

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
        try:
            while True:
                # pause to let saver work if necessary
                if self.save_queue.qsize() >= SAVER_BATCH_SIZE:
                    await asyncio.sleep(0) # let saver work

                # get url from crawl queue
                url: str = await self.crawl_queue.get()

                try:
                    # request page and add to save queue
                    soup = await ScrapingPipeline.request_page(url=url, client=self.client, verbose=verbose)
                    if not soup:
                        continue

                    contents: list[Content] = self.scrape_func(soup=soup, url=url, origin=self.forum_origin) # scrape function of scraping pipeline subclass
                    if not contents or len(contents) == 0:
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
        except asyncio.CancelledError:
            return
    
    # asyncrononous saver
    async def async_saver(self, SAVE_BATCH_SIZE: int = SAVER_BATCH_SIZE, verbose: bool = False):
        if verbose:
            print('Initializing saver')

        save_batch = []
        while True:
            # get data
            item = await self.save_queue.get()

            # check if sentinel value -> None
            if not item:
                self.deduplicate_save_batch(batch=save_batch)
                self.save_queue.task_done()
                break


            # add to save batch
            save_batch.append(item)
            self.save_queue.task_done()

            # if batch size met, save all and clear save batch
            if len(save_batch) >= SAVER_BATCH_SIZE:
                self.deduplicate_save_batch(batch=save_batch)

        # incase save batch not empty, save leftovers
        if len(save_batch) != 0:
            self.deduplicate_save_batch(batch=save_batch)

    def deduplicate_save_batch(self, batch: list[Content]) -> list[Content]:
        # in memory deduplication
        deduplicated_batch = list({content.hash_: content for content in batch}.values())

        # save deduplcation merge insert
        self.manager.deduplicate_insert(
            tbl_name=CONTENT_TBL_NAME,
            key="hash_",
            data=deduplicated_batch
        )

        batch.clear()
        gc.collect()

# class for processing and validating text
class Processor:
    def __init__(self, manager: Manager):
        self.manager = manager

    # split content into sentences
    #   update all relevant flags
    #   deduplicate and validate: remove usernames
    #   post process
    def run_processor(self, BATCH_SIZE: int = FILE_IO_BATCH_SIZE):
        # get usernames set
        metadata_dicts: list[str] = self.manager.retrieve_column_list(tbl_name=CONTENT_TBL_NAME, columns=['metadata_'])
        usernames: list[str] = [i['username'].lower() for i in metadata_dicts] # all in lowercase
        set().update(usernames) #usernames as set
        del metadata_dicts
        gc.collect()

        # load in batches: rows not already split
        #   split into sentences
        #   validate sentences
        current_save_batch = []
        for batch in self.manager.batch_generator(
            tbl_name=CONTENT_TBL_NAME,
            condition='is_split = false',
            columns=['text', 'uuid_', 'metadata_']
        ):
            batch_text = batch['text'].tolist()
            batch_uuids = batch['uuid_'].tolist()
            batch_metadata = batch['metadata_'].tolist()  # list of dicts

            for text, uid, metadata in zip(batch_text, batch_uuids, batch_metadata, strict=True):
                # split text
                sentences: list[str] = self.split_text(text)

                # validate sentences
                cleaned_sentences = self.process_sentences(sentences=sentences, usernames=usernames)

                # create sentence objects
                for clean_sentence in cleaned_sentences:
                    hash_ = xxhash.xxh64_hexdigest(clean_sentence)
                    uuid_ = str(uuid.uuid4())

                    sentence = Sentence(
                        uuid_=uuid_,
                        hash_=hash_,
                        content_uuid_=uid,
                        metadata_=metadata,
                        sentence=clean_sentence,
                        embedding=None,
                        reduced_embedding=None,
                        topic=None,
                        probabilities=None,
                        is_processed=True,
                    )
                    current_save_batch.append(sentence)

            # if batch size met, save
            if len(current_save_batch) >= FILE_IO_BATCH_SIZE:
                self.save_processed_content(
                    save_batch=current_save_batch
                )
                current_save_batch.clear()
                gc.collect()
        
        if len(current_save_batch) != 0:
            self.save_processed_content(
                save_batch=current_save_batch
            )
            current_save_batch.clear()
            gc.collect()

    # split text into sentences
    def split_text(self, text: str) -> list[str]:
        return [sentence.strip() for sentence in text.split(". ")]

    # process sentences
    #   remove if too short, too long, contains links, other data artifacts
    #   replace usernames with [USER]
    def process_sentences(self, sentences: list[str], usernames: set) -> list[str]:
        cleaned_sentences: list[str] = []
        at_removal_pattern = re.compile(r'@') # removing @'s
        word_pattern = re.compile(r'\b[\w\.-]+\b') # for removing usernames

        for sentence in sentences:
            if len(sentence) <= MIN_SENTENCE_LENGTH:
                continue
            elif len(sentence) >= MAX_SENTENCE_LENGTH:
                continue
            elif any(keyword in sentence for keyword in ['https', 'MemberPost']):
                continue
            elif "@" in sentence:
                sentence = at_removal_pattern.sub(' ', sentence)

            # replace username
            sentence = self.replace_username(text=sentence, word_pattern=word_pattern, usernames=usernames)
            cleaned_sentences.append(sentence)

        return cleaned_sentences

    # replace username with placeholder
    #   AI generated
    def replace_username(self, text: str, word_pattern, usernames: set, placeholder: str = '[USER]') -> str:
        return word_pattern.sub(
            lambda m: placeholder if m.group(0).lower() in usernames else m.group(0),
            text
        )

    # save processed content
    #   deduplication occurs by hash_
    def save_processed_content(self, save_batch: list[Sentence]):
        self.manager.deduplicate_insert(
            tbl_name=SENTENCE_TBL_NAME,
            key='hash_',
            data=save_batch
        )
        
    @classmethod
    def clean_text(cls, text=str) -> str:
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

# alzconnected specific scraping pipeline
class alzconnectedScrapingPipeline(ScrapingPipeline):
    def __init__(self, loader: Loader, manager: Manager, num_crawlers: int, num_scrapers: int, forum_origin: str, verbose: bool):
        super().__init__(loader=loader, manager=manager, num_crawlers=num_crawlers, num_scrapers=num_scrapers, forum_origin=forum_origin, verbose=verbose)

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

        parent_uuid: str = post.uuid_

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

        metadata = Metadata(
            url=url,
            date=date,
            date_accessed=date_accessed,
            forum_origin=origin,
            username=username,
            type_=content_type
        )

        # validate essentials (metadata + content)
        content: Content = Content(
            uuid_=my_uuid,
            parent_uuid_=uuid_parent,
            hash_=hash_,
            metadata_=metadata,
            title=title,
            text=content,
            is_processed=False,
            is_split=False
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
        date_accessed: str = str(datetime.date.today())
        my_uuid: str = str(uuid.uuid4())
        uuid_parent = parent_uuid
        content_type: str = 'comment'
        origin: str = origin

        metadata = Metadata(
            url=url,
            date=date,
            date_accessed=date_accessed,
            forum_origin=origin,
            username=username,
            type_=content_type
        )

        # validate essentials (metadata + content)
        content: Content = Content(
            uuid_=my_uuid,
            parent_uuid_=uuid_parent,
            hash_=hash_,
            metadata_=metadata,
            title=None,
            text=content,
            is_processed=False,
            is_split=False
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

# dementia support forum scraping pipeline
class dementiasupportforumScrapingPipeline(ScrapingPipeline):
    def __init__(self, loader: Loader, manager: Manager, num_crawlers: int, num_scrapers: int, forum_origin: str, verbose: bool):
        super().__init__(loader=loader, manager=manager, num_crawlers=num_crawlers, num_scrapers=num_scrapers, forum_origin=forum_origin, verbose=verbose)

    # crawl page
    @classmethod
    def crawl(cls, soup: BeautifulSoup) -> list[str]:
        links = set()
        list_a = soup.find_all('a')
        if not list_a: 
            return []
        for link in list_a:
            href = link.get('href')
            if not href: 
                continue
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

        parent_uuid: str = post.uuid_

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

        metadata = Metadata(
            url=url,
            date=date,
            date_accessed=date_accessed,
            forum_origin=origin,
            username=username,
            type_="post"
        )

        # validate essentials (metadata + content)
        content: Content = Content(
            uuid_=my_uuid,
            parent_uuid_=None,
            hash_=url_hash,
            metadata_=metadata,
            title=title,
            text=content,
            is_processed=False,
            is_split=False
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
        content_type: str = 'comment'
        origin: str = origin
        title = None

        metadata = Metadata(
            url=url,
            date=date,
            date_accessed=date_accessed,
            forum_origin=origin,
            username=username,
            type_=content_type
        )


        # validate essentials (metadata + content)
        content: Content = Content(
            uuid_=my_uuid,
            parent_uuid_=None,
            hash_=url_hash,
            metadata_=metadata,
            title=None,
            text=content,
            is_processed=False,
            is_split=False
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