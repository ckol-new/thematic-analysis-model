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

# annotated types for embedded dataclass serialization/deserialization
#NOTE it is important to do this to not have to use python lists (very slow)

#   before validator loads from json, tries to force data to be a a np.ndarray
#   plain serializer forces np.ndarray to be a python list
CustomNpArray = Annotated[
    np.ndarray,
    BeforeValidator(lambda v: np.array(v) if not isinstance(v, np.ndarray) else v),
    PlainSerializer(lambda v: v.tolist(), return_type=list)
]

#NOTE must use RootModel whenever we want to type adapt these dataclasses, as they are more complicated than the native python data type ones.

# now sentences are embedded as np.ndarrays, therefore content is now a list of np.ndarrays
@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class EmbeddedContent(ABC): # inherits form root model for better serialization of nested complex data types
    metadata: Metadata
    embedded_content: Optional[list[CustomNpArray]] = Field(default=list)

    def __eq__(self, other):
        if not isinstance(other, EmbeddedContent): return False
        if self.metadata != other.metadata: return False
        if len(self.embedded_content) != len(other.embedded_content): return False
        for t1, t2 in zip(self.embedded_content, other.embedded_content):
            if isinstance(t1, np.ndarray):
                if not np.array_equal(t1, t2): return False
            elif t1 != t2: return False

        return True

@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class EmbeddedComment(EmbeddedContent):
    embedded_comments: Optional[list['EmbeddedComment']] = Field(default=list) # forward reference, default empty list

    def __eq__(self, other):
        if not isinstance(other, EmbeddedComment): return False
        if self.metadata != other.metadata: return False
        if len(self.embedded_content) != len(other.embedded_content): return False
        for t1, t2 in zip(self.embedded_content, other.embedded_content):
            if isinstance(t1, np.ndarray):
                if not np.array_equal(t1, t2): return False
            elif t1 != t2: return False
        if self.embedded_comments != other.embedded_comments: return False
        return True
        

@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class EmbeddedPost(EmbeddedContent):
    embedded_title: Optional[list[CustomNpArray]] = Field(default=list)
    embedded_comments: Optional[list[EmbeddedComment]] = Field(default=list) # forward reference, default empty list

    def __eq__(self, other):
        if not isinstance(other, EmbeddedPost): return False
        if self.metadata != other.metadata: return False
        # check embedded content equality
        if len(self.embedded_content) != len(other.embedded_content): return False
        for t1, t2 in zip(self.embedded_content, other.embedded_content):
            if isinstance(t1, np.ndarray):
                if not np.array_equal(t1, t2): return False
            elif t1 != t2: return False
        # check embedded title equality
        if len(self.embedded_title) != len(other.embedded_title): return False
        for t1, t2 in zip(self.embedded_title, other.embedded_title):
            if isinstance(t1, np.ndarray):
                if not np.array_equal(t1, t2): return False
            elif t1 != t2: return False
        if self.embedded_comments != other.embedded_comments: return False
        return True

# embedded metadata is a custom metadataclass that has some extra things
@dataclass 
class EmbeddedMetadata(Metadata):
    type_text: str
    sentence_num: int
    embedding_type: str

# class EmbeddedSentence() is an embedding for an indiviudal sentence, not packaged into a Post/Comment object
# this will most likely what i use
@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class EmbeddedSentence():
    metadata: EmbeddedMetadata
    embedded_text: CustomNpArray

    def __eq__(self, other):
        if not isinstance(other, EmbeddedSentence): return False
        if self.metadata != other.metadata: return False
        if not np.array_equal(self.embedded_text, other.embedded_text): return False
        return True

# efficient embedded sentence, that lowers ram usage
@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class EfficientEmbeddedSentence:
    uuid: str
    embedded_text: CustomNpArray

    def __eq__(self, other):
        if not isinstance(other, EfficientEmbeddedSentence): return False
        if self.uuid != other.uuid: return False
        if not np.array_equal(self.embedded_text, other.embedded_text): return False
        return True