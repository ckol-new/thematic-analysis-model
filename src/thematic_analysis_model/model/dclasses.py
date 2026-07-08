from lancedb.pydantic import LanceModel
from pydantic import BaseModel, TypeAdapter

# dataclass for content (either post or comment), as close to its native context as possible
class Content:
    ...

# dataclass for individual line of post/comment, with all necessary metadata
class Line:
    ...

# dataclass for configuration parameters of a given trial of the pipeline
class TrialConfig:
    ...

# dataclass for the validation metrics of the topic model, for easy serialization.
class ValidationMetrics:
    ...
