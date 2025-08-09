from __future__ import annotations

import json
from typing import List

import httpx

from .storage import load_sources, save_remote_conferences, save_sources
from importlib import resources


def _normalize_rows(rows: List[dict]) -> List[dict]:
    """Normalize external rows to our schema.

    Input rows may be camelCase like from tech-conferences dataset:
    - name, url, startDate, endDate, city, country, tags/topics
    Output schema keys: name, start_date, end_date, city, country, url, topics(list[str])
    """
    normalized: List[dict] = []
    for r in rows or []:
        name = r.get("name") or r.get("title")
        url = r.get("url") or r.get("link")
        start_date = r.get("start_date") or r.get("startDate") or r.get("date")
        end_date = r.get("end_date") or r.get("endDate") or start_date
        city = r.get("city") or r.get("location") or ""
        country = r.get("country") or r.get("countryCode") or ""
        topics = r.get("topics") or r.get("tags") or []

        if isinstance(topics, str):
            topics = [t.strip() for t in topics.split(",") if t.strip()]
        elif not isinstance(topics, list):
            topics = []

        # Skip if essential fields missing
        if not name or not url or not start_date:
            continue

        normalized.append(
            {
                "name": name,
                "start_date": start_date,
                "end_date": end_date or start_date,
                "city": city,
                "country": country,
                "url": url,
                "topics": topics,
            }
        )
    return normalized


def _infer_topics_from_source(src: dict) -> List[str]:
    name = ""
    if src.get("type") == "json" and "url" in src:
        name = src["url"].rsplit("/", 1)[-1]
    elif src.get("type") == "file-json" and "path" in src:
        name = str(src["path"]).rsplit("/", 1)[-1]
    name = name.lower()
    topics: List[str] = []
    if "javascript" in name or name.endswith("js.json"):
        topics.append("javascript")
    if "python" in name:
        topics.append("python")
    if "ai-ml-data-science" in name:
        topics.extend(["ai", "machine learning", "data science"])
    if "devops" in name:
        topics.append("devops")
    return topics


def _augment_topics(item: dict, inferred: List[str]) -> None:
    topics = item.get("topics") or []
    if not topics:
        topics = list(inferred)
    # Heuristic from name
    lname = (item.get("name") or "").lower()
    if "python" in lname and "python" not in topics:
        topics.append("python")
    if ("javascript" in lname or " js" in lname) and "javascript" not in topics:
        topics.append("javascript")
    if any(k in lname for k in ["ai", "ml", "machine learning"]) and "ai" not in topics:
        topics.append("ai")
    if "kube" in lname or "kubernetes" in lname:
        if "kubernetes" not in topics:
            topics.append("kubernetes")
    item["topics"] = topics


def refresh_sources(timeout_s: float = 10.0) -> int:
    """Fetch all configured sources and persist a merged remote cache.

    Supported types:
    - json: fetch a JSON array of conference dicts
    - file-json: read a local JSON file with an array of conference dicts
    Returns: number of conferences saved
    """
    sources = load_sources()
    if not sources:
        # Seed with curated default sources (JSON URLs) so refresh has live data
        try:
            with resources.files("confradar.data").joinpath("default_sources.json").open("r", encoding="utf-8") as f:
                sources = json.load(f)
            save_sources(sources)
        except Exception:
            # Fallback: local bundled file
            try:
                builtin_path = resources.files("confradar.data").joinpath("conferences.json")
                sources = [{"type": "file-json", "path": str(builtin_path)}]
                save_sources(sources)
            except Exception:
                sources = []
    all_rows: List[dict] = []

    for src in sources:
        stype = src.get("type")
        try:
            if stype == "json":
                url = src["url"]
                with httpx.Client(timeout=timeout_s) as client:
                    resp = client.get(url)
                    resp.raise_for_status()
                    rows = resp.json()
                    if isinstance(rows, dict):
                        rows = rows.get("conferences", [])
                norm = _normalize_rows(rows)
                inferred = _infer_topics_from_source(src)
                for it in norm:
                    _augment_topics(it, inferred)
                all_rows.extend(norm)
            elif stype == "file-json":
                path = src["path"]
                with open(path, "r", encoding="utf-8") as f:
                    rows = json.load(f)
                norm = _normalize_rows(rows)
                inferred = _infer_topics_from_source(src)
                for it in norm:
                    _augment_topics(it, inferred)
                all_rows.extend(norm)
            else:
                # unsupported; skip
                continue
        except Exception:
            # Ignore failing source; proceed with others
            continue

    save_remote_conferences(all_rows)
    return len(all_rows)


