from thematic_analysis_model.model.dclasses import *
from pathlib import Path
import json
import os
from pydantic import TypeAdapter


#util methods 

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