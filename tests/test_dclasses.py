from thematic_analysis_model.model.dclasses import *
from pydantic.dataclasses import dataclass
from dataclasses import asdict
from pydantic import TypeAdapter
import pytest
import json

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







