from pydantic.dataclasses import dataclass
from abc import ABC
from typing import Optional


# author dataclass
@dataclass
class Author:
    username: str

# metadata dataclass
@dataclass
class Metadata:
    uuid: str
    url: str
    date: str
    origin: str

# content abstract dataclass
@dataclass
class Content(ABC):
    content: str
    metadata: Metadata

# comment dataclass
@dataclass
class Comment(Content):
    comments: Optional[list[Content]] = None

# post dataclass
@dataclass
class Post(Content):
    title: str
    comments: Optional[list[Content]] = None