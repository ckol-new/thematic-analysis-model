# scraping pipeline containing all classes and functions around scraping.
from thematic_analysis_model.model.util import *
from thematic_analysis_model.model.dclasses import *
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import requests
from pathlib import Path
import uuid

# UTILITY functions
# seed generator utility helps speed up process of generating seeds, which act as start nodes for the crawler to branch out from.
def generate_seeds(base: str, start: int, stop: int, end_seq: str) -> list[str]:
    seeds: list = []

    for i in range(start, stop + 1):
        seed: str = base + f'{i}' + end_seq
        seeds.append(seed)   

    return seeds

# save seeds
def save_seeds(location: Path | str, seeds: list[str]):
    seed_str = '\n'.join(seeds)
    smart_save(location=location, data=seed_str, format_type='txt')

# read seed method is opposite, generates list of seeds from seed file
def read_seeds(location: Path) -> list[str] | None:
    seeds_str = smart_load(location=location)
    seeds = seeds_str.splitlines()
    return seeds

# request page
# returns html of page as string
# optionally pass in header, otherwise it uses default
def request_page(url: str, header: dict = None) -> str:
    if not header:
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    try:
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            ...
        else: print('REQUEST FAILED: ', response.status_code)

        html_text = response.text
        response.close() # close connection to server I think

        return html_text

    except requests.exceptions.RequestException as e:
        raise Exception(e)

# abstract scraping pipeline class: because each forum has unique html structure, and scraping rules, it needs its own implementation of this class
class ScrapingPipeline(ABC):
    # general pipeline operation goes as follows: *save seeds -> crawl -> *save crawl output -> scrape -> save scrape output
    # forum origin parameter is the origin the forum that is being scraped form
    def __init__(self, seeds: list[str], crawl_save_location: Path | str | None, forum_origin: str = None):
        self.seeds = seeds
        self.crawl_save_location = crawl_save_location
        self.crawl_output = self.run_crawler()
        self.forum_origin = forum_origin
        
        if crawl_save_location:
            self.save_crawl_output()
    
    # run_crawler method acts as 'queue' of all crawl operations to be performed on each 'seed' or start node
    # generate crawl output which is the list of all pages to be scraped from
    def run_crawler(self) -> list[str]:
        # iterate through seeds, to request each page html
        crawl_output = set()

        for seed in self.seeds:
            output = self.crawl(seed)           
            crawl_output.update(output)

        return crawl_output

    # crawl method is specific to each forum
    @abstractmethod
    def crawl(self, seed:str) -> set[str] | None:
        ...

    # save crawl output enables docuemntation of every website scraped
    # parameterized, so it can be optionally ran
    def save_crawl_output(self):
        crawl_output_str = '\n'.join(self.crawl_output)
        smart_save(self.crawl_save_location, data = crawl_output_str, format_type='txt')

    # run scraper method acts as 'queue', running many scraping operations for every link in the crawl output
    def run_scraper(self):
        scrape_output = set() 
        for crawl_seed in self.crawl_output:
            scraped_post: Post = self.scrape(crawl_seed)
            # validation step
            if not self.validate_post(scraped_post): continue
            scrape_output.add(scraped_post())

    # scrape is a single scraping operation for a single link. It corresponds to the scraping of one single forum post.
    # is unique to each forum.
    def scrape(self, url: str) -> Post | None:
        # get page
        #TODO implement customization of header
        page_html = request_page(url)
        
        # get title
        title = self.scrape_title()

        # get content
        content = self.scrape_content()

        # get metadata
        # get unique id
        my_uuid = uuid.uuid4()

        #   get date
        date = self.scrape_date()


        #   get author 
        #       get user name
        username = self.scrape_username()       
        #       get user id
        userid = self.scrape_userid()

        #   get comments: recursively call
        comments = self.scrape_comments()

        # create objects, must package comments inside post object
        author = Author(username, userid)
        metadata = Metadata(my_uuid, author, url, date, self.forum_origin)
        post = Post(content, metadata, title, comments)

        return post

    
    # method validates post returning true if valid, false if not
    def validate_post(self, post: Post) -> bool:
        # check post length (minimum characters)
        # check post title
        # check post meta data (*must have url, date, author?)
        #TODO implement duplicate checking

        if len(post.content) < 30: return False
        if not post.title: return False
        if not post.metadata.url: return False
        if not post.metadata.date: return False

        return True


    # abstract methods for getting each componenet of the post: implemented by each specific scraping pipeline
    @abstractmethod
    def scrape_title(self):
        ...
    @abstractmethod
    def scrape_content(self):
        ...
    @abstractmethod
    def scrape_date(self):
        ...
    @abstractmethod
    def scrape_username(self):
        ...
    @abstractmethod
    def scrape_userid(self):
        ...
    # scrape comments plural
    #   must be able to return None if necessary
    @abstractmethod
    def scrape_comments(self):
        @abstractmethod
        def scrape_comment(self):
            ...
        ...
    

    # save scrape output 
    def save_scrape_output(self):
        ...



# ALZConnected.org specific scraping pipeline
class ALZConnectedScrapingPipeline(ScrapingPipeline):
    def __init__(self, seeds: list[str], crawl_save_location: Path | str | None, forum_origin = 'alz_connected.org'):
        super().__init__(seeds, crawl_save_location, forum_origin)

    
    # implement crawl indivudal page method
    def crawl(self, url: str) -> set[str] | None:
        html = request_page(url)
        if not html: return None

        soup = BeautifulSoup(html, 'html.parser')
        links = set()

        for link in soup.find_all('a'):
            href = link.get('href')
            if '/discussion/' in href:
                links.add(href)

        return links


    def scrape_title(self):
        ...
    def scrape_content(self):
        ...
    def scrape_date(self):
        ...
    def scrape_username(self):
        ...
    def scrape_userid(self):
        ...
    # scrape comments plural
    def scrape_comments(self):
        def scrape_comment(self):
            ...
        ...
    
