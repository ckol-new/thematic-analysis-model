from thematic_analysis_model.model.dclasses import *
from thematic_analysis_model.model.util import *
from abc import ABC, abstractmethod
import codecs
import requests

# UTILITY functions
# seed generator utility helps speed up process of generating seeds, which act as start nodes for the crawler to branch out from.
def generate_seeds(base: str, start: int, stop: int, end_seq: str) -> list[str]:
    seeds: list = []

    for i in range(start, stop + 1):
        seed: str = base + f'{i}' + end_seq
        seeds.append(seed)   

    return seeds

class ScrapingPipeline(ABC):
    def __init__(self):
        ...

    # main methods

    # run_crawler method acts as 'queue' of all crawl operations to be performed on each 'seed' or start node
    # generate crawl output which is the list of all pages to be scraped from
    def run_crawler(self) -> list[str]:
        # iterate through seeds, to request each page html
        crawl_output = []

        for seed in self.seeds:
            output = self.crawl(seed)           
            crawl_output = crawl_output + output

        return crawl_output


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
