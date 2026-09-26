from pathlib import Path

import pytest

from src import config


def test_latest_raw_picks_newest_date(tmp_path: Path):
    (tmp_path / "dot_crane_permits_2026-09-01.csv").write_text("a")
    (tmp_path / "dot_crane_permits_2026-09-26.csv").write_text("b")
    (tmp_path / "other_2026-12-31.csv").write_text("c")

    result = config.latest_raw("dot_crane_permits", raw_dir=tmp_path)

    assert result.name == "dot_crane_permits_2026-09-26.csv"


def test_latest_raw_missing_file_explains_what_to_run(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="01_download.py"):
        config.latest_raw("dot_crane_permits", raw_dir=tmp_path)


def test_settings_match_spec():
    assert config.BOROUGHS == ["MANHATTAN"]
    assert config.START_DATE == "2022-01-01"
    assert config.BOILERPLATE_CUTOFF == 0.90
    assert config.MIN_PERMITS == 20
