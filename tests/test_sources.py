from confradar.sources import _normalize_rows


def test_normalize_rows_maps_keys_and_topics():
    rows = [
        {
            "name": "Test",
            "url": "https://example.com",
            "startDate": "2025-01-01",
            "endDate": "2025-01-02",
            "city": "X",
            "country": "Y",
            "tags": ["ai", "ml"],
        },
        {
            "title": "Alt",
            "link": "https://example.org",
            "date": "2025-02-01",
            "topics": "python, web ",
        },
    ]
    out = _normalize_rows(rows)
    assert out[0]["start_date"] == "2025-01-01"
    assert out[0]["end_date"] == "2025-01-02"
    assert out[0]["topics"] == ["ai", "ml"]
    assert out[1]["name"] == "Alt"
    assert out[1]["url"] == "https://example.org"
    assert out[1]["topics"] == ["python", "web"]


