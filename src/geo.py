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
