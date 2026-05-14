from thematic_analysis_model.model.dclasses import *
from thematic_analysis_model.model.util import *
from pydantic.dataclasses import dataclass
from pydantic import RootModel
from dataclasses import asdict
from pydantic import TypeAdapter
import pytest
import json
import numpy as np
from sentence_transformers import SentenceTransformer

test_var = {
    'uuid': '123',
    'url': 'test.com',
    'date': 'today',
    'origin': 'forum.com',
    'username': 'user',
    'userid': 'userid',
    'content': 'text',
    'title': 'title',
}

def test_author():
    username = 'user'
    userid = 'userid'
    author = Author(username, userid)

    adapter = TypeAdapter(Author)

    # expected serialized output
    expected = {"username":"user", "userid":"userid"}
    data = json.loads(adapter.dump_json(author).decode())
    assert expected == data

    # test if loading from json works
    input_str = '{"username":"user", "userid":"userid"}'
    author2 = adapter.validate_json(input_str)
    assert author == author2
    
def test_metadata():
    uuid = '123'
    url = 'test.com'
    date = 'today'
    origin = 'forum.com'

    username = 'user'
    userid = 'userid'
    author = Author(username, userid)

    metadata = Metadata(uuid, author, url, date, origin)
    adapter = TypeAdapter(Metadata)
    
    # test serialization
    expected = {'uuid': '123', 'author': {'username': 'user', 'userid': 'userid'}, 'url': 'test.com', 'date': 'today', 'origin': 'forum.com'}
    data = json.loads(adapter.dump_json(metadata).decode())
    assert expected == data

    # test deserialization
    #NOTE it is important for the string to have "" for any json or it will fail; python excepts both but json does not
    input_str = {'uuid':'123', 'author':{'username':'user', 'userid':'userid'}, 'url':'test.com', 'date':'today', 'origin':'forum.com'}
    metadata2 = adapter.validate_python(input_str)
    assert metadata == metadata2


# if post is working, comment is also working
# also tests nesting
def test_post():
    a = Author(test_var['username'], test_var['userid'])
    m = Metadata(uuid=test_var['uuid'], author=a, url=test_var['url'], date=test_var['date'], origin=test_var['origin'])
    c = Comment(test_var['content'], m, None)
    p = Post(test_var['content'], m, test_var['title'], [c])

    adapter = TypeAdapter(Post)

    # test serialization
    expected = {'content': 'text', 'metadata': {'uuid': '123', 'author': {'username': 'user', 'userid': 'userid'}, 'url': 'test.com', 'date': 'today', 'origin': 'forum.com'}, 'title': 'title', 'comments': [{'content': 'text', 'metadata': {'uuid': '123', 'author': {'username': 'user', 'userid': 'userid'}, 'url': 'test.com', 'date': 'today', 'origin': 'forum.com'}, 'comments': None}]}
    data = json.loads(adapter.dump_json(p))
    assert expected == data

    # test deserialization
    input_json = adapter.dump_json(p).decode()
    p2 = adapter.validate_json(input_json)
    assert p == p2

#tests if posts work if there are no comments
def test_post_nocomments():
    a = Author(test_var['username'], test_var['userid'])
    m = Metadata(uuid=test_var['uuid'], author=a, url=test_var['url'], date=test_var['date'], origin=test_var['origin'])
    p = Post(test_var['content'], m, test_var['title'], None)

    adapter = TypeAdapter(Post)

    # test serialization
    expected = {'content': 'text', 'metadata': {'uuid': '123', 'author': {'username': 'user', 'userid': 'userid'}, 'url': 'test.com', 'date': 'today', 'origin': 'forum.com'}, 'title': 'title', 'comments': None}
    data = json.loads(adapter.dump_json(p))
    assert expected == data

    # test deserilaization
    input_json = adapter.dump_json(p).decode()
    p2 = adapter.validate_json(input_json)
    assert p == p2


# test embedded post serialization, and deserialization, nested objects as well
def test_embedded_post():
    author_dict = {'username':'username', 'userid':'userid'}
    author = Author(**author_dict)
    metadata_dict = {'uuid':'test', 'author':author, 'url':'test.com', 'date':'date', 'origin':'origin.com'}
    metadata = Metadata(**metadata_dict)
    narr = np.array([1,2,3])
    comment = EmbeddedComment(metadata=metadata, embedded_content=[narr], embedded_comments=None)
    comment2 = EmbeddedComment(metadata=metadata, embedded_content=[narr], embedded_comments=[comment])
    post = EmbeddedPost(metadata, [narr], [narr], [comment2])

    adapter = TypeAdapter(EmbeddedPost)

    # test serialization
    expected = {'metadata': {'uuid': 'test', 'author': {'username': 'username', 'userid': 'userid'}, 'url': 'test.com', 'date': 'date', 'origin': 'origin.com'}, 'embedded_content': [[1, 2, 3]], 'embedded_title': [[1, 2, 3]], 'embedded_comments': [{'metadata': {'uuid': 'test', 'author': {'username': 'username', 'userid': 'userid'}, 'url': 'test.com', 'date': 'date', 'origin': 'origin.com'}, 'embedded_content': [[1, 2, 3]], 'embedded_comments': [{'metadata': {'uuid': 'test', 'author': {'username': 'username', 'userid': 'userid'}, 'url': 'test.com', 'date': 'date', 'origin': 'origin.com'}, 'embedded_content': [[1, 2, 3]], 'embedded_comments': None}]}]}
    data = adapter.dump_python(post)
    assert expected ==  data
    # save to file
    location = Path.cwd() / 'tests' / 'testing_data' / 'test_embedded_save_single.jsonl'
    smart_save(location, [json.dumps(data)], 'jsonl')

    post_loaded =  adapter.validate_json(smart_load(location)[0])# note smart load jsonl returns list

    assert post == post_loaded

def test_embedded_sentence():
    # set up embedded sentence object
    author_dict = {'username':'username', 'userid':'userid'}
    author = Author(**author_dict)
    embedded_metadata_dict = {'uuid':'test', 'author':author, 'url':'test.com', 'date':'date', 'origin':'origin.com', 'type_text':'post', 'sentence_num':1, 'embedding_type': 'dense'}
    embedded_metadata = EmbeddedMetadata(**embedded_metadata_dict)
    narr = np.array([1,2,3])
    embedded_sentence = EmbeddedSentence(embedded_metadata, narr)

    # type adapter
    adapter = TypeAdapter(EmbeddedSentence)

    # test serialization
    expected = {"metadata":{"uuid":"test","author":{"username":"username","userid":"userid"},"url":"test.com","date":"date","origin":"origin.com","type_text":"post","sentence_num":1,"embedding_type":"dense"},"embedded_text":[1,2,3]}
    data = adapter.dump_python(embedded_sentence)
    assert data == expected

    # test deserialization
    location = Path.cwd() / 'tests' / 'testing_data' / 'test_embedded_sentence.jsonl'
    smart_save(location, [json.dumps(data)], 'jsonl')
    loaded_embedded_sentence = adapter.validate_json(smart_load(location)[0])
    assert loaded_embedded_sentence == embedded_sentence







