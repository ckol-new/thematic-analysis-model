from ..config import EMBEDDING_DIMENSIONS
from lancedb.pydantic import LanceModel, Vector
from pydantic import BaseModel, TypeAdapter
from enum import Enum

class ContentType(Enum):
    POST = 1
    COMMENT = 1

# dataclass for content (either post or comment), as close to its native context as possible
class Content:
    text: str
    url: str
    date: str
    title: str | None
    author_username: str
    forum_origin: str
    hash_: str
    uuid: str
    type_: ContentType
    is_processed: bool = False

# dataclass for individual line of post/comment, with all necessary metadata
class Line:
    line: str
    url: str
    date: str
    forum_origin: str
    content_origin_uuid: str
    uuid: str
    hash_: str
    type_: ContentType
    vector: Vector(dim=EMBEDDING_DIMENSIONS) | None = None
    is_embedded: bool = False
    is_modelled: bool = False
    is_validated: bool = False
    topic: int
    probabilities: list[float]
    

# dataclass for configuration parameters of a given trial of the pipeline
class TrialConfig:
    ...

# dataclass for the validation metrics of the topic model, for easy serialization.
class ValidationMetrics:
    ...


# adapters
content_adapter = TypeAdapter(Content)
line_adapter = TypeAdapter(Line)
trial_config_adapter = TypeAdapter(TrialConfig)
validation_metrics_adapter = TypeAdapter(ValidationMetrics)