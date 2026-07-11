from ..config import EMBEDDING_DIMENSIONS
from lancedb.pydantic import LanceModel, Vector
from pydantic import BaseModel, TypeAdapter
from enum import Enum

class ContentType(str, Enum):
    POST = 'post'
    COMMENT = 'comment'

# dataclass for content (either post or comment), as close to its native context as possible
class Content(LanceModel):
    text: str
    url: str
    date: str
    title: str | None
    author_username: str
    forum_origin: str
    hash_: str
    uuid: str
    parent_uuid: str | None
    date_accessed: str
    type_: ContentType
    is_processed: bool = False

# dataclass for individual line of post/comment, with all necessary metadata
class Line(LanceModel):
    line: str
    url: str
    date: str
    forum_origin: str
    content_origin_uuid: str
    uuid: str
    hash_: str # url hash
    type_: ContentType
    vector: Vector(dim=EMBEDDING_DIMENSIONS) | None = None
    is_embedded: bool = False
    is_modelled: bool = False
    is_validated: bool = False
    topic: int
    probabilities: list[float]
    

# dataclass for configuration parameters of a given trial of the pipeline
class TrialConfig(BaseModel):
    ...

# dataclass for the validation metrics of the topic model, for easy serialization.
class ValidationMetrics(BaseModel):
    ...


# adapters
trial_config_adapter = TypeAdapter(TrialConfig)
validation_metrics_adapter = TypeAdapter(ValidationMetrics)