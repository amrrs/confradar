from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from importlib import resources
from typing import Iterable, List, Optional

from .storage import load_user_conferences, load_remote_conferences


@dataclass
class Conference:
    name: str
    start_date: str  # ISO date string
    end_date: str  # ISO date string
    city: str
    country: str
    url: str
    topics: List[str]

    def start_dt(self) -> datetime:
        return datetime.fromisoformat(self.start_date)

    def end_dt(self) -> datetime:
        return datetime.fromisoformat(self.end_date)


def load_conferences() -> List[Conference]:
    """Load bundled sample conferences and merge with user-added items."""
    with resources.files("confradar.data").joinpath("conferences.json").open("r", encoding="utf-8") as f:
        data = json.load(f)
    data.extend(load_user_conferences())
    data.extend(load_remote_conferences())
    confs = [Conference(**row) for row in data]
    # Deduplicate by (name, start_date, end_date)
    seen = set()
    unique: List[Conference] = []
    for c in confs:
        key = (c.name.lower(), c.start_date, c.end_date)
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)
    return unique


def filter_conferences(
    items: Iterable[Conference],
    *,
    topic: Optional[str] = None,
    country: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
) -> List[Conference]:
    result = list(items)
    if topic:
        t = topic.lower()
        result = [c for c in result if any(t in s.lower() for s in c.topics) or t in c.name.lower()]
    if country:
        ctry = country.lower()
        result = [c for c in result if ctry in c.country.lower()]
    if after:
        after_dt = datetime.fromisoformat(after)
        result = [c for c in result if c.end_dt() >= after_dt]
    if before:
        before_dt = datetime.fromisoformat(before)
        result = [c for c in result if c.start_dt() <= before_dt]
    return sorted(result, key=lambda c: c.start_dt())


