from pydantic import BaseModel
from typing import Optional
from pydantic.dataclasses import dataclass
from lancedb.pydantic import LanceModel

# Everything is optional, but validation will occur later

class Author(BaseModel):
    username: Optional[str] = None
    userid: Optional[str] = None

class Metadata(BaseModel):
    url: Optional[str] = None
    uuid: Optional[str] = None
    url_hash: Optional[str] = None
    date: Optional[str] = None
    date_accessed: Optional[str] = None
    author: Optional[Author] = None
    origin: Optional[str] = None

class Content(LanceModel):
    metadata: Optional[Metadata] = None
    content: Optional[str] = None
    title: Optional[str] = None
    content_type: Optional[str] = None


