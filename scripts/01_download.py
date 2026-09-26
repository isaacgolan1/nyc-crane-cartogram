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
