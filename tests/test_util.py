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

def test_write_append_bug_txt():
    save_location = Path.cwd() / 'tests' / 'testing_data' / 'test_write_append_bug.txt'
    item = "I am the item"
    items = [item, item, item]

    # write file
    save_text(save_location, items)

    # append to file
    append_text(save_location, items)

    # test load items
    assert items + items == load_text(save_location)

def test_write_append_bug_dclasses():
    fpath = Path.cwd() / 'tests' / 'testing_data' / 'test_write_append_bug.jsonl'
    author = Author(test_var['username'], test_var['userid'])
    dclasses = [author, author, author]

    # write file
    save_dclasses(fpath, Author,  dclasses)

    # append file
    append_dclasses(fpath, Author, dclasses)

    assert dclasses + dclasses == load_dclasses(fpath, Author)

