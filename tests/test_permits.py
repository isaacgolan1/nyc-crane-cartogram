import numpy as np
import pandas as pd

from src.permits import (
    application_gap_days, evaluate_tracking_dates, lead_time_days, lead_time_exclusions, parse_tracking_date,
)


def test_parse_tracking_date_reads_first_8_digits():
    assert parse_tracking_date("2026092200673116") == pd.Timestamp("2026-09-22")


def test_parse_tracking_date_bad_input_is_nat():
    assert pd.isna(parse_tracking_date("20261399XXXX"))   # month 13
    assert pd.isna(parse_tracking_date("ABC"))
    assert pd.isna(parse_tracking_date(None))
    assert pd.isna(parse_tracking_date(float("nan")))


def _permits(rows):
    return pd.DataFrame(rows, columns=["applicationtrackingid", "permitissuedate"])


def test_application_gap_days():
    permits = _permits([["2026092200673116", "2026-09-25T13:59:14.000"]])
    assert application_gap_days(permits).tolist() == [3.0]


def test_evaluate_passes_on_plausible_data():
    permits = _permits([
        ["2026092200000001", "2026-09-25T10:00:00.000"],
        ["2026091900000002", "2026-09-25T10:00:00.000"],
        ["2026092100000003", "2026-09-25T10:00:00.000"],
    ])
    result = evaluate_tracking_dates(permits)
    assert result["parsed_share"] == 1.0
    assert result["median_gap_days"] == 4.0
    assert result["passed"] is True


def test_evaluate_fails_when_ids_do_not_parse():
    permits = _permits([
        ["2026092200000001", "2026-09-25T10:00:00.000"],
        ["NOTADATE00000002", "2026-09-25T10:00:00.000"],
    ])
    assert evaluate_tracking_dates(permits)["passed"] is False


def test_evaluate_fails_when_application_after_issue():
    permits = _permits([
        ["2026093000000001", "2026-09-25T10:00:00.000"],
        ["2026092200000002", "2026-09-25T10:00:00.000"],
    ])
    assert evaluate_tracking_dates(permits)["passed"] is False


def test_evaluate_fails_when_median_gap_implausible():
    permits = _permits([["2025010100000001", "2026-01-01T10:00:00.000"]])
    assert evaluate_tracking_dates(permits)["passed"] is False


def _lead_permits():
    return pd.DataFrame(
        [
            ["2026092200000001", "2026-09-27T10:00:00.000", "New", np.nan],                      # used: 5 days
            ["2026092200000002", "2026-09-27T10:00:00.000", "Renew", np.nan],                    # not New
            ["2026092200000003", "2026-09-27T10:00:00.000", "New", "2026-09-23T00:00:00.000"],   # emergency
            ["2026093000000004", "2026-09-27T10:00:00.000", "New", np.nan],                      # negative
            ["2025010100000005", "2026-09-27T10:00:00.000", "New", np.nan],                      # > 365 days
            ["BADID", "2026-09-27T10:00:00.000", "New", np.nan],                                 # unparsed
        ],
        columns=["applicationtrackingid", "permitissuedate", "applicationtypeshortdesc", "emergencyissuedate"],
    )


def test_lead_time_days_only_keeps_plausible_new_permits():
    result = lead_time_days(_lead_permits())
    assert result.iloc[0] == 5.0
    assert result.iloc[1:].isna().all()


def test_lead_time_exclusions_counts_each_reason():
    assert lead_time_exclusions(_lead_permits()) == {
        "not_new": 1, "emergency": 1, "unparsed": 1, "implausible": 2, "used": 1,
    }
