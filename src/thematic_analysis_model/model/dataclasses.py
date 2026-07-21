# dataclasses and adapters.
from lancedb.pydantic import LanceModel, Vector
from pydantic import BaseModel, TypeAdapter
from .config import EMBEDDING_DIMENSIONS



class Metadata(BaseModel): # metaedata of content, not of individual sentence, mostly for locating post in internet
    url: str
    date: str
    date_accessed: str
    forum_origin: str
    username: str | None = None

class Content(LanceModel):
    uuid_: str # unique identifier separate from content
    parent_uuid_: str | None = None # if comment, hold uuid to parent post -> like a linked list
    hash_: str # content hash
    metadata_: Metadata
    title: str | None = None
    text: str 
    # bool flags
    is_processed: bool = False
    is_split: bool = False

class Sentence(LanceModel):
    uuid_: str
    hash_: str
    content_uuid_: str
    metadata_: Metadata
    sentence: str
    embedding: Vector(dim=EMBEDDING_DIMENSIONS) | None = None
    reduced_embedding: list[float] # I want to be able to change this later, so it has to be dynamic array
    # bool flags
    is_embedded: bool = False
    is_modelled: bool = False
    is_validated: bool = False

class TrialConfig(BaseModel):
    ...

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