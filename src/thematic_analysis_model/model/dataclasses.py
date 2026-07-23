# dataclasses and adapters.
from lancedb.pydantic import LanceModel, Vector
from pydantic import BaseModel, TypeAdapter
from .config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL_NAME

from pathlib import Path



class Metadata(BaseModel): # metaedata of content, not of individual sentence, mostly for locating post in internet
    url: str
    date: str
    date_accessed: str
    forum_origin: str
    username: str | None = None
    type_: str

class Content(LanceModel):
    uuid_: str # unique identifier separate from content
    parent_uuid_: str | None = None # if comment, hold uuid to parent post -> like a linked list
    hash_: str # content hash
    metadata_: Metadata
    title: str | None = None
    text: str 
    # bool flags
    is_split: bool = False

class Sentence(LanceModel):
    uuid_: str
    hash_: str
    content_uuid_: str
    metadata_: Metadata
    sentence: str
    embedding: Vector(dim=EMBEDDING_DIMENSIONS) | None = None
    reduced_embedding: list[float] | None = None # I want to be able to change this later, so it has to be dynamic array
    topic: int | None = None
    probabilities: list[float] | None = None
    # bool flags
    is_processed: bool = False # has been processed for embedding
    is_embedded: bool = False # has been embedded
    is_modelled: bool = False # has been modelled
    is_validated: bool = False # has been validated


class TrialConfig(BaseModel):
    trial_name: str
    id_: str
    trial_num: int
    trial_group: str | None = None
    embedding_model: str = EMBEDDING_MODEL_NAME
    umap_n_neighbours: int = 15
    umap_n_components: int = 2
    umap_metric: str = 'euclidean'
    umap_min_dist: float = 0.1
    hdbscan_min_cluster_size: int = 5
    hdbscan_min_samples: int | None = None
    hdbscan_metric: str = 'euclidean'
    hdbscan_cluster_selection_method: str = 'eom'
    stopwords_path: str | None = None # where stopwords will be
    nr_topics: int | None = None
    top_n_words: int = 10 # really no point increasing beyond 15 or 20


class ValidationMetric(BaseModel):
    ...

class ModelOutput(LanceModel):
    name: str
    batch_name: str | None = None
    trial_config: TrialConfig
    validation_metrics: str # json str
    topic_map: str | None# json str of plotly chart
    document_map: str | None
    heatmap: str | None
    hierarchy_map: str | None
    

    



# Adapters: enable pydantic dataclass adaptation to json, str, dict, etc.