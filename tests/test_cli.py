import json
from pathlib import Path

from typer.testing import CliRunner

from confradar.cli import app
from confradar import storage


def test_cli_add_and_list(tmp_path, monkeypatch):
    # Redirect data dir to tmp
    monkeypatch.setattr(storage, "get_data_dir", lambda: Path(tmp_path))

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "add",
            "TestConf",
            "--start-date",
            "2025-07-01",
            "--end-date",
            "2025-07-03",
            "--city",
            "Remote",
            "--country",
            "Online",
            "--url",
            "https://example.com",
            "--topics",
            "ai,ml",
        ],
    )
    assert result.exit_code == 0

    result2 = runner.invoke(app, ["list", "--topic", "ai"])
    assert result2.exit_code == 0
    # output should contain our TestConf
    assert "TestConf" in result2.stdout


