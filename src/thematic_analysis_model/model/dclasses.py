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
    type_: str
    is_processed: bool = False

# dataclass for individual sentence of post/comment, with all necessary metadata
class Sentence(LanceModel):
    sentence: str
    url: str
    date: str
    forum_origin: str
    content_origin_uuid: str
    uuid: str
    hash_: str # url hash
    type_: str
    vector: Vector(dim=EMBEDDING_DIMENSIONS) | None = None
    is_embedded: bool = False
    is_modelled: bool = False
    is_validated: bool = False
    topic: int | None = None
    probabilities: list[float] | None = None
    

# dataclass for configuration parameters of a given trial of the pipeline
class TrialConfig(BaseModel):
    trial_num: int
    trial_desc: str
    model_save_path: str
    validation_metric_save_path: str
    embedding_model: str
    n_neighbours: int
    n_components: int
    min_cluster_size: int
    min_samples: int | None

# dataclass for the validation metrics of the topic model, for easy serialization.
class ValidationMetrics(BaseModel):
    trial_config: TrialConfig
    total_pairwise_embedding_distance: float
    mean_intertopic_cosine_similarity: float
    topic_diversity: float
    noise_ratio: float
    topic_pairwise_embedding_distance: list[float]
    topic_prob_data: list[dict]
    redundant_pairs: list[dict]


# adapters
trial_config_adapter = TypeAdapter(TrialConfig)
validation_metrics_adapter = TypeAdapter(ValidationMetrics)