# utilitity methods not shared by classes
import pathlib 
from pathlib import Path
import json

# save text 
def __save_text(location: Path, data):
    location.write_text(str(data), encoding='utf-8')

# save json
def __save_json(location: Path, data):
    location.write_text(json.dumps(data, indent=4), encoding='utf-8')

# save jsonl
# turns lists into json lines
def __save_jsonl(location: Path, data: list):
    with location.open('w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

# smart saver, 'dispatches' different save functions based on type of dave
# automatically creates directory if does not exist
# input format type that you want to save to, defaults to 'txt'
def smart_save(location: str | Path, data, format_type: str = 'txt'):
    # get path
    p = Path(location).resolve()
    p.parent.mkdir(parents=True, exist_ok=True) # make parent directories if necessary

    # dispatcher dictionary
    formats = {
        'json': __save_json,
        'txt': __save_text,
        'jsonl':  __save_jsonl
    }

    # get save function based on format type
    save_function = formats.get(format_type.lower())
    if not save_function: raise ValueError(f'Unsupported format {format_type}')

    # save data
    try:
        save_function(p, data)
    except OSError as e:
        print(f'File save error {e}')

# load txt file
def __load_txt(location: Path):
    return location.read_text(encoding='utf-8')

# load json
def __load_json(location: Path):
    return json.loads(location.read_text(encoding='utf-8'))

def __load_jsonl(location: Path) -> list:
    data = []
    with location.open('r', encoding='utf-8') as f:
        for line in f.readlines():
            data.append(json.loads(line))
    return data

# smart load function automatically detects file type of data to be loaded, and loads it dispatches correct function accordingling
def smart_load(location: Path | str):
    # load path
    p = Path(location).resolve()
    if not p.exists():
        raise FileNotFoundError(f'No file found at {p}')
    if not p.is_file():
        raise IsADirectoryError(f'Expected a file, but got a directory at {p}')

    # format
    readers = {
        '.txt': __load_txt,
        '.json': __load_json,
        '.jsonl': __load_jsonl
    }
    reader_function = readers.get(p.suffix.lower(), __load_txt) # get reader function, default to loading text

    # read
    try:
        return reader_function(p)
    except Exception as e:
        print(f'Failed to parse {p.name}: {e}')
        return None


    
