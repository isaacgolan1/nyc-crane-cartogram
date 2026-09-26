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
