import types
from confradar import core


def test_filter_conferences_topic_filter():
    c1 = core.Conference(
        name="PyCon",
        start_date="2025-01-01",
        end_date="2025-01-03",
        city="X",
        country="Y",
        url="https://example.com",
        topics=["python"],
    )
    c2 = core.Conference(
        name="JSConf",
        start_date="2025-02-01",
        end_date="2025-02-03",
        city="X",
        country="Y",
        url="https://example.com",
        topics=["javascript"],
    )
    out = core.filter_conferences([c1, c2], topic="python")
    assert [c.name for c in out] == ["PyCon"]


def test_load_conferences_uses_bundled(monkeypatch):
    monkeypatch.setattr(core, "load_user_conferences", lambda: [])
    monkeypatch.setattr(core, "load_remote_conferences", lambda: [])
    confs = core.load_conferences()
    assert isinstance(confs, list)
    assert confs and isinstance(confs[0], core.Conference)


