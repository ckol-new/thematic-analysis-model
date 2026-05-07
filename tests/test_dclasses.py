from thematic_analysis_model.model.dclasses import *
from pydantic.dataclasses import dataclass
from pydantic import TypeAdapter
import pytest
import json

test_var = {
    'uuid': '123',
    'url': 'test.com',
    'date': 'today',
    'origin': 'forum.com',
    'username': 'user',
    'content': 'text',
    'title': 'title',
}

def test_author():
    username = 'user'
    author = Author(username)

    adapter = TypeAdapter(Author)

    # expected serialized output
    expected = {"username":"user"}
    data = json.loads(adapter.dump_json(author).decode())
    assert expected == data

    # test if loading from json works
    input_str = '{"username":"user"}'
    author2 = adapter.validate_json(input_str)
    assert author == author2
    
def test_metadata():
    uuid = '123'
    url = 'test.com'
    date = 'today'
    origin = 'forum.com'

    metadata = Metadata(uuid, url, date, origin)
    adapter = TypeAdapter(Metadata)
    
    # test serialization
    expected = {'uuid': '123', 'url': 'test.com', 'date': 'today', 'origin': 'forum.com'}
    data = json.loads(adapter.dump_json(metadata).decode())
    assert expected == data

    # test deserialization
    input_str = '{"uuid":"123", "url":"test.com", "date":"today", "origin":"forum.com"}'
    metadata2 = adapter.validate_json(input_str)
    assert metadata == metadata2

# if post is working, comment is also working
# also tests nesting
def test_post():
    a = Author(test_var['username'])
    m = Metadata(test_var['uuid'], test_var['url'], test_var['date'], test_var['origin'])
    c = Comment(test_var['content'], m, None)
    p = Post(test_var['content'], m, test_var['title'], [c])

    adapter = TypeAdapter(Post)

    # test serialization
    expected = {"content":"text","metadata":{"uuid":"123","url":"test.com","date":"today","origin":"forum.com"},"title":"title","comments":[{"content":"text","metadata":{"uuid":"123","url":"test.com","date":"today","origin":"forum.com"}}]}
    data = json.loads(adapter.dump_json(p).decode())
    assert expected == data

    # test deserialization
    input_str = '{"content":"text","metadata":{"uuid":"123","url":"test.com","date":"today","origin":"forum.com"},"title":"title","comments":[{"content":"text","metadata":{"uuid":"123","url":"test.com","date":"today","origin":"forum.com"}}]}'
    p2 = adapter.validate_json(json.dumps(data))
    assert p == p2

test_post()




