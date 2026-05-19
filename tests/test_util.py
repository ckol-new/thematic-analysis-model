from thematic_analysis_model.model.util import *
from thematic_analysis_model.model.dclasses import *
from pathlib import Path
import os

test_var = {
    'uuid': '123',
    'url': 'test.com',
    'date': 'today',
    'origin': 'forum.com',
    'date_accessed': 'right now',
    'username': 'user',
    'userid': 'userid',
    'content': 'text',
    'title': 'title',
}

def test_save_load_dclasses():
    save_location = Path.cwd() / 'tests' / 'testing_data' /'test_save_dclasses.jsonl'
    author = Author(test_var['username'], test_var['userid'])
    dclasses = [author, author, author]

    # test save dclasses
    save_dclasses(save_location, Author, dclasses)

    # test load dclasses
    loaded_dclasses = load_dclasses(save_location, Author)

    assert dclasses == loaded_dclasses

def test_append_dclasses():
    save_location = Path.cwd() / 'tests' / 'testing_data' /'test_append_dclasses.jsonl'
    author = Author(test_var['username'], test_var['userid'])
    dclasses = [author, author, author]

    # get original file length
    original_len = get_file_length(save_location)

    append_dclasses(save_location, Author, dclasses)

    new_len = get_file_length(save_location)

    assert new_len == original_len + len(dclasses)



