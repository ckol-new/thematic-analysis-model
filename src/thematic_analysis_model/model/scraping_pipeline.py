from thematic_analysis_model.model.dclasses import *
from thematic_analysis_model.model.util import *
from abc import ABC, abstractmethod
import codecs

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