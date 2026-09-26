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
