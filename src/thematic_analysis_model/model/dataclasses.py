# dataclasses and adapters.
from lancedb.pydantic import LanceModel, Vector
from pydantic import BaseModel, TypeAdapter
from .config import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL_NAME
from datetime import datetime

from pathlib import Path
import uuid

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
    id_: str = str(uuid.uuid4())
    trial_num: int
    batch_name: str | None = None
    date: str = datetime.now().strftime("%Y/%m/%d")
    embedding_model: str = EMBEDDING_MODEL_NAME
    model_save_path: str | None = None
    umap_parametric: bool = False
    umap_n_neighbours: int = 15
    umap_n_components: int = 2
    umap_metric: str = 'euclidean'
    umap_min_dist: float = 0.1
    umap_random_state: int = 42
    hdbscan_min_cluster_size: int = 5
    hdbscan_min_samples: int | None = None
    hdbscan_metric: str = 'euclidean'
    hdbscan_cluster_selection_method: str = 'eom'
    stopwords_path: str | None = None # where stopwords will be
    nr_topics: int | None = None
    top_n_words: int = 10 # really no point increasing beyond 15 or 20
    visualize_documents: bool = False # really slow to do this, so while fine-tuning have this false.

class ValidationMetric(BaseModel):
    num_topics: int
    npmi_score: float
    total_pairwise_distance: float
    topics_pairwise_distance: list[float] # index is topic num
    topic_diversity: float
    mean_intertopic_cos_similarity: float
    redundant_pairs: list[dict]
    noise_ratio: float
    prob_distributions: list[dict]

class ModelOutput(LanceModel):
    trial_config: TrialConfig
    validation_metrics: str # json str
    topic_map: str | None# json str of plotly chart
    document_map: str | None
    heatmap: str | None
    hierarchy_map: str | None
    
# Adapters: enable pydantic dataclass adaptation to json, str, dict, etc.
validation_metric_adapter = TypeAdapter(ValidationMetric)