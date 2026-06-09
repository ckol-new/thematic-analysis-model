from pydantic import BaseModel
from typing import Optional
from pydantic.dataclasses import dataclass
from lancedb.pydantic import LanceModel, Vector


# UUID is for identity irrespective of content, hashes is for identity based on content

VECTOR_DIM = 384
class SchemaSentence(LanceModel):
    url: Optional[str] = None
    url_hash: Optional[bytes] = None
    content_uuid: Optional[str] = None
    sentence_uuid: Optional[str] = None
    sentence_hash: Optional[bytes] = None
    sentence: Optional[str] = None
    vector: Optional[Vector(dim=VECTOR_DIM)] = None
    is_modelled: Optional[bool] = False
    


class SchemaContent(LanceModel):
    url: Optional[str] = None
    uuid: Optional[str] = None
    url_hash: Optional[bytes] = None
    date: Optional[str] = None
    date_accessed: Optional[str] = None
    origin: Optional[str] = None
    username: Optional[str] = None
    userid: Optional[str] = None
    content: Optional[str] = None
    title: Optional[str] = None
    content_type: Optional[str] = None
    is_split: bool
