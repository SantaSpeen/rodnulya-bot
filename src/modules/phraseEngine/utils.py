import sys
from pathlib import Path

def base_path():
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    try:
        # noinspection PyUnresolvedReferences,PyProtectedMember
        return Path(sys._MEIPASS).resolve()
    except AttributeError:
        return Path().resolve()

def get_file(filename):
    return base_path() / "resources" / filename

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
