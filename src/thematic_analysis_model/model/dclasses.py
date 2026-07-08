from lancedb.pydantic import LanceModel
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
    ...

# dataclass for configuration parameters of a given trial of the pipeline
class TrialConfig:
    ...

# dataclass for the validation metrics of the topic model, for easy serialization.
class ValidationMetrics:
    ...
