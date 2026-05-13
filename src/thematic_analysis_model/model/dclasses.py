from pydantic.dataclasses import dataclass
from typing import Annotated
import numpy as np
from pydantic import Field, BeforeValidator, PlainSerializer, RootModel, ConfigDict
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

# smart compare for embedded data classes
def smart_compare(val1, val2):
    if type(val1) != type(val2):
        return False

    if isinstance(val1, np.ndarray):
        return np.array_equal(val1, val2)
    elif isinstance(val1, list):
        return len(val1) == len(val2) and all(smart_compare(a, b) for a, b in zip(val1, val2))
    elif isinstance(val1, dict):
        return val1.keys() == val2.keys() and all(smart_compare(val1[k], val2[k]) for k in val1)
    else:
        return val1 == val2

# annotated types for embedded dataclass serialization/deserialization
#NOTE it is important to do this to not have to use python lists (very slow)

#   before validator loads from json, tries to force data to be a a np.ndarray
#   plain serializer forces np.ndarray to be a python list
CustomNpArray = Annotated[
    np.ndarray,
    BeforeValidator(lambda v: np.ndarray(v) if not isinstance(v, np.ndarray) else v),
    PlainSerializer(lambda v: v.tolist(), return_type=list)
]

#NOTE must use RootModel whenever we want to type adapt these dataclasses, as they are more complicated than the native python data type ones.

# now sentences are embedded as np.ndarrays, therefore content is now a list of np.ndarrays
@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class EmbeddedContent(ABC): # inherits form root model for better serialization of nested complex data types
    metadata: Metadata
    embedded_content: list[CustomNpArray]

    def __eq__(self, other):
        if not isinstance(other, EmbeddedContent): return False
        if self.metadata != other.metadata: return False
        if len(self.embedded_conten) != len(other.embedded_content): return False
        for t1, t2 in zip(self.embedded_content, other.embedded_content):
            if isinstance(t1, np.ndarray):
                if not np.array_equal(t1, t2): return False
            elif t1 != t2: return False

        return True



@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class EmbeddedComment(EmbeddedContent):
    embedded_comments: Optional[list['EmbeddedComment']] = Field(default=list) # forward reference, default empty list

@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class EmbeddedPost(EmbeddedContent):
    embedded_title: list[CustomNpArray]
    embedded_comments: Optional[list[EmbeddedComment]] = Field(default=list) # forward reference, default empty list

