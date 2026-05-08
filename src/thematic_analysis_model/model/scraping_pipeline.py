# scraping pipeline containing all classes and functions around scraping.
from abc import ABC, abstractmethod

# UTILITY functions

# seed generator utility helps speed up process of generating seeds, which act as start nodes for the crawler to branch out from.
def generate_seeds(base: str, start: int, stop: int, end_seq: str) -> list[str]:
    seeds: list = []

    for i in range(start, stop + 1):
        seed: str = base + f'{i}' + end_seq
        seeds.append(seed)   

    return seeds

# save seed output enables documentation of every seed scraped from
# note it appends, not writes
def save_seeds(seeds: list[str], location: str):
    with open(location, 'a') as f:
        for seed in seeds:
            f.append(seed)
# read seed method is opposite, generates list of seeds from seed file
def read_seeds(location: str, limit: int = None) -> list[str] | None:
    seeds = None
    i = 0
    with open(location, 'r') as f:
        if not limit:
            seeds = f.readlines()
        else:
            while i <= limit:
                seeds.append(f.readline())
                i += 1
    
    return seeds



# abstract scraping pipeline class: because each forum has unique html structure, and scraping rules, it needs its own implementation of this class
class ScrapingPipeline(ABC):
    # general pipeline operation goes as follows: *save seeds -> crawl -> *save crawl output -> scrape -> save scrape output
    def __init__(self, seeds: list[str]):

        if self.save_seeds_location:

    
    # run_crawler method acts as 'queue' of all crawl operations to be performed on each 'seed' or start node
    # generate crawl output which is the list of all pages to be scraped from
    def run_crawler(self) -> list[str]:
        ...

    # crawl method is specific to each forum
    @abstractmethod
    def crawl(self, seed:str):
        ...

    # save crawl output enables docuemntation of every website scraped
    # parameterized, so it can be optionally ran
    def save_crawl_output(self):
        ...

    # run scraper method acts as 'queue', running many scraping operations for every link in the crawl output
    def run_scraper(self):
        ...

    # scrape is a single scraping operation for a single link. It corresponds to the scraping of one single forum post.
    # is unique to each forum.
    @abstractmethod
    def scrape(self):
        ...

    # save scrape output 
    def save_scrape_output(self):
        ...
    


