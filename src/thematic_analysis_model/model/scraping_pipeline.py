from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from .dclasses import Content, Metadata, Author


class ScrapingPipeline(ABC):
    def __init__(self):
        ...
    
    # main pipeline methods, to abstract pipeline execution process for user
    def run_pipeline(self):
        # for each seed, crawl all possible posts

        # for each crawl output, scrape post

        # save posts to lancedb, as batch fills
        ...

    
    def run_crawler(self):
        # for seed in seed
            # get page
            # get outgoing connections to posts
        
        # optionally save
        ...

    def run_scraper(self):
        # for crawl node

            # if buffer fills, save to lancedb, continue

        # save to lancedb
        ...

    # returns list of content posts/comments on page
    def scrape(self, url: str) -> list[Content]:
        # get page
        soup = self.request_page(url)

        # scrape metadata

        # scrape post
        # scrape comment(s)

        # form pydantic dataclass obj
        ...


    # CLASS METHODS
    
    # methods for saving and loading seeds from file, note that the seeds must common from same forum
    @classmethod
    def generate_seeds(self):
        ...
    @classmethod
    def save_seeds(self):
        ...
    @classmethod 
    def load_seeds(self) -> list[str]:
        ...

    # save/load crawl output, does not have to be from the same forum
    @classmethod
    def save_crawl_output(self):
        ...
    @classmethod
    def load_crawl_output(self) -> list[str]:
        ...

    # method requests page, returns error if not working
    # return soup obj
    @classmethod
    def request_page(self) -> BeautifulSoup:
        ...

    @classmethod
    def validate_content(self) -> bool:
        ...

    @classmethod
    def clean_text(self) -> bool:
        ...

    # abstract methods, to be implemented by subclasses, enforce contract
    @abstractmethod
    def scrape_post(self) -> Content:
        ...

    @abstractmethod
    def scrape_date(self) -> str:
        ...

    @abstractmethod
    def scrape_title(self) -> str:
        ...

    @abstractmethod
    def scrape_content(self) -> str:
        ...

    @abstractmethod
    def scrape_username(self) -> str:
        ...

    @abstractmethod
    def scrape_userid(self) -> str:
        ...

    @abstractmethod
    def scrape_comment(self) -> Content:
        ...

    