from lancedb.pydantic import LanceModel, Vector
from pydantic import BaseModel
import pyarrow as pa
from typing import Optional
from ..config import SENTENCE_EMBEDDING_DIMENSIONS


# schema and dataclass as one class. Acts as scheme for content LanceDB, where data is stored in its more native form.
class SchemaContent(LanceModel):
    url: str
    url_hash: str 
    uuid: str
    parent_uuid: str | None
    date: str
    date_accessed: str
    origin: str
    username: str | None
    content: str
    content_type: str
    is_split: bool

# schema and dataclass as one. Acts as schema for Sentence LanceDB< where data is stored at the sentence level. This acts as corpus for training.
class SchemaSentence(LanceModel):
    url: str
    url_hash: str 
    content_uuid: str
    sentence: str
    sentence_hash: str 
    sentence_uuid: str
    date: str
    vector: Vector(dim=SENTENCE_EMBEDDING_DIMENSIONS) | None
    is_embedded: bool = False
    is_modelled: bool  = False

class ValidationMetricsView(BaseModel):
    trial_num: int
    trial_id: str
    score_NPMI: float | None
    score_UMass: float | None
    prob_distribution: any

