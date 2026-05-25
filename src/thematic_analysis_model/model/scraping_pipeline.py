from lancedb import Table
import regex as re
import codecs
import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from .dclasses import Content, Metadata, Author
from uuid import uuid4
from pathlib import Path
import datetime


class ScrapingPipeline(ABC):
    def __init__(self):
        ...
    
    # main pipeline methods, to abstract pipeline execution process for user
    def run_pipeline(self, table: Table, seeds: list[str], crawl_save_location: Path | None = None, origin: str = None, BATCH_SIZE: int = 10000):
        # for each seed, crawl all possible posts
        crawl_output = self.run_crawler(seeds, crawl_save_location)
        # scrape
        self.run_scraper(table, crawl_output, origin, BATCH_SIZE)
        ...

    
    def run_crawler(self, seeds: list[str], save_location: Path | None = None) -> list[str]:
        # for seed in seed
            # get page
            # get outgoing connections to posts
        crawl_output: list[str] = []
        for seed in seeds:
            soup: BeautifulSoup = ScrapingPipeline.request_page(seed)
            crawl_output.append(self.crawl_page(soup))

        # optionally save
        if self.save_seeds:
            with save_location.open('w', encoding='utf-8') as f:
                f.writelines(line + '\n' for line in crawl_output)
        
        return crawl_output

    # scrape and save to db
    def run_scraper(self, table: Table, crawl_output: list[str], origin: str, BATCH_SIZE: int =10000):
        # for crawl node
        scraped_content: list[Content] = []
        for crawl_node in crawl_output:
            content: list[Content] = self.scrape(crawl_node, origin)
            scraped_content.append(content)


            # if buffer fills, save to lancedb, empty, continue
            if len(scraped_content) >= BATCH_SIZE:
                ScrapingPipeline.save_to_db(table, scraped_content)
                scraped_content = [] 

        # save to lancedb
        if len(scraped_content) != 0:
                ScrapingPipeline.save_to_db(table, scraped_content)
                scraped_content = [] 

    # returns list of content posts/comments on page
    def scrape(self, url: str, origin: str) -> list[Content]:
        # get page
        soup: BeautifulSoup = ScrapingPipeline.request_page(url)

        # scrape metadata
        post_author: Author = Author(
            username=self.scrape_username(soup),
            userid=self.scrape_id(soup)
        )
        post_metadata: Metadata = Metadata(
            url=url,
            uuid=str(uuid4()),
            url_hash=hash(url),
            date=self.scrape_date(soup),
            date_accessed=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            author=post_author,
            origin=origin
        )

        # scrape post
        post: Content = Content(
            metadata=post_metadata,
            content=self.scrape_post_content(soup),
            title=self.scrape_title(soup),
            content_type='post'
        )


        # scrape comment(s)
        comments: list[Content] = self.scrape_comments(soup)

        # validate post
        if not ScrapingPipeline.validate_content(post):
            scraped_content: list[Content] = comments
            return scraped_content
        
        scraped_content: list[Content] = post + comments
        return scraped_content

    # CLASS METHODS
    
    # methods for saving and loading seeds from file, note that the seeds must common from same forum
    @classmethod
    def generate_seeds(cls, prefix: str, start: int, end: int, suffix: str):
        seeds: list[str] = []
        for i in range(start, end + 1):
            seeds.append(prefix + str(i) + suffix)

        return seeds

    @classmethod
    def save_seeds(cls, seeds: list[str],  save_location: Path):
        with save_location.open('w', encoding='utf-8') as f:
            f.writelines(line + '\n' for line in seeds)

    @classmethod 
    def load_seeds(cls, save_location: Path) -> list[str]:
        seeds: list[str] = []
        with save_location.open('r', encoding='utf-8') as f:
            seeds.append(f.readlines())
        return seeds

    # save/load crawl output, does not have to be from the same forum
    @classmethod
    def save_crawl_output(cls, crawl_output: list[str], save_location: Path):
        with save_location.open('w', encoding='utf-8') as f:
            f.writelines(line + '\n' for line in crawl_output)

    @classmethod
    def load_crawl_output(cls, save_location: Path) -> list[str]:
        arr: list[str] = []
        with save_location.open('r', encoding='utf-8') as f:
            arr.append(f.readlines())
        return arr

    @classmethod
    def save_to_db(cls, table: Table, content: list[Content]):
        table.add(content)

    # method requests page, returns error if not working
    # return soup obj
    @classmethod
    def request_page(cls, url: str, header: dict) -> BeautifulSoup:
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

    @classmethod
    def validate_content(cls, content: Content) -> bool:
        if not content.content: return False
        if len(content.content) < 30: return False
        if not content.metadata.url: return False
        if not content.metadata.url_hash: return False
        if not content.metadata.date: return False
        if not content.metadata.date_accessed: return False

        return True

    @classmethod
    def clean_text(cls) -> str:
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


    # abstract methods, to be implemented by subclasses, enforce contract
    @abstractmethod
    def crawl_page(self, soup: BeautifulSoup) -> list[str]:
        ...

    @abstractmethod
    def scrape_post(self, soup: BeautifulSoup) -> Content:
        ...

    @abstractmethod
    def scrape_date(self, soup: BeautifulSoup) -> str:
        ...

    @abstractmethod
    def scrape_title(self, soup: BeautifulSoup) -> str:
        ...

    @abstractmethod
    def scrape_post_content(self, soup: BeautifulSoup) -> str:
        ...

    @abstractmethod
    def scrape_comment_content(self, soup: BeautifulSoup) -> str:
        ...

    @abstractmethod
    def scrape_username(self, soup: BeautifulSoup) -> str:
        ...

    @abstractmethod
    def scrape_userid(self, soup: BeautifulSoup) -> str:
        ...

    @abstractmethod
    def scrape_comments(self, soup: BeautifulSoup) -> list[Content]:
        ...

    @abstractmethod
    def scrape_comment(self, soup: BeautifulSoup) -> Content:
        ...

    

class ALZConnectedScrapingPipeline(ScrapingPipeline):
    def __init__(self):
        super().__init__()

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
        content_unclean = re.sub(r'\s+', ' ', content_unclean) # remove additional white space
        #TODO clean unicode characters
        decoded_text = ScrapingPipeline.clean_text(content_unclean)

        content_split = re.sub(r'\. ', '.\n', decoded_text) # separate each sentence by period
        
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
    def scrape_comments(self, soup: BeautifulSoup, url: str, forum_origin: str) -> list[Content] | None:
        # get list of soup objects for comments
        commentlist_div = soup.find('ul', class_='MessageList DataList Comments pageBox')
        # get each individual comment soup object from comment list
        if not commentlist_div: return None
        comments_div: list = commentlist_div.find_all('div', class_='Comment')

        comments: list[Content] = []
        # for each comment; scrape data
        for comment_div in comments_div:
            comment: Content = self.scrape_comment(comment_div, url, forum_origin)
            if comment:
                comments.append(comment)

        if not comments: return None
        return comments
            
    # scrape individual comment
    def scrape_comment(self, soup: BeautifulSoup, url: str, forum_origin: str) -> Content | None:
        author = Author(
            username=self.scrape_username(soup),
            userid=self.scrape_userid(soup)
        )
        metadata = Metadata(
            url=url,
            uuid=str(uuid4()),
            url_hash=hash(url),
            date=self.scrape_date(soup),
            date_accessed=datetime.dateime.now().strftime('%Y-%m-%d %H:%M:%S'),
            author=Author,
            origin=forum_origin
        )
        comment: Content = Content(
            metadata=metadata,
            content=self.scrape_content(soup),
            title=None,
            content_type='comment'
        )
        if ScrapingPipeline.validate_content(comment): return comment
        else: return None
    
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