from pydantic.dataclasses import dataclass
import numpy as np
from pydantic import Field
from abc import ABC
from typing import Optional


# author dataclass
@dataclass
class Author:
    username: str
    userid: str

# metadata dataclass
@dataclass
class Metadata:
    uuid: str
    author: Author
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
    comments: Optional[list['Comment']] = Field(default=list) # forward reference to Comment class, or default to empty list

# post dataclass
@dataclass
class Post(Content):
    title: str
    comments: Optional[list[Comment]] = Field(default=list)


# now sentences are embedded as np.ndarrays, therefore content is now a list of np.ndarrays
@dataclass
class EmbeddedContent(ABC):
    metadata: Metadata
    embedded_content: list[np.ndarray]

@dataclass
class EmbeddedComment(EmbeddedContent):
    embedded_comments: Optional[list['EmbeddedComment']] = Field(default=list) # forward reference, default empty list

@dataclass
class EmbeddedPost(EmbeddedContent):
    embedded_title: list[np.ndarray]
    embedded_comments: Optional[list[EmbeddedComment]] = Field(default=list) # forward reference, default empty list