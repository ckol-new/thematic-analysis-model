# scraping pipeline containing all classes and functions around scraping.
from thematic_analysis_model.model.util import *
from thematic_analysis_model.model.dclasses import *
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
import bs4 as soup
import requests
from pathlib import Path
import uuid
import re 

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
    def __init__(self, seeds: list[str], crawl_save_location: Path | str | None, save_scrape_output: Path | str | None, forum_origin: str = None):
        self.seeds = seeds
        self.crawl_save_location = crawl_save_location
        self.save_scrape_output = self.save_scrape_output
        self.crawl_output = self.run_crawler()
        self.forum_origin = forum_origin
        
        if crawl_save_location:
            self.save_crawl_output()
        
        if self.save_scrape_output: 
            self.save_scrape_output()
        
    # alternate constructor that does not run the pipeline automatically
    def __init__(self):
        self.seeds = None
        self.crawl_save_location = None
        self.crawl_output = None
        self.save_scrape_output = None
        self.forum_origin = None
        self.scrape_output = None
    
    # run_crawler method acts as 'queue' of all crawl operations to be performed on each 'seed' or start node
    # generate crawl output which is the list of all pages to be scraped from
    def run_crawler(self) -> list[str]:
        # iterate through seeds, to request each page html
        crawl_output = []

        for seed in self.seeds:
            output = self.crawl(seed)           
            crawl_output = crawl_output + output

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
    def run_scraper(self) -> list[Post] | None:
        scrape_output = []
        for crawl_seed in self.crawl_output:
            scraped_post: Post = self.scrape(crawl_seed)
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
        page_html = request_page(url)
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


        #   get author 
        #       get user name
        username = self.scrape_username(soup)       
        #       get user id
        userid = self.scrape_userid(soup)

        #   get comments: recursively call
        comments = self.scrape_comments(soup, url, self.forum_origin)

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
    # validate comment method
    def validate_comment(self, comment: Comment) -> bool:
        if len(comment.content) < 30: return False
        if not comment.metadata.url: return False
        if not comment.metadata.date: return False

        return True

    # abstract methods for getting each componenet of the post: implemented by each specific scraping pipeline
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

    # save scrape output 
    def save_scrape_output(self):
        # convert to list[str]

        smart_save(self.save_scrape_output, )



# ALZConnected.org specific scraping pipeline
class ALZConnectedScrapingPipeline(ScrapingPipeline):
    def __init__(self, seeds: list[str], crawl_save_location: Path | str | None, save_scrape_output: Path | str | None, forum_origin = 'alz_connected.org'):
        super().__init__(seeds, crawl_save_location, save_scrape_output forum_origin)
    def __init__(self):
        super().__init__()
        self.forum_origin = 'alz_connected.org'

    
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


    def scrape_title(self, soup: BeautifulSoup):
        title_text = soup.title.string
        title_text = title_text.removesuffix(' \u2014 ALZConnected') # '\u2014' is the em-dash escape key
        return title_text

    def scrape_content(self, soup: BeautifulSoup):
        div_discussion = soup.find('div', class_='Discussion') # discussion div
        div_content = div_discussion.find('div', class_='Message userContent') # get content out of discussion div
        if not div_content: return None 
        # get text and add separator for all separating elements in html
        content_unclean = div_content.get_text(separator=' ', strip=True)
        content_clean = re.sub(r'\s+', ' ', content_unclean) # remove additional white space
        #TODO clean unicode characters

        content_split = re.sub(r'\. ', '.\n', content_clean) # separate each sentence by period
        
        return content_split

    def scrape_date(self, soup: BeautifulSoup):
        div_date = soup.find('div', class_='Meta DiscussionMeta')       
        date = div_date.find('time').get('title')
        return date


    def scrape_username(self, soup: BeautifulSoup) -> str | None:
        div_author = soup.find('div', class_='AuthorWrap')
        username = div_author.find('a').text
        if not username: return None
        return username

    def scrape_userid(self, soup: BeautifulSoup) -> str | None:
        div_author = soup.find('div', class_='AuthorWrap')
        userid = div_author.find('a').get('data-userid')
        if not userid: return None
        return userid

    # scrape comments plural
    def scrape_comments(self, soup: BeautifulSoup, url: str, forum_origin: str) -> list[Comment] | None:
        # get list of soup objects for comments
        commentlist_div = soup.find('ul', class_='MessageList DataList Comments pageBox')
        # get each individual comment soup object from comment list
        comments_div: list = commentlist_div.find_all('div', class_='Comment')

        comments = []
        # for each comment; scrape data
        for comment_div in comments_div:
            comment = self.scrape_comment(comment_div, url, forum_origin)
            if comment:
                comments.append(comment)

        if not comments: return None
        return comments
            
    # scrape individual comment
    def scrape_comment(self, soup: BeautifulSoup, url: str, forum_origin: str) -> Comment | None:
        # get comment data
        content = self.scrape_comment_content(soup)
        date = self.scrape_comment_date(soup)
        username = self.scrape_comment_author_username(soup)
        userid = self.scrape_comment_author_userid(soup)
        author = Author(username, userid)
        my_uuid = str(uuid.uuid4())
        metadata = Metadata(my_uuid, author, url, date, forum_origin)
        #TODO figure out how to handle sub-comments of comments
        comment = Comment(content, metadata, None) 

        # validate comment
        if not self.validate_comment(comment): return None
        return comment
    
    # scrape content of comment, and do some initial cleaning of text
    def scrape_comment_content(self, soup: BeautifulSoup) -> str | None:
        div_content = soup.find('div', class_='Message userContent') # get content out of discussion div
        if not div_content: return None 
        # get text and add separator for all separating elements in html
        content_unclean = div_content.get_text(separator=' ', strip=True)
        if not content_unclean: return None

        content_clean = re.sub(r'\s+', ' ', content_unclean) # remove additional white space
        #TODO clean unicode characters
        content_split = re.sub(r'\. ', '.\n', content_clean) # separate each sentence by period

        return content_split
    def scrape_comment_date(self, soup: BeautifulSoup) -> str | None:
        date = soup.find('time').get('title')
        if not date: return None
        return date
    def scrape_comment_author_username(self, soup: BeautifulSoup) -> str | None:
        div_author = soup.find('div', class_='AuthorWrap')
        username = div_author.find('a').text
        if not username: return None
        return username
    def scrape_comment_author_userid(self, soup: BeautifulSoup) -> str | None:
        div_author = soup.find('div', class_='AuthorWrap')
        userid = div_author.find('a').get('data-userid')
        if not userid: return None
        return userid
