from pydantic.dataclasses import dataclass
from typing import Annotated
import numpy as np
from pydantic import Field, BeforeValidator, PlainSerializer, RootModel, ConfigDict
from abc import ABC
from typing import Optional


# author dataclass
@dataclass(config=ConfigDict())
class Author:
    username: str
    userid: str

# metadata dataclass
@dataclass(config=ConfigDict())
class Metadata:
    uuid: str
    author: Author
    url: str
    date: str
    origin: str
    date_accessed: str

# content abstract dataclass
@dataclass
class Content(ABC):
    metadata: Metadata
    content: str

# comment dataclass
@dataclass
class Comment(Content):
    comments: Optional[list['Comment']] = Field(default_factory=list) # forward reference to Comment class, or default to empty list

# post dataclas
@dataclass
class Post(Content):
    title: str
    comments: Optional[list[Comment]] = Field(default=list)