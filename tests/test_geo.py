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
