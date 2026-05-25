from lancedb import Table
import regex as re
import codecs
import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from  thematic_analysis_model.model.dclasses import Content, Metadata, Author
from uuid import uuid4
from pathlib import Path
import datetime


class ScrapingPipeline(ABC):
    def __init__(self):
        ...
    
    # main pipeline methods, to abstract pipeline execution process for user
    def run_pipeline(self, table: Table, seeds: list[str], crawl_save_location: Path | None = None, origin: str = None, BATCH_SIZE: int = 10000, header: dict = None):
        # update count to current table length

        # for each seed, crawl all possible posts
        crawl_output = self.run_crawler(seeds, crawl_save_location)
        # scrape

        self.run_scraper(table, crawl_output, origin, BATCH_SIZE)
        ...
    
    def run_crawler(self, seeds: list[str], save_location: Path | None = None, header: dict = None) -> list[str]:
        # for seed in seed
            # get page
            # get outgoing connections to posts
        crawl_output: list[str] = []
        for seed in seeds:
            soup: BeautifulSoup = ScrapingPipeline.request_page(seed, header)
            crawl_output = crawl_output + self.crawl_page(soup)

        # optionally save
        if save_location:
            with save_location.open('w', encoding='utf-8') as f:
                f.writelines(line + '\n' for line in crawl_output)
        
        return crawl_output

    # scrape and save to db
    def run_scraper(self, table: Table, crawl_output: list[str], origin: str, BATCH_SIZE: int =10000, header: dict = None):
        # for crawl node
        scraped_content: list[Content] = []

        total = len(crawl_output)
        count = 0
        for crawl_node in crawl_output:
            count += 1
            if count % 100 == 0:
                print(f'scraped %{(count / total) * 100} finished')

            content: list[Content] = self.scrape(crawl_node, origin)
            if not content: continue
            scraped_content = scraped_content + content


            # if buffer fills, save to lancedb, empty, continue
            if len(scraped_content) >= BATCH_SIZE:
                ScrapingPipeline.save_to_db(table, scraped_content)
                scraped_content = [] 

        # save to lancedb
        if len(scraped_content) != 0:
                ScrapingPipeline.save_to_db(table, scraped_content)
                scraped_content = [] 

    # returns list of content posts/comments on page
    def scrape(self, url: str, origin: str, header: dict = None) -> list[Content] | None:
        # get page
        soup: BeautifulSoup = ScrapingPipeline.request_page(url, header)
        if not soup: return None
        discussion_div = soup.find('div', 'Discussion')
        if not discussion_div: return None

        # scrape metadata
        post_author: Author = Author(
            username=self.scrape_username(discussion_div),
            userid=self.scrape_userid(discussion_div)
        )
        post_metadata: Metadata = Metadata(
            url=url,
            uuid=str(uuid4()),
            url_hash=str(hash(url)),
            date=self.scrape_date(discussion_div),
            date_accessed=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            author=post_author,
            origin=origin
        )

        # scrape post
        post: Content = Content(
            metadata=post_metadata,
            content=self.scrape_content(discussion_div),
            title=self.scrape_title(soup),
            content_type='post',
            is_split=False
        )
        # scrape comment(s)
        comments: list[Content] = self.scrape_comments(soup, url, origin)

        if not post:
            post = []
        elif not self.validate_content(post):
            post = []
        else:
            post = [post]
        if not comments:
            comments = []
        
        content: list[Content] = post + comments
        return content



    # CLASS METHODS
    
    # methods for saving and loading seeds from file, note that the seeds must common from same forum
    @classmethod
    def generate_seeds(cls, prefix: str, start: int, end: int, suffix: str):
        seeds: list[str] = []
        for i in range(start, end + 1):
            seed: str = prefix + f'{i}' + suffix
            seeds.append(seed)
        return seeds

    @classmethod
    def save_seeds(cls, seeds: list[str],  save_location: Path):
        with save_location.open('w', encoding='utf-8') as f:
            f.writelines(line + '\n' for line in seeds)

    @classmethod 
    def load_seeds(cls, save_location: Path) -> list[str]:
        seeds: list[str] = []
        with save_location.open('r', encoding='utf-8') as f:
            seeds = f.readlines()
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
            arr = f.readlines()
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

            soup = BeautifulSoup(html_text, 'html.parser')
            return soup
        except requests.exceptions.RequestException as e:
            return None

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


    # abstract methods, to be implemented by subclasses, enforce contract
    @abstractmethod
    def crawl_page(self, soup: BeautifulSoup) -> list[str]:
        ...

    @abstractmethod
    def scrape_date(self, soup: BeautifulSoup) -> str:
        ...

    @abstractmethod
    def scrape_title(self, soup: BeautifulSoup) -> str:
        ...

    @abstractmethod
    def scrape_content(self, soup: BeautifulSoup) -> str:
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


    def crawl_page(self, soup: BeautifulSoup):
        links = set()
        for link in soup.find_all('a'):
            href = link.get('href')
            if '/discussion/' in href:
                links.add(href)
        return list(links)

    def scrape_date(self, soup: BeautifulSoup) -> str:
        time_div = soup.find('time')
        if not time_div: return None
        date = time_div.get('title')
        if not date: return None
        return str(date)

    def scrape_title(self, soup: BeautifulSoup):
        title_text = soup.title.string
        title_text = title_text.removesuffix(' \u2014 ALZConnected') # '\u2014' is the em-dash escape key
        return title_text

    def scrape_content(self, soup: BeautifulSoup) -> str:
        div_content = soup.find('div', class_='Message userContent') # get content out of discussion div
        if not div_content: return None 
        # get text and add separator for all separating elements in html
        content_unclean = div_content.get_text(separator=' ', strip=True)
        if not content_unclean: return None
        content_clean = re.sub(r'\s+', ' ', content_unclean) # remove additional white space
        #TODO clean unicode characters
        content_split = re.sub(r'\. ', '.\n', content_clean) # separate each sentence by period
        return content_split

    def scrape_username(self, soup: BeautifulSoup) -> str | None:
        username_div = soup.find('a', class_='Username js-userCard')
        if not username_div:
            return None
        username = username_div.text
        if not username: return None
        return str(username)

    def scrape_userid(self, soup: BeautifulSoup) -> str:
        userid_div = soup.find('a', class_='Username js-userCard')
        if not userid_div: return None
        userid = userid_div.get('data-userid')
        if not userid: return None
        return str(userid)

    def scrape_comments(self, soup: BeautifulSoup, url: str, origin: str) -> list[Content] | None:
        comment_list_div = soup.find('ul', class_='MessageList DataList Comments pageBox')
        if not comment_list_div: return None

        comments: list[Content] = []
        for comment_div in comment_list_div.find_all('div', class_='Comment'):
            comment: Content = self.scrape_comment(comment_div, url, origin)
            # if invalid, none, do not add
            if not comment: continue
            if not ScrapingPipeline.validate_content(comment): continue
            comments.append(comment)
        
        if len(comments) == 0: return None
        return comments

    def scrape_comment(self, soup: BeautifulSoup, url: str, origin: str) -> Content | None:
        author: Author = Author(
            username= self.scrape_username(soup),
            userid= self.scrape_userid(soup)
        )
        metadata: Metadata = Metadata(
            url=url,
            uuid=str(uuid4()),
            url_hash=str(hash(url)),
            date=self.scrape_date(soup),
            date_accessed=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            author=author,
            origin=origin
        )
        comment: Content = Content(
            metadata=metadata,
            content=self.scrape_content(soup),
            title=None,
            content_type='comment',
            is_split=False
        )

        return comment