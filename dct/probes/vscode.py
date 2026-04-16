import re
from pathlib import Path


_EXT_RE = re.compile(r"^(?P<id>.+?\.[^-]+(?:-[^-]+)*)-(?P<ver>\d[\w.+-]*)$")


def list_installed(home=None):
    home = Path(home) if home else Path.home()
    ext_dir = home / ".vscode" / "extensions"
    return _scan(ext_dir)


def _scan(ext_dir):
    if not ext_dir.is_dir():
        return []
    ids = set()
    for entry in ext_dir.iterdir():
        if not entry.is_dir():
            continue
        m = _EXT_RE.match(entry.name)
        if m:
            ids.add(m.group("id"))
    return sorted(ids)
