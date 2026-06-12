from lancedb.pydantic import LanceModel, Vector
import pyarrow as pa
from typing import Optional
from ..config import SENTENCE_EMBEDDING_DIMENSIONS


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

class SchemaSentence(LanceModel):
    url: str
    url_hash: str 
    content_uuid: str
    sentence: str
    sentence_hash: str 
    sentence_uuid: str
    date: str
    vector: Vector(dim=SENTENCE_EMBEDDING_DIMENSIONS)
    is_embedded: bool = False
    is_modelled: bool  = False
