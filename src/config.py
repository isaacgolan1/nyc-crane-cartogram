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
