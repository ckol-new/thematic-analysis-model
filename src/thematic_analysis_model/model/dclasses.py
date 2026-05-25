from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from lancedb.pydantic import LanceModel

class Author(BaseModel):
    username: str
    userid: str

class Metadata(BaseModel):
    url: str
    uuid: str
    date: str
    date_accessed: str
    author: Author
    origin: str

class Content(LanceModel):
    metadata: Metadata
    content: str
    content_type: str


