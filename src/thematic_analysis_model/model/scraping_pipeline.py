from thematic_analysis_model.model.dclasses import *
from thematic_analysis_model.model.util import *
from abc import ABC, abstractmethod

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
    