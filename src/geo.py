"""Locations: street-name matching, centerline geocoding, neighborhood (NTA) assignment."""
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
