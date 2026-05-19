from thematic_analysis_model.model.dclasses import *
from pathlib import Path
import json
import os
from pydantic import TypeAdapter


#util methods 

# get file length
def get_file_length(file_path: Path) -> int:
    with file_path.open('r', encoding='utf-8') as f:
        count = sum(1 for _ in f)
    return count

# def save text
def save_text(fpath: Path, arr: list[str]):
    fpath.parent.mkdir(parents=True, exist_ok=True)

    with fpath.open('w', encoding='utf-8') as f:
        for i in arr:
            f.write(i.strip() + '\n')
# append text to file
def append_text(fpath: Path, arr: list[str]):
    prefix = "" # default
    
    # if pointer not on newline, add newline character to front
    if os.path.exists(fpath) and os.path.getsize() > 0:
        with fpath.open('rb', encoding='utf-8') as f:
            f.seek(-1, os.SEEK_END)
            last_char = f.read(1)
            if last_char != b'\n':
                prefix = '\n'

    # save text to end of file
    with fpath.open('a', encoding='utf-8') as f:
        for i in arr:
            f.write(f'{prefix}{i.strip()}\n')
# def load text
def load_text(fpath: Path) -> list[str]:
    text: list[str] = []
    with fpath.open('r') as f:
        for line in f:
            text.append(line.strip())
    return text



# load dataclasses from jsonl
# not memory efficient, loads all at once
def load_dclasses(file_path: Path, cls) -> list:
    # get adapter to enable conversion
    adapter = TypeAdapter(cls)

    # initialize array
    dclasses = []

    # load classes
    with file_path.open('r', encoding='utf-8') as f:
        for line in f:
            dclass = adapter.validate_json(line.strip())
            dclasses.append(dclass)
    
    return dclasses


# save dataclasses to jsonl, writes over file
# ensure cls and dclasses object are of same type
# not memory efficient, loads all at once
def save_dclasses(file_path: Path, cls, dclasses: list):
    # get adapter to enable conversion
    adapter = TypeAdapter(cls)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    # open file
    with file_path.open('w', encoding='utf-8') as f:
        for dclass in dclasses:
            f.write(adapter.dump_json(dclass).decode() + '\n')
    
# append dataclass to jsonl, appends to end
# ensure cls and dclasses object are of same type
# not memory efficient, loads all at once
def append_dclasses(file_path: Path, cls, dclasses: list):
    # get adapter to enable conversion
    adapter = TypeAdapter(cls)
    prefix = '' # default value

    # confirm that last line is on newline
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        # read binary, faster
        with file_path.open('rb') as f:
            f.seek(-1, os.SEEK_END)
            last_char = f.read(1)
            if last_char != b'\n':
                prefix = '\n'

    # write to file
    with file_path.open('a', encoding='utf-8') as f:
        for dclass in dclasses:
            json_line = adapter.dump_json(dclass).decode()
            f.write(f"{prefix}{json_line}\n")