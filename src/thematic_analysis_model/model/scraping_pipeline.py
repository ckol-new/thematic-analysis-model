from thematic_analysis_model.model.dclasses import *
from thematic_analysis_model.model.util import *
from abc import ABC, abstractmethod
import codecs
import requests
import datetime
from bs4 import BeautifulSoup
import uuid

# UTILITY functions
# seed generator utility helps speed up process of generating seeds, which act as start nodes for the crawler to branch out from.
def generate_seeds(base: str, start: int, stop: int, end_seq: str) -> list[str]:
    seeds: list = []

    for i in range(start, stop + 1):
        seed: str = base + f'{i}' + end_seq
        seeds.append(seed)   

    return seeds

# can instantiate the scraping pipeline to be empty, however it will not run. It is on the user to ensure all data is prewsent to allow scraping pipeline to run.
class ScrapingPipeline(ABC):
    def __init__(self, seeds: list[str] | None = None, crawl_save_location: Path | None = None, scrape_save_location: Path | None = None, forum_origin: str | None = None):
        self.seeds = seeds
        self.crawl_save_location = crawl_save_location
        self.scrape_save_location = scrape_save_location
        self.forum_origin = forum_origin
        self.crawl_output = None
        self.scrape_output = None
        

    # main methods

    # run pipeline method
    def run_pipeline(self):
        # run crawler
        print('RUNNING CRAWLER')
        self.crawl_output = self.run_crawler()

        # optionally save scrape output
        if self.crawl_save_location: 
            self.save_crawl_output()

        print("RUNNING SCRAPER")
        # run scraper
        self.scrape_output = self.run_scraper()

        # optionally save scrape output
        if self.scrape_save_location: 
            self.save_scrape_output()

    # run_crawler method acts as 'queue' of all crawl operations to be performed on each 'seed' or start node
    # generate crawl output which is the list of all pages to be scraped from
    def run_crawler(self) -> list[str]:
        # iterate through seeds, to request each page html
        crawl_output = []

        for seed in self.seeds:
            output = self.crawl(seed)           
            crawl_output = crawl_output + output

        return crawl_output
    
    # run scraper method acts as 'queue', running many scraping operations for every link in the crawl output
    def run_scraper(self) -> list[Post] | None:
        scrape_output = []
        count = 0
        total = len(self.crawl_output)
        for crawl_seed in self.crawl_output:
            count += 1
            if count % 10 == 0:
                print(f'% {100*(count / total)} finished')
            try:
                scraped_post: Post = self.scrape(crawl_seed)
            except Exception as e:
                print(f'ran into issue at {crawl_seed} exception: {e}')
            # validation step
            if not self.validate_post(scraped_post): continue
            scrape_output.append(scraped_post)
        
        if not scrape_output: return None
        return scrape_output

      # scrape is a single scraping operation for a single link. It corresponds to the scraping of one single forum post.
    # is unique to each forum.
    def scrape(self, url: str) -> Post | None:
        # get page
        #TODO implement customization of header
        page_html = ScrapingPipeline.request_page(url)
        # get soup object
        soup = BeautifulSoup(page_html, 'html.parser')
        
        # get title
        title = self.scrape_title(soup)

        # get content
        content = self.scrape_content(soup)

        # get metadata
        # get unique id
        my_uuid = str(uuid.uuid4())

        #   get date
        date = self.scrape_date(soup)
        # get date accessed
        now = datetime.now()
        date_accessed = now.strftime("%Y-%m-%d %H:%M:%S")

        #   get author 
        #       get user name
        username = self.scrape_username(soup)       
        #       get user id
        userid = self.scrape_userid(soup)

        #   get comments: recursively call
        comments = self.scrape_comments(soup, url, self.forum_origin)

        # create objects, must package comments inside post object
        author = Author(username, userid)
        metadata = Metadata(my_uuid, author, url, date, self.forum_origin, str(date_accessed))
        post = Post(metadata, content, title, comments)

        return post


    # file i/o for seeds
    @classmethod
    def save_seeds(cls, seeds: list[str], fpath: Path):
        save_text(fpath, seeds)
    @classmethod
    def load_seeds(cls, fpath: Path) -> list[str]:
        return load_text(fpath)

    # file i/o for crawl output
    @classmethod
    def save_crawl_output(cls, crawl_output: list[str], fpath: Path):
        save_text(fpath=fpath, arr=crawl_output)
    @classmethod
    def load_crawl_output(cls, fpath) -> list[str]:
        return load_text(fpath)

    # file i/o for scrape output
    def save_scrape_output(cls, scrape_output: list[Post], fpath: Path):
        save_dclasses(file_path=fpath, cls=Post, dclasses=scrape_output)
    # NOT MEMORY EFFICIENT
    @classmethod
    def load_scrape_output(cls, fpath: Path) -> list[Post]:
        return load_dclasses(file_path=fpath, cls=Post)
    

    # request page
    # returns html of page as string
    # optionally pass in header, otherwise it uses default
    @classmethod
    def request_page(cls, url: str, header: dict = None) -> str:
        if not header:
            header = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        try:
            response = requests.get(url, headers=header)
            if response.status_code == 200:
                ...
            else: print(f'REQUEST FAILED for {url}: ', response.status_code)

            html_text = response.text
            response.close() # close connection to server I think

            return html_text

        except requests.exceptions.RequestException as e:
            raise Exception(e)
    
    # method for processing text, and removing escape characterws
     # pre-process text
    @classmethod
    def process_text(cls, text):
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

     # method validates post returning true if valid, false if not
    @classmethod
    def validate_post(self, post: Post) -> bool:
        # check post length (minimum characters)
        # check post title
        # check post meta data (*must have url, date, author?)
        #TODO implement duplicate checking

        if len(post.content) < 30: return False
        if not post.title: return False
        if not post.metadata.url: return False
        if not post.metadata.date: return False
        if not post.metadata.uuid: return False
        if not post.metadata.date_accessed: return False

        return True

    # validate comment method
    @classmethod
    def validate_comment(self, comment: Comment) -> bool:
        if len(comment.content) < 30: return False
        if not comment.metadata.url: return False
        if not comment.metadata.date: return False
        if not comment.metadata.uuid: return False
        if not comment.metadata.date_accessed: return False

        return True

    
    # abstract methods for getting each componenet of the post: implemented by each specific scraping pipeline

    # crawl method is specific to each forum
    @abstractmethod
    def crawl(self, seed:str) -> list[str] | None:
        ...
    @abstractmethod
    def scrape_title(self, soup):
        ...
    # content will be stored as a string with newline characters separating sentences
    @abstractmethod
    def scrape_content(self, soup):
        ...
    @abstractmethod
    def scrape_date(self, soup):
        ...
    @abstractmethod
    def scrape_username(self, soup):
        ...
    @abstractmethod
    def scrape_userid(self, soup):
        ...
    # scrape comments plural
    #   must be able to return None if necessary
    @abstractmethod
    def scrape_comments(self, soup: BeautifulSoup, url: str, forum_origin: str) -> list[Comment] | None:
        ...
