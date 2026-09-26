"""Stage 3: remove duplicates, give every permit a location, and assign its neighborhood."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import pandas as pd

from src import config
from src.geo import (
    assign_nta, block_midpoint, load_centerline_streets, location_flags, reassign_park_edges, wkt_to_point,
)


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
    permits = reassign_park_edges(permits, nta)
    print(f"Moved from a park edge to the neighboring NTA: {permits['nta_reassigned'].sum():,}")
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
