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

    @classmethod
    def save_seeds(cls, seeds: list[str], fpath: Path):
        with fpath.open('w', encoding='utf-8') as f:
            for seed in seeds:
                f.write(seed.strip() + '\n')

    @classmethod
    def load_seeds(cls, fpath: Path) -> list[str]:
        seeds: list[str] = []
        with fpath.open('r', encoding='utf-8') as f:
            for line in f:
                seeds.append(line.strip())
        return seeds        
    