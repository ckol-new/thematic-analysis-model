from pydantic import BaseModel
from typing import Optional
from pydantic.dataclasses import dataclass
from lancedb.pydantic import LanceModel

class Author(BaseModel):
    username: Optional[str] = None
    userid: Optional[str] = None

class Metadata(BaseModel):
    url: str
    uuid: str
    date: str
    date_accessed: str
    author: Optional[Author] = None
    origin: str

class Content(LanceModel):
    metadata: Metadata
    content: str
    title: Optional[str] = None
    content_type: str


