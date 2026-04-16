import json
from pathlib import Path

CONFIG_FILE = ".dct.json"
SCHEMA_VERSION = 1


def load(workspace):
    path = Path(workspace) / CONFIG_FILE
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)


def save(answers, workspace):
    path = Path(workspace) / CONFIG_FILE
    data = {"schema": SCHEMA_VERSION, **answers}
    with path.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    return path
