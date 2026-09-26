# Project 2: Permit Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce two permit-friction metrics per Manhattan neighborhood (median lead time and median distinctive-stipulation count) from DOT street crane permits.

**Architecture:** A five-stage script pipeline (`scripts/01_…` to `05_…`) built on small, tested modules in `src/`. Each stage writes a file to disk that the next stage reads. All boroughs are downloaded and cleaned; metrics are computed for the boroughs listed in `src/config.py`.

**Tech Stack:** Python 3.14 (`.venv`), pandas, geopandas, shapely, matplotlib, pytest, `curl` for all downloads.

**Spec:** `docs/superpowers/specs/2026-09-25-project2-permit-data-design.md`

## Global Constraints

- Run Python only as `.venv/bin/python` (or `.venv/bin/pytest`). Never `/usr/bin/python3`.
- All downloads go through `curl` via `src/download.py`. Python's `urllib` fails with `CERTIFICATE_VERIFY_FAILED` on this Mac.
- Read every downloaded CSV with `dtype=str`. `applicationtrackingid` has 16 digits and turns into a wrong float otherwise.
- Raw files in `data/raw/` are never edited. They are named `<name>_<YYYY-MM-DD>.<ext>`.
- Nothing disappears silently: every script prints a funnel (rows in, rows out, reason).
- Settings live in `src/config.py`: `BOROUGHS = ["MANHATTAN"]`, `START_DATE = "2022-01-01"`, `BOILERPLATE_CUTOFF = 0.90`, `MIN_PERMITS = 20`, `GEOCODE_FALLBACK_TRIGGER = 0.05`, `MAX_LEAD_TIME_DAYS = 365`.
- Do not import from or edit `reference/`.
- The user (Isaac) is new to geospatial work. Before running each new script, tell him what it does and what he should see. After each task, tell him how to verify it.
- Commit after each task. End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Spec corrections found while planning

These came from checking the real data on 2026-09-26. Task 1 updates the spec to match.

1. **Use `wkt`, not `locationgeometry`.** `locationgeometry` is a binary blob. `wkt` holds the same geometry as text, in EPSG:2263 (NY State Plane, feet). Both are empty on the same 3,907 permits.
2. **Normalize to `AVE`, not `AV`.** The centerline's `Street Name Label` uses `E 55 ST`, `1 AVE`, `MADISON AVE`. The same normalizer runs on permit names and centerline names, so both sides always agree.
3. **Application types are New, Renew, Reissue and Amend and Reissue.** Only `New` counts for lead time. All four count for stipulations.
4. **A block with only one matching cross street still geocodes**, to that intersection. Example: `E 57 ST` from `1 AVE` to `QNSBORO BRDG APPROACH`. It lands in the right neighborhood.

## File Structure

| File | Responsibility |
|---|---|
| `src/__init__.py` | Makes `src` a package (empty) |
| `src/config.py` | Settings, paths, dataset IDs, `latest_raw()` |
| `src/download.py` | curl wrapper: paging, batching, row-count check |
| `src/geo.py` | Street-name normalizer, centerline geocoding, NTA join, location flags |
| `src/permits.py` | Tracking-ID date parsing, verify check, lead time |
| `src/stipulations.py` | Code shares, boilerplate, distinctive counts, custom-text flag |
| `src/neighborhoods.py` | Per-NTA rollup with thresholds |
| `scripts/01_download.py` … `05_visualize.py` | Pipeline stages, run in order |
| `tests/test_*.py` | One test file per `src` module |
| `pytest.ini` | Lets tests import `src` |
| `requirements.txt` | Dependencies |

---

### Task 1: Environment, config and spec corrections

**Files:**
- Create: `requirements.txt`, `pytest.ini`, `src/__init__.py`, `src/config.py`, `tests/test_config.py`
- Modify: `.gitignore`, `docs/superpowers/specs/2026-09-25-project2-permit-data-design.md`

**Interfaces:**
- Produces: `src.config` module with `ROOT`, `RAW_DIR`, `PROCESSED_DIR`, `OUTPUTS_DIR`, `CENTERLINE_FILE`, `BOROUGHS: list[str]`, `START_DATE: str`, `END_DATE: str | None`, `BOILERPLATE_CUTOFF: float`, `MIN_PERMITS: int`, `GEOCODE_FALLBACK_TRIGGER: float`, `MAX_LEAD_TIME_DAYS: int`, `CRANE_PERMIT_TYPE: str`, `DATASETS: dict[str, str]`, `latest_raw(prefix: str, suffix: str = ".csv", raw_dir: Path = RAW_DIR) -> Path`

- [x] **Step 1: Create the virtual environment**

Tell Isaac: a virtual environment is a private copy of Python for this project, so packages installed here don't affect anything else on the Mac.

```bash
cd /Users/cas/Desktop/nyc-crane-cartogram
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 -m venv .venv
.venv/bin/python --version
```

Expected: `Python 3.14.x`

- [x] **Step 2: Write `requirements.txt` and install**

```text
pandas>=2.2
matplotlib>=3.8
geopandas>=1.0
shapely>=2.0
pytest>=8.0
```

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/python -c "import pandas, geopandas, shapely, matplotlib; print('ok', geopandas.__version__)"
```

Expected: `ok 1.x.x`. If `pip` fails with an SSL error, stop and report it. Do not work around it with `--trusted-host`.

- [x] **Step 3: Write `pytest.ini` and `src/__init__.py`**

`pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

`src/__init__.py`: empty file.

- [x] **Step 4: Write the failing test `tests/test_config.py`**

```python
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
```

- [x] **Step 5: Run the test to verify it fails**

Run: `.venv/bin/pytest tests/test_config.py -v`
Expected: FAIL with `ImportError: cannot import name 'config' from 'src'`

- [x] **Step 6: Write `src/config.py`**

```python
"""Project-wide settings. Change values here, not in the scripts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUTS_DIR = ROOT / "outputs"
CENTERLINE_FILE = RAW_DIR / "Centerline_20260828.csv"

# Boroughs that get metrics. Names match DOT's `boroughname` column.
# All boroughs are always downloaded and cleaned.
BOROUGHS = ["MANHATTAN"]

# Permit issue-date range. END_DATE None means "up to the latest record".
START_DATE = "2022-01-01"
END_DATE = None

BOILERPLATE_CUTOFF = 0.90         # codes on more than this share of permits are boilerplate
MIN_PERMITS = 20                  # below this, a neighborhood metric is left blank
GEOCODE_FALLBACK_TRIGGER = 0.05   # unmatched share that would justify adding NYC Geoclient
MAX_LEAD_TIME_DAYS = 365          # longer gaps are treated as data errors

CRANE_PERMIT_TYPE = "PLACE CRANE OR SHOVEL ON STREET"

# NYC Open Data (SODA API) dataset IDs
DATASETS = {
    "permits": "tqtj-sjs8",       # Street Construction Permits (2022-Present)
    "cranes": "hcv3-zacv",        # Street Construction Permits - Cranes
    "stipulations": "gsgx-6efw",  # Street Construction Permits - Stipulations (2020-Present)
    "nta": "9nt8-h7nd",           # 2020 Neighborhood Tabulation Areas
}


def latest_raw(prefix: str, suffix: str = ".csv", raw_dir: Path = RAW_DIR) -> Path:
    """Return the newest raw file named <prefix>_<YYYY-MM-DD><suffix>."""
    matches = sorted(raw_dir.glob(f"{prefix}_*{suffix}"))
    if not matches:
        raise FileNotFoundError(
            f"No file {prefix}_*{suffix} in {raw_dir}. Run scripts/01_download.py first."
        )
    return matches[-1]
```

- [x] **Step 7: Run the test to verify it passes**

Run: `.venv/bin/pytest tests/test_config.py -v`
Expected: 3 passed

- [x] **Step 8: Keep large processed files out of git**

Append to `.gitignore`:

```text

# Large processed files (rebuilt by scripts/03 and 04)
data/processed/crane_permit*.csv
data/processed/geocode_unmatched.csv
```

- [x] **Step 9: Apply the spec corrections**

In `docs/superpowers/specs/2026-09-25-project2-permit-data-design.md`:
- Stage 3 step 3: replace "Use `locationgeometry` where present." with "Use the `wkt` column where present (text geometry in EPSG:2263, feet). `locationgeometry` holds the same data as a binary blob and is not used."
- Stage 3 step 4 normalizer: replace "AVENUE→AV" with "AVENUE→AVE". Add: "The same normalizer runs on centerline names, so both sides always agree."
- Stage 3 step 4 matching: add "If only one cross street matches, use that intersection."
- Decisions table, Application types row: replace "(New, Renew, Reissue)" with "(New, Renew, Reissue, Amend and Reissue)".

- [x] **Step 10: Commit**

```bash
git add requirements.txt pytest.ini src/__init__.py src/config.py tests/test_config.py .gitignore docs/superpowers/specs/2026-09-25-project2-permit-data-design.md
git commit -m "Set up venv, config and tests for Project 2

Apply spec corrections found while planning (wkt column, AVE, four
application types, one-crossing geocode).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Tell Isaac how to verify: `.venv/bin/pytest -v` shows 3 passed.

---

### Task 2: Download module

**Files:**
- Create: `src/download.py`, `tests/test_download.py`

**Interfaces:**
- Produces:
  - `build_curl_command(url: str, params: dict[str, str]) -> list[str]`
  - `chunks(items: list[str], size: int) -> list[list[str]]`
  - `in_clause(column: str, values: list[str]) -> str`
  - `fetch_count(dataset_id: str, where: str | None = None) -> int`
  - `fetch_csv(dataset_id: str, where: str | None = None, select: str | None = None) -> pd.DataFrame` (all columns `str`, empty cells `NaN`; raises `RuntimeError` on row-count mismatch)
  - `fetch_csv_for_keys(dataset_id: str, column: str, keys: list[str], batch_size: int = 100, select: str | None = None) -> pd.DataFrame`
  - `fetch_geojson(dataset_id: str, out_path: Path) -> int` (returns feature count)

- [x] **Step 1: Write the failing test `tests/test_download.py`**

Only the pure helpers are tested. Network calls are checked by hand in Task 3.

```python
from src.download import build_curl_command, chunks, in_clause


def test_build_curl_command_encodes_each_param():
    cmd = build_curl_command(
        "https://example.org/resource/abcd-1234.csv",
        {"$where": "boroughname='MANHATTAN'", "$limit": "10"},
    )

    assert cmd[0] == "curl"
    assert "--fail" in cmd
    assert "--get" in cmd
    assert cmd[cmd.index("--retry") + 1] == "3"
    assert "https://example.org/resource/abcd-1234.csv" in cmd
    assert "$where=boroughname='MANHATTAN'" in cmd
    assert "$limit=10" in cmd


def test_chunks_splits_and_keeps_remainder():
    assert chunks(["a", "b", "c", "d", "e"], 2) == [["a", "b"], ["c", "d"], ["e"]]


def test_chunks_empty():
    assert chunks([], 100) == []


def test_in_clause_quotes_values():
    assert in_clause("permitnumber", ["M1", "B2"]) == "permitnumber in('M1','B2')"


def test_in_clause_escapes_single_quotes():
    assert in_clause("name", ["O'NEIL"]) == "name in('O''NEIL')"
```

- [x] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/pytest tests/test_download.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.download'`

- [x] **Step 3: Write `src/download.py`**

```python
"""Download NYC Open Data (SODA API) with curl.

Python's own HTTPS downloader fails with CERTIFICATE_VERIFY_FAILED on this Mac,
so every request goes through the curl program instead.
"""
import io
import json
import subprocess
from pathlib import Path

import pandas as pd

BASE_URL = "https://data.cityofnewyork.us/resource"
PAGE_SIZE = 50_000


def build_curl_command(url: str, params: dict[str, str]) -> list[str]:
    """curl arguments for a GET request with URL-encoded query parameters."""
    cmd = [
        "curl", "--silent", "--show-error", "--fail",
        "--retry", "3", "--retry-all-errors",
        "--get", url,
    ]
    for key, value in params.items():
        cmd += ["--data-urlencode", f"{key}={value}"]
    return cmd


def chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def in_clause(column: str, values: list[str]) -> str:
    """SoQL `column in('a','b')`, with single quotes escaped."""
    quoted = ",".join("'" + v.replace("'", "''") + "'" for v in values)
    return f"{column} in({quoted})"


def _run(url: str, params: dict[str, str]) -> str:
    result = subprocess.run(build_curl_command(url, params), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"curl failed after 3 retries for {url}\n{result.stderr.strip()}")
    return result.stdout


def fetch_count(dataset_id: str, where: str | None = None) -> int:
    """Number of rows the API says match `where`."""
    params = {"$select": "count(*)"}
    if where:
        params["$where"] = where
    text = _run(f"{BASE_URL}/{dataset_id}.json", params)
    return int(json.loads(text)[0]["count"])


def fetch_csv(dataset_id: str, where: str | None = None, select: str | None = None) -> pd.DataFrame:
    """Download every row matching `where`, page by page, as strings.

    Raises RuntimeError if the row count differs from the API's count(*).
    """
    pages = []
    offset = 0
    while True:
        params = {"$limit": str(PAGE_SIZE), "$offset": str(offset), "$order": ":id"}
        if where:
            params["$where"] = where
        if select:
            params["$select"] = select
        text = _run(f"{BASE_URL}/{dataset_id}.csv", params)
        page = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False, na_values=[""])
        pages.append(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    df = pd.concat(pages, ignore_index=True)
    expected = fetch_count(dataset_id, where)
    if len(df) != expected:
        raise RuntimeError(f"{dataset_id}: downloaded {len(df)} rows but the API reports {expected}.")
    return df


def fetch_csv_for_keys(
    dataset_id: str,
    column: str,
    keys: list[str],
    batch_size: int = 100,
    select: str | None = None,
) -> pd.DataFrame:
    """Download rows whose `column` is in `keys`, in batches (URLs have a length limit)."""
    batches = chunks(sorted(set(keys)), batch_size)
    frames = []
    for i, batch in enumerate(batches, start=1):
        frames.append(fetch_csv(dataset_id, where=in_clause(column, batch), select=select))
        print(f"  batch {i}/{len(batches)}", end="\r", flush=True)
    print()
    return pd.concat(frames, ignore_index=True)


def fetch_geojson(dataset_id: str, out_path: Path) -> int:
    """Save a map dataset as GeoJSON. Returns the feature count after checking it."""
    text = _run(f"{BASE_URL}/{dataset_id}.geojson", {"$limit": str(PAGE_SIZE)})
    features = len(json.loads(text)["features"])
    expected = fetch_count(dataset_id)
    if features != expected:
        raise RuntimeError(f"{dataset_id}: downloaded {features} features but the API reports {expected}.")
    out_path.write_text(text)
    return features
```

- [x] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/pytest tests/test_download.py -v`
Expected: 5 passed

- [x] **Step 5: Commit**

```bash
git add src/download.py tests/test_download.py
git commit -m "Add curl-based SODA download module

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Stage 1 script — download raw data

**Files:**
- Create: `scripts/01_download.py`

**Interfaces:**
- Consumes: `src.config`, `src.download.fetch_csv`, `fetch_csv_for_keys`, `fetch_geojson`
- Produces (in `data/raw/`, dated): `dot_crane_permits_<date>.csv`, `dot_crane_types_<date>.csv`, `dot_crane_stipulations_<date>.csv` (columns `permitnumber`, `stipulationid`, `stipulationfulltext`), `nta2020_<date>.geojson`

- [x] **Step 1: Write `scripts/01_download.py`**

```python
"""Stage 1: download DOT crane permits, crane types, stipulations and NTA boundaries.

All boroughs are downloaded. Filtering to config.BOROUGHS happens in stage 4.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config
from src.download import fetch_csv, fetch_csv_for_keys, fetch_geojson


def main() -> None:
    today = date.today().isoformat()
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)

    where = (
        f"permittypedesc='{config.CRANE_PERMIT_TYPE}'"
        f" AND permitissuedate>='{config.START_DATE}'"
    )
    if config.END_DATE:
        where += f" AND permitissuedate<'{config.END_DATE}'"

    print("1/4 Crane permits...")
    permits = fetch_csv(config.DATASETS["permits"], where=where)
    permits.to_csv(config.RAW_DIR / f"dot_crane_permits_{today}.csv", index=False)
    print(f"  {len(permits):,} permits (row count matches API)")
    print(permits["boroughname"].value_counts().to_string())

    numbers = permits["permitnumber"].dropna().tolist()

    print("2/4 Crane types...")
    cranes = fetch_csv_for_keys(config.DATASETS["cranes"], "permitnumber", numbers)
    cranes.to_csv(config.RAW_DIR / f"dot_crane_types_{today}.csv", index=False)
    print(f"  {len(cranes):,} rows")

    print("3/4 Stipulations (about 170 batches, several minutes)...")
    stips = fetch_csv_for_keys(
        config.DATASETS["stipulations"], "permitnumber", numbers,
        select="permitnumber,stipulationid,stipulationfulltext",
    )
    stips.to_csv(config.RAW_DIR / f"dot_crane_stipulations_{today}.csv", index=False)
    print(f"  {len(stips):,} rows for {stips['permitnumber'].nunique():,} permits")

    print("4/4 NTA boundaries...")
    n = fetch_geojson(config.DATASETS["nta"], config.RAW_DIR / f"nta2020_{today}.geojson")
    print(f"  {n} neighborhoods")

    print("Done.")


if __name__ == "__main__":
    main()
```

- [x] **Step 2: Tell Isaac what to expect, then run it**

What it does: downloads four files into `data/raw/`, checking each against the API's own row count. It takes about 5–10 minutes, mostly the stipulations batches.

What he should see: about 16,500 permits, a borough breakdown with Manhattan near 7,600, stipulations around 300,000 rows, and 262 neighborhoods.

Run: `.venv/bin/python scripts/01_download.py`

Expected: ends with `Done.` and no `RuntimeError`.

- [x] **Step 3: Verify by hand**

```bash
ls -lh data/raw/
head -3 data/raw/dot_crane_permits_*.csv | cut -c1-300
git status --short data/raw
```

Expected: four new dated files. `applicationtrackingid` shows 16 digits (not `2.02e+15`). `git status` shows nothing for `data/raw` because the files are gitignored.

- [x] **Step 4: Commit**

```bash
git add scripts/01_download.py
git commit -m "Add stage 1 download script

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Stage 2 — verify the tracking-ID date (decision gate)

**Files:**
- Create: `src/permits.py`, `tests/test_permits.py`, `scripts/02_verify_tracking_id.py`

**Interfaces:**
- Consumes: `data/raw/dot_crane_permits_<date>.csv`
- Produces:
  - `parse_tracking_date(tracking_id: object) -> pd.Timestamp` (`pd.NaT` when not a real date)
  - `application_gap_days(permits: pd.DataFrame) -> pd.Series` (float days, issue date minus application date; needs columns `applicationtrackingid`, `permitissuedate`)
  - `evaluate_tracking_dates(permits: pd.DataFrame) -> dict` with keys `rows`, `parsed_share`, `not_after_issue_share`, `median_gap_days`, `passed`

- [x] **Step 1: Write the failing test `tests/test_permits.py`**

```python
import pandas as pd

from src.permits import application_gap_days, evaluate_tracking_dates, parse_tracking_date


def test_parse_tracking_date_reads_first_8_digits():
    assert parse_tracking_date("2026092200673116") == pd.Timestamp("2026-09-22")


def test_parse_tracking_date_bad_input_is_nat():
    assert pd.isna(parse_tracking_date("20261399XXXX"))   # month 13
    assert pd.isna(parse_tracking_date("ABC"))
    assert pd.isna(parse_tracking_date(None))
    assert pd.isna(parse_tracking_date(float("nan")))


def _permits(rows):
    return pd.DataFrame(rows, columns=["applicationtrackingid", "permitissuedate"])


def test_application_gap_days():
    permits = _permits([["2026092200673116", "2026-09-25T13:59:14.000"]])
    assert application_gap_days(permits).tolist() == [3.0]


def test_evaluate_passes_on_plausible_data():
    permits = _permits([
        ["2026092200000001", "2026-09-25T10:00:00.000"],
        ["2026091900000002", "2026-09-25T10:00:00.000"],
        ["2026092100000003", "2026-09-25T10:00:00.000"],
    ])
    result = evaluate_tracking_dates(permits)
    assert result["parsed_share"] == 1.0
    assert result["median_gap_days"] == 4.0
    assert result["passed"] is True


def test_evaluate_fails_when_ids_do_not_parse():
    permits = _permits([
        ["2026092200000001", "2026-09-25T10:00:00.000"],
        ["NOTADATE00000002", "2026-09-25T10:00:00.000"],
    ])
    assert evaluate_tracking_dates(permits)["passed"] is False


def test_evaluate_fails_when_application_after_issue():
    permits = _permits([
        ["2026093000000001", "2026-09-25T10:00:00.000"],
        ["2026092200000002", "2026-09-25T10:00:00.000"],
    ])
    assert evaluate_tracking_dates(permits)["passed"] is False


def test_evaluate_fails_when_median_gap_implausible():
    permits = _permits([["2025010100000001", "2026-01-01T10:00:00.000"]])
    assert evaluate_tracking_dates(permits)["passed"] is False
```

- [x] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/pytest tests/test_permits.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.permits'`

- [x] **Step 3: Write `src/permits.py`**

```python
"""Permit timing: application date from the tracking ID, and lead time."""
import pandas as pd


def parse_tracking_date(tracking_id: object) -> pd.Timestamp:
    """Read the first 8 digits of applicationtrackingid as YYYYMMDD.

    Returns NaT when the value is missing or is not a real date.
    """
    if not isinstance(tracking_id, str) or len(tracking_id) < 8 or not tracking_id[:8].isdigit():
        return pd.NaT
    return pd.to_datetime(tracking_id[:8], format="%Y%m%d", errors="coerce")


def application_gap_days(permits: pd.DataFrame) -> pd.Series:
    """Days from the tracking-ID date to the permit issue date (NaN if unparsed)."""
    applied = pd.to_datetime(permits["applicationtrackingid"].map(parse_tracking_date))
    issued = pd.to_datetime(permits["permitissuedate"]).dt.normalize()
    return (issued - applied).dt.days.astype(float)


def evaluate_tracking_dates(permits: pd.DataFrame) -> dict:
    """Check whether the tracking-ID date behaves like an application date.

    Passes only if every ID parses, at least 99% of dates are on or before
    the issue date, and the median gap is between 1 and 60 days.
    """
    applied = pd.to_datetime(permits["applicationtrackingid"].map(parse_tracking_date))
    gap = application_gap_days(permits).dropna()
    parsed_share = float(applied.notna().mean())
    not_after_issue_share = float((gap >= 0).mean()) if len(gap) else 0.0
    median_gap_days = float(gap.median()) if len(gap) else float("nan")
    passed = bool(
        parsed_share == 1.0
        and not_after_issue_share >= 0.99
        and 1 <= median_gap_days <= 60
    )
    return {
        "rows": len(permits),
        "parsed_share": parsed_share,
        "not_after_issue_share": not_after_issue_share,
        "median_gap_days": median_gap_days,
        "passed": passed,
    }
```

- [x] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/pytest tests/test_permits.py -v`
Expected: 7 passed

- [x] **Step 5: Write `scripts/02_verify_tracking_id.py`**

```python
"""Stage 2: check whether applicationtrackingid's first 8 digits are an application date."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src import config
from src.permits import application_gap_days, evaluate_tracking_dates


def main() -> None:
    permits = pd.read_csv(config.latest_raw("dot_crane_permits"), dtype=str)
    result = evaluate_tracking_dates(permits)
    gap = application_gap_days(permits)

    print(f"Permits checked:                 {result['rows']:,}")
    print(f"IDs that parse as a real date:   {result['parsed_share']:.2%}   (need 100%)")
    print(f"Date on or before issue date:    {result['not_after_issue_share']:.2%}   (need >= 99%)")
    print(f"Median gap (days):               {result['median_gap_days']:.1f}   (need 1-60)")
    print("\nGap percentiles (days):")
    print(gap.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).round(1).to_string())
    print("\nMedian gap by application type:")
    print(gap.groupby(permits["applicationtypeshortdesc"]).median().to_string())
    print("\nSample of permits with negative gaps:")
    cols = ["permitnumber", "applicationtrackingid", "applicationtypeshortdesc", "permitissuedate"]
    print(permits.loc[gap < 0, cols].head(10).to_string(index=False))

    print("\nRESULT:", "PASS" if result["passed"] else "FAIL")
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
```

- [x] **Step 6: Check the data dictionary**

Open https://data.cityofnewyork.us/Transportation/Street-Construction-Permits-2022-Present-/tqtj-sjs8/about_data. Under "Attachments", open the data dictionary and search for "tracking". Write down what it says about `applicationtrackingid`, or that it says nothing. This goes in the Project 2 notes (Task 11).

- [x] **Step 7: Tell Isaac what to expect, then run it**

What it does: reads the permits file and tests the three pass rules from the spec. It prints the evidence and then PASS or FAIL.

What he should see: nearly 100% parsing, a median gap of a few days, and New permits with longer gaps than Renew.

Run: `.venv/bin/python scripts/02_verify_tracking_id.py`

- [x] **Step 8: Decision gate**

- **PASS:** continue to Task 5.
- **FAIL:** stop. Show Isaac the printed evidence. The spec says lead time is dropped and the DOB NOW fallback is decided with him before continuing. Do not change the pass rules to make it pass.

- [x] **Step 9: Commit**

```bash
git add src/permits.py tests/test_permits.py scripts/02_verify_tracking_id.py
git commit -m "Add tracking-ID date check (stage 2)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Record the PASS/FAIL result and the three numbers in the commit message body.

---

### Task 5: Street-name normalizer

**Files:**
- Create: `src/geo.py`, `tests/test_geo.py`

**Interfaces:**
- Produces: `normalize_street_name(name: object) -> str` (returns `""` for missing input; idempotent)

- [x] **Step 1: Write the failing test `tests/test_geo.py`**

```python
import pytest

from src.geo import normalize_street_name


@pytest.mark.parametrize("raw, expected", [
    ("EAST   55 STREET", "E 55 ST"),
    ("   1 AVENUE", "1 AVE"),
    ("WEST 42ND STREET", "W 42 ST"),
    ("MADISON AVENUE", "MADISON AVE"),
    ("VARICK STREET", "VARICK ST"),
    ("F D R DRIVE", "FDR DR"),
    ("FIRST AVENUE", "1 AVE"),
    ("AVENUE OF THE AMERICAS", "6 AVE"),
    ("St. Marks Place", "ST MARKS PL"),
    ("NORTH MOORE STREET", "N MOORE ST"),
    ("AVENUE A", "AVE A"),              # a lone letter is not joined
    ("E 55 ST", "E 55 ST"),            # centerline style is unchanged
    ("1 AVE", "1 AVE"),
    ("W  155 ST", "W 155 ST"),
])
def test_normalize_street_name(raw, expected):
    assert normalize_street_name(raw) == expected


def test_normalize_is_idempotent():
    once = normalize_street_name("EAST   55 STREET")
    assert normalize_street_name(once) == once


@pytest.mark.parametrize("missing", [None, float("nan"), "", "   "])
def test_normalize_missing_is_empty(missing):
    assert normalize_street_name(missing) == ""
```

- [x] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/pytest tests/test_geo.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.geo'`

- [x] **Step 3: Write `src/geo.py`**

```python
"""Locations: street-name matching, centerline geocoding, neighborhood (NTA) assignment."""
import re

_WORDS = {
    "EAST": "E", "WEST": "W", "NORTH": "N", "SOUTH": "S",
    "STREET": "ST", "AVENUE": "AVE", "PLACE": "PL", "DRIVE": "DR",
    "BOULEVARD": "BLVD", "ROAD": "RD", "SQUARE": "SQ", "PARKWAY": "PKWY",
    "LANE": "LN", "TERRACE": "TER",
    "FIRST": "1", "SECOND": "2", "THIRD": "3", "FOURTH": "4", "FIFTH": "5",
    "SIXTH": "6", "SEVENTH": "7", "EIGHTH": "8", "NINTH": "9", "TENTH": "10",
    "ELEVENTH": "11", "TWELFTH": "12",
}

# Whole-name aliases, applied after word replacement.
_ALIASES = {
    "AVE OF THE AMERICAS": "6 AVE",
}

_ORDINAL = re.compile(r"^(\d+)(ST|ND|RD|TH)$")


def normalize_street_name(name: object) -> str:
    """Put a street name in one standard form.

    Runs on both DOT permit names and centerline names, so the two match:
    "EAST   55 STREET" and "E 55 ST" both become "E 55 ST".
    """
    if not isinstance(name, str):
        return ""
    words = _join_letter_runs(name.upper().replace(".", "").split())
    words = [_ORDINAL.sub(r"\1", w) for w in words]
    words = [_WORDS.get(w, w) for w in words]
    result = " ".join(words)
    return _ALIASES.get(result, result)


def _join_letter_runs(words: list[str]) -> list[str]:
    """Join two or more single letters in a row: ["F", "D", "R", "DRIVE"] -> ["FDR", "DRIVE"].

    Runs before word replacement, so "EAST" -> "E" never joins with a neighbor.
    """
    out: list[str] = []
    run: list[str] = []
    for w in words:
        if len(w) == 1 and w.isalpha():
            run.append(w)
            continue
        if run:
            out.append("".join(run))
            run = []
        out.append(w)
    if run:
        out.append("".join(run))
    return out
```

- [x] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/pytest tests/test_geo.py -v`
Expected: all passed

- [x] **Step 5: Commit**

```bash
git add src/geo.py tests/test_geo.py
git commit -m "Add street-name normalizer

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Geometry helpers — permit point and centerline block midpoint

**Files:**
- Modify: `src/geo.py` (add functions below `normalize_street_name`)
- Modify: `tests/test_geo.py` (append tests)

**Interfaces:**
- Consumes: `normalize_street_name`
- Produces:
  - `wkt_to_point(text: object) -> Point | None` (midpoint of a line; `None` for missing or bad text)
  - `build_street_index(streets: gpd.GeoDataFrame) -> dict[tuple[str, str], BaseGeometry]` (input columns `borough`, `name`, `geometry`; key is `(borough, normalized name)`)
  - `load_centerline_streets(path: Path) -> dict[tuple[str, str], BaseGeometry]` (EPSG:2263, feet)
  - `block_midpoint(borough: str, on_street: object, from_street: object, to_street: object, streets: dict, tolerance_ft: float = 50.0) -> Point | None`
  - `BOROUGH_CODES: dict[str, str]` (`"1"` → `"MANHATTAN"` … `"5"` → `"STATEN ISLAND"`)

All geometry here is EPSG:2263 (feet). Conversion to lat/lon happens in stage 3.

- [x] **Step 1: Append the failing tests to `tests/test_geo.py`**

```python
import geopandas as gpd
from shapely.geometry import LineString, Point

from src.geo import block_midpoint, build_street_index, wkt_to_point


def test_wkt_to_point_line_midpoint():
    assert wkt_to_point("LINESTRING (0 0, 10 0)").equals(Point(5, 0))


def test_wkt_to_point_point_stays():
    assert wkt_to_point("POINT (3 4)").equals(Point(3, 4))


@pytest.mark.parametrize("bad", [None, float("nan"), "", "not wkt"])
def test_wkt_to_point_bad_is_none(bad):
    assert wkt_to_point(bad) is None


def _grid():
    """E 55 ST runs east-west at y=0. 1 AVE is at x=0, 2 AVE at x=600, 9 AVE far away."""
    streets = gpd.GeoDataFrame(
        {
            "borough": ["MANHATTAN"] * 4,
            "name": ["E 55 ST", "1 AVE", "2 AVE", "9 AVE"],
        },
        geometry=[
            LineString([(-100, 0), (1000, 0)]),
            LineString([(0, -500), (0, 500)]),
            LineString([(600, -500), (600, 500)]),
            LineString([(5000, 4000), (5000, 5000)]),
        ],
        crs=2263,
    )
    return build_street_index(streets)


def test_build_street_index_keys():
    index = _grid()
    assert ("MANHATTAN", "E 55 ST") in index
    assert len(index) == 4


def test_block_midpoint_between_two_crossings():
    point = block_midpoint("MANHATTAN", "EAST   55 STREET", "   1 AVENUE", "   2 AVENUE", _grid())
    assert point.equals(Point(300, 0))


def test_block_midpoint_one_crossing_uses_that_intersection():
    point = block_midpoint("MANHATTAN", "EAST 55 STREET", "1 AVENUE", "QNSBORO BRDG APPROACH", _grid())
    assert point.equals(Point(0, 0))


def test_block_midpoint_cross_street_too_far_is_ignored():
    assert block_midpoint("MANHATTAN", "E 55 ST", "9 AVE", "UNKNOWN", _grid()) is None


def test_block_midpoint_unknown_on_street_is_none():
    assert block_midpoint("MANHATTAN", "NOWHERE ST", "1 AVE", "2 AVE", _grid()) is None


def test_block_midpoint_wrong_borough_is_none():
    assert block_midpoint("BROOKLYN", "E 55 ST", "1 AVE", "2 AVE", _grid()) is None
```

Move the new imports to the top of the file next to the existing ones.

- [x] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_geo.py -v`
Expected: FAIL with `ImportError: cannot import name 'block_midpoint'`

- [x] **Step 3: Add the functions to `src/geo.py`**

Replace the single `import re` line at the top of `src/geo.py` with this import block:

```python
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
import shapely.wkt
from shapely.errors import GEOSException
from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points
```

Add below `normalize_street_name`:

```python
BOROUGH_CODES = {
    "1": "MANHATTAN", "2": "BRONX", "3": "BROOKLYN", "4": "QUEENS", "5": "STATEN ISLAND",
}


def wkt_to_point(text: object) -> Point | None:
    """One point for a permit's WKT geometry: the middle of a line, else a point inside it."""
    if not isinstance(text, str) or not text.strip():
        return None
    try:
        geom = shapely.wkt.loads(text)
    except GEOSException:
        return None
    if geom.is_empty:
        return None
    if geom.geom_type in ("LineString", "MultiLineString"):
        return geom.interpolate(0.5, normalized=True)
    return geom.representative_point()


def build_street_index(streets: gpd.GeoDataFrame) -> dict[tuple[str, str], BaseGeometry]:
    """Merge all segments of each street into one shape, keyed by (borough, normalized name)."""
    streets = streets.dropna(subset=["borough", "geometry"])
    streets = streets[streets["name"] != ""]
    return {
        key: shapely.union_all(group.geometry.values)
        for key, group in streets.groupby(["borough", "name"])
    }


def load_centerline_streets(path: Path) -> dict[tuple[str, str], BaseGeometry]:
    """Street index from the NYC centerline CSV, in EPSG:2263 (feet)."""
    df = pd.read_csv(path, usecols=["the_geom", "Borough Code", "Street Name Label"], dtype=str)
    df = df.dropna(subset=["the_geom"])
    gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkt(df["the_geom"]), crs=4326).to_crs(2263)
    gdf["borough"] = gdf["Borough Code"].map(BOROUGH_CODES)
    gdf["name"] = gdf["Street Name Label"].map(normalize_street_name)
    return build_street_index(gdf[["borough", "name", "geometry"]])


def _crossing(a: BaseGeometry, b: BaseGeometry, tolerance_ft: float) -> Point | None:
    """Where street a meets street b, if they come within tolerance_ft of each other."""
    on_a, on_b = nearest_points(a, b)
    return on_a if on_a.distance(on_b) <= tolerance_ft else None


def block_midpoint(
    borough: str,
    on_street: object,
    from_street: object,
    to_street: object,
    streets: dict[tuple[str, str], BaseGeometry],
    tolerance_ft: float = 50.0,
) -> Point | None:
    """Locate "on_street between from_street and to_street" as a point.

    Two crossings found: the midpoint between them. One found: that intersection.
    None found, or on_street unknown: None.
    """
    on = streets.get((borough, normalize_street_name(on_street)))
    if on is None:
        return None
    crossings = []
    for cross_name in (from_street, to_street):
        cross = streets.get((borough, normalize_street_name(cross_name)))
        if cross is not None:
            point = _crossing(on, cross, tolerance_ft)
            if point is not None:
                crossings.append(point)
    if not crossings:
        return None
    if len(crossings) == 1:
        return crossings[0]
    return LineString(crossings).interpolate(0.5, normalized=True)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_geo.py -v`
Expected: all passed

- [x] **Step 5: Commit**

```bash
git add src/geo.py tests/test_geo.py
git commit -m "Add permit point and centerline block geocoding

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Neighborhood assignment and location flags

**Files:**
- Modify: `src/geo.py` (append), `tests/test_geo.py` (append)

**Interfaces:**
- Produces:
  - `assign_nta(df: pd.DataFrame, nta: gpd.GeoDataFrame) -> pd.DataFrame` (input needs `lat`, `lon`; `nta` needs `nta2020`, `ntaname`, `boroname`, geometry. Returns a copy with added `nta2020`, `ntaname`, `nta_boroname`; NaN where no match or no location)
  - `location_flags(df: pd.DataFrame) -> pd.Series` (values `ok`, `outside_nta`, `borough_mismatch`, `no_location`; needs `lat`, `nta2020`, `nta_boroname`, `boroughname`)

- [x] **Step 1: Append the failing tests to `tests/test_geo.py`**

```python
import numpy as np
import pandas as pd
from shapely.geometry import box

from src.geo import assign_nta, location_flags


def _nta():
    return gpd.GeoDataFrame(
        {"nta2020": ["MN0101"], "ntaname": ["Test Hood"], "boroname": ["Manhattan"]},
        geometry=[box(0, 0, 1, 1)],
        crs=4326,
    )


def test_assign_nta_inside_outside_missing():
    df = pd.DataFrame({
        "lat": [0.5, 5.0, np.nan],
        "lon": [0.5, 5.0, np.nan],
    })
    out = assign_nta(df, _nta())
    assert out.loc[0, "nta2020"] == "MN0101"
    assert out.loc[0, "ntaname"] == "Test Hood"
    assert out.loc[0, "nta_boroname"] == "Manhattan"
    assert pd.isna(out.loc[1, "nta2020"])
    assert pd.isna(out.loc[2, "nta2020"])
    assert len(out) == 3


def test_location_flags():
    df = pd.DataFrame({
        "lat":          [0.5,         0.5,         5.0,     np.nan],
        "nta2020":      ["MN0101",    "MN0101",    np.nan,  np.nan],
        "nta_boroname": ["Manhattan", "Manhattan", np.nan,  np.nan],
        "boroughname":  ["MANHATTAN", "BROOKLYN",  "MANHATTAN", "MANHATTAN"],
    })
    assert location_flags(df).tolist() == ["ok", "borough_mismatch", "outside_nta", "no_location"]
```

Move the new imports to the top of the file.

- [x] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_geo.py -v`
Expected: FAIL with `ImportError: cannot import name 'assign_nta'`

- [x] **Step 3: Append to `src/geo.py`**

```python
def assign_nta(df: pd.DataFrame, nta: gpd.GeoDataFrame) -> pd.DataFrame:
    """Add the NTA each lat/lon point falls in. Rows without a location stay NaN."""
    located = df[df["lat"].notna() & df["lon"].notna()]
    points = gpd.GeoDataFrame(
        index=located.index,
        geometry=gpd.points_from_xy(located["lon"].astype(float), located["lat"].astype(float)),
        crs=4326,
    )
    joined = gpd.sjoin(
        points,
        nta[["nta2020", "ntaname", "boroname", "geometry"]].to_crs(4326),
        how="left",
        predicate="within",
    )
    joined = joined[~joined.index.duplicated(keep="first")]  # a point on a shared border matches twice

    out = df.copy()
    out["nta2020"] = joined["nta2020"]
    out["ntaname"] = joined["ntaname"]
    out["nta_boroname"] = joined["boroname"]
    return out


def location_flags(df: pd.DataFrame) -> pd.Series:
    """Why a permit can or cannot be used in neighborhood metrics."""
    flags = pd.Series("ok", index=df.index, dtype=object)
    flags[df["nta2020"].isna()] = "outside_nta"
    mismatch = df["nta2020"].notna() & (
        df["nta_boroname"].str.upper() != df["boroughname"].str.upper()
    )
    flags[mismatch] = "borough_mismatch"
    flags[df["lat"].isna()] = "no_location"
    return flags
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_geo.py -v`
Expected: all passed

- [x] **Step 5: Commit**

```bash
git add src/geo.py tests/test_geo.py
git commit -m "Add NTA assignment and location flags

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Stage 3 script — clean and locate permits (geocode gate)

**Files:**
- Create: `scripts/03_clean.py`

**Interfaces:**
- Consumes: raw permits CSV, `data/raw/Centerline_20260828.csv`, raw NTA GeoJSON; `wkt_to_point`, `load_centerline_streets`, `block_midpoint`, `assign_nta`, `location_flags`
- Produces:
  - `data/processed/crane_permits_clean.csv`: all raw permit columns plus `lat`, `lon`, `location_source` (`dot_geometry` / `centerline_geocode` / empty), `nta2020`, `ntaname`, `nta_boroname`, `location_flag`. One row per `permitnumber`. All boroughs.
  - `data/processed/geocode_unmatched.csv`: permits with no location, for inspection

- [x] **Step 1: Write `scripts/03_clean.py`**

```python
"""Stage 3: remove duplicates, give every permit a location, and assign its neighborhood."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import pandas as pd

from src import config
from src.geo import assign_nta, block_midpoint, load_centerline_streets, location_flags, wkt_to_point


def main() -> None:
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    permits = pd.read_csv(config.latest_raw("dot_crane_permits"), dtype=str)
    print(f"Raw permits:                         {len(permits):,}")

    permits = (
        permits.sort_values("modifiedon")
        .drop_duplicates("permitnumber", keep="last")
        .reset_index(drop=True)
    )
    print(f"After removing duplicate numbers:    {len(permits):,}")

    # 1. Location from DOT's own geometry
    points = permits["wkt"].map(wkt_to_point).astype(object)
    source = pd.Series(pd.NA, index=permits.index, dtype=object)
    source[points.notna()] = "dot_geometry"
    print(f"Located from DOT geometry:           {points.notna().sum():,}")

    # 2. Geocode the rest from street names
    missing = points.isna()
    print(f"Geocoding {missing.sum():,} permits from street names (loading centerline)...")
    streets = load_centerline_streets(config.CENTERLINE_FILE)
    geocoded = [
        block_midpoint(r.boroughname, r.onstreetname, r.fromstreetname, r.tostreetname, streets)
        for r in permits[missing].itertuples()
    ]
    points[missing] = pd.Series(geocoded, index=permits.index[missing], dtype=object)
    source[missing & points.notna()] = "centerline_geocode"
    print(f"Located by centerline geocoding:     {(source == 'centerline_geocode').sum():,}")

    # 3. Convert feet (EPSG:2263) to lat/lon
    located = points.notna()
    lonlat = gpd.GeoSeries(points[located].tolist(), index=permits.index[located], crs=2263).to_crs(4326)
    permits["lon"] = lonlat.x
    permits["lat"] = lonlat.y
    permits["location_source"] = source

    # 4. Neighborhood and flags
    nta = gpd.read_file(config.latest_raw("nta2020", ".geojson"))
    permits = assign_nta(permits, nta)
    permits["location_flag"] = location_flags(permits)

    print("\nLocation flags (all boroughs):")
    print(permits["location_flag"].value_counts().to_string())

    unmatched = permits[permits["location_flag"] == "no_location"]
    unmatched[["permitnumber", "boroughname", "onstreetname", "fromstreetname", "tostreetname"]].to_csv(
        config.PROCESSED_DIR / "geocode_unmatched.csv", index=False
    )

    in_scope = permits["boroughname"].isin(config.BOROUGHS)
    share = (permits.loc[in_scope, "location_flag"] == "no_location").mean()
    print(f"\nUnmatched share in {config.BOROUGHS}: {share:.1%} "
          f"(Geoclient fallback trigger: {config.GEOCODE_FALLBACK_TRIGGER:.0%})")
    if share > config.GEOCODE_FALLBACK_TRIGGER:
        print("ABOVE TRIGGER: review data/processed/geocode_unmatched.csv before continuing.")

    permits.to_csv(config.PROCESSED_DIR / "crane_permits_clean.csv", index=False)
    print(f"\nWrote {len(permits):,} rows to data/processed/crane_permits_clean.csv")


if __name__ == "__main__":
    main()
```

- [x] **Step 2: Tell Isaac what to expect, then run it**

What it does: removes duplicate permits, then gives each permit a location. It uses DOT's line when present and street-name geocoding otherwise. It then finds each permit's neighborhood and flags problems. Loading the centerline takes about a minute.

What he should see: a funnel, about 77% located from DOT geometry, most of the rest geocoded, and an unmatched share for Manhattan.

Run: `.venv/bin/python scripts/03_clean.py`

- [x] **Step 3: Geocode gate**

- **Unmatched share at or below 5%:** continue.
- **Above 5%:** open `data/processed/geocode_unmatched.csv` and look for repeating name patterns. First try adding aliases to `_ALIASES` in `src/geo.py`, each with a test in `tests/test_geo.py`, then rerun. If it is still above 5%, stop and discuss NYC Geoclient with Isaac, as the spec says.

- [x] **Step 4: Manual spot check (with Isaac)**

```bash
.venv/bin/python -c "
import pandas as pd
df = pd.read_csv('data/processed/crane_permits_clean.csv', dtype=str)
ok = df[(df.boroughname == 'MANHATTAN') & (df.location_flag == 'ok')]
print(ok.sample(5, random_state=1)[['permitnumber','permithousenumber','onstreetname','fromstreetname','tostreetname','location_source','ntaname','lat','lon']].to_string())
"
```

For each of the 5 rows, paste `lat,lon` into Google Maps. Confirm the pin sits on the named street and inside the named neighborhood. Include at least one `centerline_geocode` row; rerun with another `random_state` if none appear.

- [x] **Step 4b (added during execution): Park-edge fix**

The spot check found 820 Fifth Ave assigned to Central Park: 230 Manhattan permits on park-edge streets landed in park NTAs. Isaac chose option A: `reassign_park_edges` in `src/geo.py` (with 3 tests) moves points in a park NTA to the nearest non-park NTA within 100 ft. Result: 289 permits moved citywide; 4 Manhattan permits remain in Central Park (East Drive, inside the park). About 11% of points sit on a boundary between two regular NTAs; that stays as-is and goes in the notes.

- [x] **Step 5: Commit**

```bash
git add scripts/03_clean.py src/geo.py tests/test_geo.py
git commit -m "Add stage 3 clean script: dedupe, geocode, assign NTA

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Put the location-flag counts and the unmatched share in the commit message body.

---

### Task 9: Metric functions — lead time and stipulation burden

**Files:**
- Modify: `src/permits.py` (append), `tests/test_permits.py` (append)
- Create: `src/stipulations.py`, `tests/test_stipulations.py`

**Interfaces:**
- Consumes: `application_gap_days`, `config.MAX_LEAD_TIME_DAYS`
- Produces:
  - `lead_time_days(permits: pd.DataFrame, max_days: int = config.MAX_LEAD_TIME_DAYS) -> pd.Series` (float; NaN for non-New, emergency, unparsed or implausible)
  - `lead_time_exclusions(permits: pd.DataFrame, max_days: int = config.MAX_LEAD_TIME_DAYS) -> dict[str, int]` with keys `not_new`, `emergency`, `unparsed`, `implausible`, `used`
  - `code_shares(stips: pd.DataFrame, permit_numbers: pd.Series) -> pd.Series` (index `stipulationid`, value = share of those permits carrying it, sorted high to low)
  - `find_boilerplate_codes(shares: pd.Series, cutoff: float) -> set[str]`
  - `distinctive_stip_counts(stips: pd.DataFrame, permit_numbers: pd.Series, boilerplate: set[str]) -> pd.Series` (aligned to `permit_numbers` order; 0 for none)
  - `has_custom_text(text: pd.Series) -> pd.Series` (bool)

Lead time needs columns `applicationtrackingid`, `permitissuedate`, `applicationtypeshortdesc`, `emergencyissuedate`.

- [x] **Step 1: Append the failing lead-time tests to `tests/test_permits.py`**

```python
import numpy as np

from src.permits import lead_time_days, lead_time_exclusions


def _lead_permits():
    return pd.DataFrame(
        [
            ["2026092200000001", "2026-09-27T10:00:00.000", "New", np.nan],                      # used: 5 days
            ["2026092200000002", "2026-09-27T10:00:00.000", "Renew", np.nan],                    # not New
            ["2026092200000003", "2026-09-27T10:00:00.000", "New", "2026-09-23T00:00:00.000"],   # emergency
            ["2026093000000004", "2026-09-27T10:00:00.000", "New", np.nan],                      # negative
            ["2025010100000005", "2026-09-27T10:00:00.000", "New", np.nan],                      # > 365 days
            ["BADID", "2026-09-27T10:00:00.000", "New", np.nan],                                 # unparsed
        ],
        columns=["applicationtrackingid", "permitissuedate", "applicationtypeshortdesc", "emergencyissuedate"],
    )


def test_lead_time_days_only_keeps_plausible_new_permits():
    result = lead_time_days(_lead_permits())
    assert result.iloc[0] == 5.0
    assert result.iloc[1:].isna().all()


def test_lead_time_exclusions_counts_each_reason():
    assert lead_time_exclusions(_lead_permits()) == {
        "not_new": 1, "emergency": 1, "unparsed": 1, "implausible": 2, "used": 1,
    }
```

- [x] **Step 2: Write the failing test `tests/test_stipulations.py`**

```python
import pandas as pd

from src.stipulations import (
    code_shares, distinctive_stip_counts, find_boilerplate_codes, has_custom_text,
)


def _stips():
    """10 permits. Code A on all 10, B on 9, C on permit P0 only. P9 has only A."""
    rows = [(f"P{i}", "A") for i in range(10)]
    rows += [(f"P{i}", "B") for i in range(9)]
    rows += [("P0", "C"), ("P0", "C")]  # a duplicate row must not count twice
    return pd.DataFrame(rows, columns=["permitnumber", "stipulationid"])


PERMITS = pd.Series([f"P{i}" for i in range(10)] + ["P10"])  # P10 has no stipulations


def test_code_shares():
    shares = code_shares(_stips(), PERMITS)
    assert shares["A"] == 10 / 11
    assert shares["B"] == 9 / 11
    assert shares["C"] == 1 / 11
    assert shares.index[0] == "A"


def test_find_boilerplate_codes_uses_strictly_greater():
    shares = pd.Series({"A": 0.95, "B": 0.90, "C": 0.10})
    assert find_boilerplate_codes(shares, 0.90) == {"A"}


def test_distinctive_stip_counts():
    counts = distinctive_stip_counts(_stips(), PERMITS, boilerplate={"A"})
    assert counts.tolist() == [2, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]


def test_has_custom_text():
    text = pd.Series(["MUST PROVIDE FLAGGERS", "", "   ", None])
    assert has_custom_text(text).tolist() == [True, False, False, False]
```

- [x] **Step 3: Run the tests to verify they fail**

Run: `.venv/bin/pytest tests/test_permits.py tests/test_stipulations.py -v`
Expected: FAIL with `ImportError: cannot import name 'lead_time_days'` and `ModuleNotFoundError: No module named 'src.stipulations'`

- [x] **Step 4: Append to `src/permits.py`**

Add `from src import config` below `import pandas as pd`, then append:

```python
def _lead_time_masks(permits: pd.DataFrame, max_days: int) -> dict[str, pd.Series]:
    gap = application_gap_days(permits)
    is_new = permits["applicationtypeshortdesc"] == "New"
    emergency = is_new & permits["emergencyissuedate"].notna()
    candidate = is_new & ~emergency
    unparsed = candidate & gap.isna()
    implausible = candidate & gap.notna() & ~gap.between(0, max_days)
    used = candidate & gap.between(0, max_days)
    return {
        "gap": gap, "not_new": ~is_new, "emergency": emergency,
        "unparsed": unparsed, "implausible": implausible, "used": used,
    }


def lead_time_days(permits: pd.DataFrame, max_days: int = config.MAX_LEAD_TIME_DAYS) -> pd.Series:
    """Days from application to issue, for New non-emergency permits with a plausible gap."""
    masks = _lead_time_masks(permits, max_days)
    return masks["gap"].where(masks["used"])


def lead_time_exclusions(permits: pd.DataFrame, max_days: int = config.MAX_LEAD_TIME_DAYS) -> dict[str, int]:
    """How many permits each lead-time rule removed, and how many were used."""
    masks = _lead_time_masks(permits, max_days)
    return {k: int(masks[k].sum()) for k in ("not_new", "emergency", "unparsed", "implausible", "used")}
```

- [x] **Step 5: Write `src/stipulations.py`**

```python
"""Stipulation burden: which codes are boilerplate, and how many distinctive codes a permit has."""
import pandas as pd


def code_shares(stips: pd.DataFrame, permit_numbers: pd.Series) -> pd.Series:
    """Share of the given permits that carry each stipulation code, highest first."""
    permits = set(permit_numbers)
    relevant = stips[stips["permitnumber"].isin(permits)].drop_duplicates(["permitnumber", "stipulationid"])
    counts = relevant.groupby("stipulationid")["permitnumber"].nunique()
    return (counts / len(permits)).sort_values(ascending=False)


def find_boilerplate_codes(shares: pd.Series, cutoff: float) -> set[str]:
    """Codes on more than `cutoff` of permits. They add the same amount everywhere."""
    return set(shares[shares > cutoff].index)


def distinctive_stip_counts(stips: pd.DataFrame, permit_numbers: pd.Series, boilerplate: set[str]) -> pd.Series:
    """Number of non-boilerplate codes per permit, in the order of `permit_numbers`."""
    relevant = stips[~stips["stipulationid"].isin(boilerplate)].drop_duplicates(["permitnumber", "stipulationid"])
    counts = relevant.groupby("permitnumber")["stipulationid"].nunique()
    return counts.reindex(permit_numbers.tolist(), fill_value=0).reset_index(drop=True)


def has_custom_text(text: pd.Series) -> pd.Series:
    """True where DOT wrote site-specific conditions in `specificstipulations`."""
    return text.fillna("").str.strip() != ""
```

- [x] **Step 6: Run the tests to verify they pass**

Run: `.venv/bin/pytest -v`
Expected: all passed (every test file)

- [x] **Step 7: Commit**

```bash
git add src/permits.py tests/test_permits.py src/stipulations.py tests/test_stipulations.py
git commit -m "Add lead time and stipulation burden functions

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Neighborhood rollup and stage 4 script

**Files:**
- Create: `src/neighborhoods.py`, `tests/test_neighborhoods.py`, `scripts/04_analyze.py`

**Interfaces:**
- Consumes: everything from Task 9; `crane_permits_clean.csv`; raw stipulations CSV; raw NTA GeoJSON
- Produces:
  - `rollup_by_nta(permits: pd.DataFrame, ntas: pd.DataFrame, min_permits: int) -> pd.DataFrame` (permits need `nta2020`, `lead_time_days`, `distinctive_stip_count`, `has_custom_text`; ntas need `nta2020`, `ntaname`, `boroname`)
  - Output columns, in order: `nta2020`, `nta_name`, `borough`, `n_permits`, `n_new_permits`, `median_lead_time_days`, `median_distinctive_stips`, `pct_custom_text`, `insufficient_data`
  - Files in `data/processed/`: `permit_friction_by_nta.csv`, `crane_permit_metrics.csv` (per-permit metrics, in scope), `stipulation_code_shares.csv` (citywide, with `boilerplate` column), `distinctive_code_frequency.csv` (in scope: `stipulationid`, `share`, `text`)

`n_new_permits` counts New permits with a usable lead time. That is the number the lead-time threshold applies to.

- [x] **Step 1: Write the failing test `tests/test_neighborhoods.py`**

```python
import numpy as np
import pandas as pd

from src.neighborhoods import rollup_by_nta

NTAS = pd.DataFrame({
    "nta2020": ["MN01", "MN02", "MN03"],
    "ntaname": ["Big", "Small", "Empty"],
    "boroname": ["Manhattan"] * 3,
})


def _permits():
    big = pd.DataFrame({
        "nta2020": ["MN01"] * 20,
        "lead_time_days": [5.0] * 20,
        "distinctive_stip_count": [3] * 20,
        "has_custom_text": [True] * 10 + [False] * 10,
    })
    small = pd.DataFrame({
        "nta2020": ["MN02"] * 19,
        "lead_time_days": [9.0] * 19,
        "distinctive_stip_count": [7] * 19,
        "has_custom_text": [False] * 19,
    })
    return pd.concat([big, small], ignore_index=True)


def test_rollup_at_threshold_gets_metrics():
    row = rollup_by_nta(_permits(), NTAS, min_permits=20).set_index("nta2020").loc["MN01"]
    assert row["n_permits"] == 20
    assert row["n_new_permits"] == 20
    assert row["median_lead_time_days"] == 5.0
    assert row["median_distinctive_stips"] == 3.0
    assert row["pct_custom_text"] == 50.0
    assert not row["insufficient_data"]


def test_rollup_below_threshold_is_blank_and_flagged():
    row = rollup_by_nta(_permits(), NTAS, min_permits=20).set_index("nta2020").loc["MN02"]
    assert row["n_permits"] == 19
    assert np.isnan(row["median_lead_time_days"])
    assert np.isnan(row["median_distinctive_stips"])
    assert row["insufficient_data"]


def test_rollup_keeps_neighborhoods_with_no_permits():
    table = rollup_by_nta(_permits(), NTAS, min_permits=20)
    row = table.set_index("nta2020").loc["MN03"]
    assert row["n_permits"] == 0
    assert row["insufficient_data"]
    assert list(table.columns) == [
        "nta2020", "nta_name", "borough", "n_permits", "n_new_permits",
        "median_lead_time_days", "median_distinctive_stips", "pct_custom_text", "insufficient_data",
    ]


def test_rollup_lead_time_threshold_uses_usable_new_permits():
    permits = _permits()
    permits.loc[permits["nta2020"] == "MN01", "lead_time_days"] = [5.0] * 19 + [np.nan]
    row = rollup_by_nta(permits, NTAS, min_permits=20).set_index("nta2020").loc["MN01"]
    assert row["n_new_permits"] == 19
    assert np.isnan(row["median_lead_time_days"])
    assert row["median_distinctive_stips"] == 3.0
    assert row["insufficient_data"]
```

- [x] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/pytest tests/test_neighborhoods.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.neighborhoods'`

- [x] **Step 3: Write `src/neighborhoods.py`**

```python
"""Roll permit-level metrics up to one row per neighborhood (NTA)."""
import numpy as np
import pandas as pd


def rollup_by_nta(permits: pd.DataFrame, ntas: pd.DataFrame, min_permits: int) -> pd.DataFrame:
    """Median metrics per NTA. Every NTA in `ntas` appears, even with zero permits.

    A metric is left blank when its sample is below `min_permits`.
    """
    g = permits.groupby("nta2020")
    stats = pd.DataFrame({
        "n_permits": g.size(),
        "n_new_permits": g["lead_time_days"].count(),
        "median_lead_time_days": g["lead_time_days"].median(),
        "median_distinctive_stips": g["distinctive_stip_count"].median().astype(float),
        "pct_custom_text": g["has_custom_text"].mean().astype(float) * 100,
    })

    table = (
        ntas[["nta2020", "ntaname", "boroname"]]
        .rename(columns={"ntaname": "nta_name", "boroname": "borough"})
        .merge(stats, left_on="nta2020", right_index=True, how="left")
    )
    table[["n_permits", "n_new_permits"]] = table[["n_permits", "n_new_permits"]].fillna(0).astype(int)
    table.loc[table["n_new_permits"] < min_permits, "median_lead_time_days"] = np.nan
    table.loc[table["n_permits"] < min_permits, "median_distinctive_stips"] = np.nan
    table["insufficient_data"] = (
        table["median_lead_time_days"].isna() | table["median_distinctive_stips"].isna()
    )
    return table.sort_values("nta2020").reset_index(drop=True)
```

- [x] **Step 4: Run the test to verify it passes**

Run: `.venv/bin/pytest tests/test_neighborhoods.py -v`
Expected: 4 passed

- [x] **Step 5: Write `scripts/04_analyze.py`**

```python
"""Stage 4: compute lead time and stipulation burden per permit, then per neighborhood."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import pandas as pd

from src import config
from src.neighborhoods import rollup_by_nta
from src.permits import lead_time_days, lead_time_exclusions
from src.stipulations import code_shares, distinctive_stip_counts, find_boilerplate_codes, has_custom_text


def main() -> None:
    permits = pd.read_csv(config.PROCESSED_DIR / "crane_permits_clean.csv", dtype=str)
    stips = pd.read_csv(config.latest_raw("dot_crane_stipulations"), dtype=str)
    nta = gpd.read_file(config.latest_raw("nta2020", ".geojson"))

    # Boilerplate from ALL citywide crane permits, before location flags, so adding
    # a borough later never changes which codes count.
    shares = code_shares(stips, permits["permitnumber"])
    boilerplate = find_boilerplate_codes(shares, config.BOILERPLATE_CUTOFF)
    shares.rename("share").to_frame().assign(boilerplate=lambda d: d.index.isin(boilerplate)).to_csv(
        config.PROCESSED_DIR / "stipulation_code_shares.csv"
    )
    print(f"{len(shares)} stipulation codes citywide; {len(boilerplate)} boilerplate (> {config.BOILERPLATE_CUTOFF:.0%}):")
    print("  " + ", ".join(sorted(boilerplate)))

    permits["distinctive_stip_count"] = distinctive_stip_counts(stips, permits["permitnumber"], boilerplate).values
    permits["has_custom_text"] = has_custom_text(permits["specificstipulations"])
    permits["lead_time_days"] = lead_time_days(permits)

    in_scope = permits[permits["boroughname"].isin(config.BOROUGHS) & (permits["location_flag"] == "ok")]
    print(f"\nPermits in {config.BOROUGHS} with a usable location: {len(in_scope):,}")
    print("Lead-time funnel (in scope):", lead_time_exclusions(in_scope))

    # Embargo codes depend on timing as well as place; report how much they contribute.
    scope_stips = stips[stips["permitnumber"].isin(in_scope["permitnumber"]) & ~stips["stipulationid"].isin(boilerplate)]
    scope_stips = scope_stips.drop_duplicates(["permitnumber", "stipulationid"])
    embargo_share = scope_stips["stipulationid"].str.startswith("SE").mean()
    print(f"Share of distinctive code uses that are embargo (SE...) codes: {embargo_share:.1%}")

    # Most common distinctive codes in scope, with their text, for chart 4
    scope_shares = code_shares(stips, in_scope["permitnumber"]).drop(list(boilerplate), errors="ignore")
    texts = stips.drop_duplicates("stipulationid").set_index("stipulationid")["stipulationfulltext"]
    scope_shares.rename("share").to_frame().join(texts.rename("text")).to_csv(
        config.PROCESSED_DIR / "distinctive_code_frequency.csv"
    )

    ntas = nta[nta["boroname"].str.upper().isin(config.BOROUGHS)]
    table = rollup_by_nta(in_scope, ntas, config.MIN_PERMITS)
    table.to_csv(config.PROCESSED_DIR / "permit_friction_by_nta.csv", index=False)

    metric_cols = ["permitnumber", "boroughname", "nta2020", "ntaname", "applicationtypeshortdesc",
                   "lead_time_days", "distinctive_stip_count", "has_custom_text"]
    in_scope[metric_cols].to_csv(config.PROCESSED_DIR / "crane_permit_metrics.csv", index=False)

    print(f"\n{len(table)} neighborhoods; {table['insufficient_data'].sum()} flagged insufficient_data")
    ranked = table.dropna(subset=["median_lead_time_days"]).sort_values("median_lead_time_days", ascending=False)
    print("\nHighest median lead time:")
    print(ranked.head(5)[["nta_name", "n_new_permits", "median_lead_time_days"]].to_string(index=False))
    ranked = table.dropna(subset=["median_distinctive_stips"]).sort_values("median_distinctive_stips", ascending=False)
    print("\nHighest median distinctive stipulations:")
    print(ranked.head(5)[["nta_name", "n_permits", "median_distinctive_stips"]].to_string(index=False))


if __name__ == "__main__":
    main()
```

- [x] **Step 6: Tell Isaac what to expect, then run it**

What it does: finds the boilerplate codes, counts distinctive stipulations and lead time per permit, then takes medians per Manhattan neighborhood.

What he should see: about 9 boilerplate codes (the spike found `012`, `038`, `066`, `091`, `103`, `NOISE1`, `ODV`, `SCHOOL`, `TMC001`), about 35–40 Manhattan neighborhoods with some flagged, and top-5 lists.

Run: `.venv/bin/python scripts/04_analyze.py`

- [x] **Step 7: Sanity check (with Isaac)**

Do Midtown and Financial District neighborhoods rank near the top for stipulations? Do parks (for example Central Park) show `insufficient_data`? If quiet residential areas rank highest, look for a bug before believing it. For example, check that `distinctive_stip_count` is not 0 for most permits, which would mean the permit numbers didn't join.

Also open `data/processed/permit_friction_by_nta.csv` in Excel and scan it.

- [x] **Step 8: Commit**

```bash
git add src/neighborhoods.py tests/test_neighborhoods.py scripts/04_analyze.py data/processed/permit_friction_by_nta.csv data/processed/distinctive_code_frequency.csv data/processed/stipulation_code_shares.csv
git commit -m "Add neighborhood rollup and stage 4 analysis

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Stage 5 — charts

**Files:**
- Create: `scripts/05_visualize.py`

**Interfaces:**
- Consumes: `crane_permit_metrics.csv`, `permit_friction_by_nta.csv`, `distinctive_code_frequency.csv`
- Produces: `outputs/p2_lead_time_distribution.png`, `outputs/p2_lead_time_by_nta.png`, `outputs/p2_stipulations_by_nta.png`, `outputs/p2_top_distinctive_codes.png`

- [x] **Step 1: Load the dataviz skill**

Invoke the `dataviz` skill before writing chart code and apply its guidance on color, labels and axes to the code below. Keep the four charts and file names unchanged.

- [x] **Step 2: Write `scripts/05_visualize.py`**

```python
"""Stage 5: four charts of the permit-friction results."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src import config

LOW, HIGH = "#9ecae1", "#08519c"   # low friction, high friction
SCOPE = ", ".join(b.title() for b in config.BOROUGHS)


def save(fig, name: str) -> None:
    config.OUTPUTS_DIR.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(config.OUTPUTS_DIR / name, dpi=150)
    plt.close(fig)
    print(f"  outputs/{name}")


def top_bottom_chart(table: pd.DataFrame, column: str, xlabel: str, title: str, name: str, n: int = 10) -> None:
    ranked = table.dropna(subset=[column]).sort_values(column)
    bottom, top = ranked.head(n), ranked.tail(n)
    subset = pd.concat([bottom, top[~top["nta2020"].isin(bottom["nta2020"])]])
    colors = [LOW if code in set(bottom["nta2020"]) else HIGH for code in subset["nta2020"]]

    fig, ax = plt.subplots(figsize=(8, 0.35 * len(subset) + 1.5))
    ax.barh(subset["nta_name"], subset[column], color=colors)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, name)


def main() -> None:
    metrics = pd.read_csv(config.PROCESSED_DIR / "crane_permit_metrics.csv")
    table = pd.read_csv(config.PROCESSED_DIR / "permit_friction_by_nta.csv")
    codes = pd.read_csv(config.PROCESSED_DIR / "distinctive_code_frequency.csv")

    # 1. Lead-time distribution
    lead = metrics["lead_time_days"].dropna()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(lead.clip(upper=60), bins=range(0, 62), color=HIGH)
    ax.axvline(lead.median(), color="black", linestyle="--", linewidth=1)
    ax.text(lead.median() + 1, ax.get_ylim()[1] * 0.9, f"median {lead.median():.0f} days")
    ax.set_xlabel("Days from application to issue (60+ grouped at 60)")
    ax.set_ylabel("New crane permits")
    ax.set_title(f"Crane permit lead time, {SCOPE}, {config.START_DATE[:4]}–present (n={len(lead):,})")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "p2_lead_time_distribution.png")

    # 2 and 3. Top and bottom neighborhoods
    top_bottom_chart(table, "median_lead_time_days", "Median days from application to issue",
                     f"Crane permit lead time by neighborhood, {SCOPE}", "p2_lead_time_by_nta.png")
    top_bottom_chart(table, "median_distinctive_stips", "Median distinctive stipulations per permit",
                     f"Crane permit stipulation burden by neighborhood, {SCOPE}", "p2_stipulations_by_nta.png")

    # 4. Most common distinctive codes
    top = codes.head(15).iloc[::-1]
    labels = [f"{c}: {str(t)[:55]}…" for c, t in zip(top["stipulationid"], top["text"])]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(labels, top["share"] * 100, color=HIGH)
    ax.set_xlabel("% of crane permits carrying this code")
    ax.set_title(f"Most common non-boilerplate stipulations, {SCOPE}")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "p2_top_distinctive_codes.png")


if __name__ == "__main__":
    main()
```

- [x] **Step 3: Tell Isaac what to expect, then run it**

What it does: reads the stage 4 files and saves four PNG charts to `outputs/`.

Run: `.venv/bin/python scripts/05_visualize.py`
Expected: four `outputs/p2_*.png` lines printed.

- [x] **Step 4: Verify by eye (with Isaac)**

Open each PNG. Check that labels are readable, no neighborhood names are cut off, and light bars are the lowest values. Check that the numbers match the top-5 lists printed by stage 4.

- [x] **Step 5: Commit**

```bash
git add scripts/05_visualize.py outputs/p2_*.png
git commit -m "Add stage 5 charts

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 12: Project 2 notes and CLAUDE.md

**Files:**
- Create: `docs/PROJECT_2_NOTES.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write `docs/PROJECT_2_NOTES.md`**

Use the numbers the scripts printed. Write it for a portfolio reader who doesn't know the project. Use these sections:

1. **Question**: permit friction for street cranes, per Manhattan neighborhood, and why DOT permits instead of DOB.
2. **Data**: the four datasets with IDs, the date range and the download date.
3. **Method**: lead time (New only, exclusions), stipulation burden (boilerplate cutoff, distinctive count, custom text), the 20-permit threshold, and geocoding.
4. **Data quality funnel**: the counts from stages 1–4 (raw, duplicates, located by DOT geometry, geocoded, each location flag, lead-time exclusions). Include the tracking-ID check numbers and what the data dictionary said.
5. **Findings**: top and bottom neighborhoods for each metric, the median lead time, the most common distinctive codes, the embargo share, and the four charts linked from `outputs/`.
6. **Limitations**: tracking-ID date is inferred (or confirmed, per Step 6 of Task 4), embargo codes mix time and place, the 90% cutoff is a shortcut, and pre-2022 data is unused.
7. **Next questions**: Option C cost buckets, renewal chains, other boroughs, and what Project 4 needs from these two metrics.

- [ ] **Step 2: Update `CLAUDE.md`**

- In "Project structure", mark Project 2 done and Project 3 current.
- Under "Permit data sources", replace the sentence that starts "Project 2 design:" with: "Project 2 is done (design: `docs/superpowers/specs/2026-09-25-project2-permit-data-design.md`). Pipeline: run `scripts/01_download.py` to `05_visualize.py` in order. Results: `docs/PROJECT_2_NOTES.md`."
- Add to "Data gotchas already learned":
  - "DOT permits: use the `wkt` column (EPSG:2263, feet). `locationgeometry` is a binary blob."
  - "Read DOT CSVs with `dtype=str`. `applicationtrackingid` has 16 digits and becomes a wrong float otherwise."
  - "DOT application types: New, Renew, Reissue, Amend and Reissue."
  - Any new gotcha found during Tasks 3–11.

- [ ] **Step 3: Run the full test suite one last time**

Run: `.venv/bin/pytest -v`
Expected: all passed

- [ ] **Step 4: Commit**

```bash
git add docs/PROJECT_2_NOTES.md CLAUDE.md
git commit -m "Add Project 2 notes and update CLAUDE.md

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Tell Isaac how to verify: read `docs/PROJECT_2_NOTES.md` start to finish. Every number in it should appear in a script's printed output.
