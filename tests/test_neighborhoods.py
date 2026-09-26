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
