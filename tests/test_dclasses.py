from thematic_analysis_model.model.dclasses import *
from pydantic.dataclasses import dataclass
from pydantic import TypeAdapter
import pytest
import json

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
    
