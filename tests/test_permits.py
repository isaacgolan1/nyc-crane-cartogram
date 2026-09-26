import pandas as pd

from src.permits import application_gap_days, evaluate_tracking_dates, parse_tracking_date


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
