import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable

USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")

def normalize_username(value):
    if not isinstance(value, str):
        return None
    value = value.strip().strip('"').strip("'").lstrip("@").strip().lower()
    if USERNAME_RE.fullmatch(value):
        return value
    return None

def _walk_json(obj: Any) -> Iterable[str]:
    """Recursively extract likely Instagram usernames from JSON.

    Supports common export patterns such as:
      {"string_list_data":[{"value":"username"}]}
      {"username":"username"}
      {"href":"https://www.instagram.com/username/"}
    It also handles arbitrarily nested lists/dicts.
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_l = str(key).lower()

            if key_l in {"username", "value"}:
                candidate = normalize_username(value)
                if candidate:
                    yield candidate

            if key_l in {"href", "url", "link"} and isinstance(value, str):
                m = re.search(r"instagram\.com/([A-Za-z0-9._]{1,30})/?(?:[?#].*)?$", value, re.I)
                if m:
                    candidate = normalize_username(m.group(1))
                    if candidate:
                        yield candidate

            yield from _walk_json(value)

    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_json(item)

def load_text(path: Path):
    return path.read_text(encoding="utf-8-sig").splitlines()

def load_csv(path: Path):
    usernames = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                usernames.append(row[0])
    return usernames

def load_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)
    return list(_walk_json(data))

def extract_usernames(path_str: str):
    path = Path(path_str)
    ext = path.suffix.lower()

    if ext == ".txt":
        raw = load_text(path)
    elif ext == ".csv":
        raw = load_csv(path)
    elif ext == ".json":
        raw = load_json(path)
    else:
        raise ValueError("Supported files: .txt, .csv, .json")

    cleaned = set()
    for value in raw:
        u = normalize_username(value)
        if u:
            cleaned.add(u)

    return sorted(cleaned)
