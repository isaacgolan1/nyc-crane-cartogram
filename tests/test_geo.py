import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import LineString, Point, box

from src.geo import (
    assign_nta, block_midpoint, build_street_index, location_flags, normalize_street_name,
    reassign_park_edges, wkt_to_point,
)


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


def _park_and_hood():
    """In feet: a regular neighborhood from x=0 to 1000, a park from x=1000 to 2000."""
    return gpd.GeoDataFrame(
        {
            "nta2020": ["MN0501", "MN9991"],
            "ntaname": ["Upper East Side", "Central Park"],
            "boroname": ["Manhattan", "Manhattan"],
            "ntatype": ["0", "9"],
        },
        geometry=[box(0, 0, 1000, 1000), box(1000, 0, 2000, 1000)],
        crs=2263,
    ).to_crs(4326)


def _points_at(xs_ft):
    """Permits at x positions (feet, y=500), as lat/lon with their NTA assigned."""
    pts = gpd.GeoSeries([Point(x, 500) for x in xs_ft], crs=2263).to_crs(4326)
    df = pd.DataFrame({"lat": pts.y, "lon": pts.x})
    return assign_nta(df, _park_and_hood())


def test_reassign_park_edges_moves_point_near_park_edge():
    out = reassign_park_edges(_points_at([1010]), _park_and_hood())
    assert out.loc[0, "ntaname"] == "Upper East Side"
    assert out.loc[0, "nta2020"] == "MN0501"
    assert out.loc[0, "nta_reassigned"]


def test_reassign_park_edges_keeps_point_deep_in_park():
    out = reassign_park_edges(_points_at([1500]), _park_and_hood())
    assert out.loc[0, "ntaname"] == "Central Park"
    assert not out.loc[0, "nta_reassigned"]


def test_reassign_park_edges_leaves_other_points_alone():
    out = reassign_park_edges(_points_at([500]), _park_and_hood())
    assert out.loc[0, "ntaname"] == "Upper East Side"
    assert not out.loc[0, "nta_reassigned"]
