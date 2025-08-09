from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, Set

from platformdirs import user_data_dir

APP_NAME = "confradar"


def get_data_dir() -> Path:
    data_dir = Path(user_data_dir(APP_NAME))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _file(path_name: str) -> Path:
    return get_data_dir() / path_name


def load_json_list(path: Path) -> List[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_json_list(path: Path, items: Iterable[dict]) -> None:
    path.write_text(json.dumps(list(items), indent=2, ensure_ascii=False), encoding="utf-8")


def load_user_conferences() -> List[dict]:
    return load_json_list(_file("user_conferences.json"))


def save_user_conferences(conferences: Iterable[dict]) -> None:
    save_json_list(_file("user_conferences.json"), conferences)


def load_stars() -> Set[str]:
    path = _file("stars.json")
    if not path.exists():
        return set()
    try:
        return set(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return set()


def save_stars(starred_names: Iterable[str]) -> None:
    _file("stars.json").write_text(json.dumps(list(starred_names), indent=2), encoding="utf-8")


# ------------------------------- Sources ---------------------------------

def load_sources() -> List[dict]:
    """Return list of source dicts. Example: {"type": "json", "url": "https://..."} or {"type": "file-json", "path": "/path"}."""
    return load_json_list(_file("sources.json"))


def save_sources(sources: Iterable[dict]) -> None:
    save_json_list(_file("sources.json"), sources)


def load_remote_conferences() -> List[dict]:
    return load_json_list(_file("remote_conferences.json"))


def save_remote_conferences(conferences: Iterable[dict]) -> None:
    save_json_list(_file("remote_conferences.json"), conferences)


