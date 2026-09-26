"""Permit timing: application date from the tracking ID, and lead time."""
import pandas as pd

from src import config


def parse_tracking_date(tracking_id: object) -> pd.Timestamp:
    """Read the first 8 digits of applicationtrackingid as YYYYMMDD.

    Returns NaT when the value is missing or is not a real date.
    """
    if not isinstance(tracking_id, str) or len(tracking_id) < 8 or not tracking_id[:8].isdigit():
        return pd.NaT
    return pd.to_datetime(tracking_id[:8], format="%Y%m%d", errors="coerce")


def application_gap_days(permits: pd.DataFrame) -> pd.Series:
    """Days from the tracking-ID date to the permit issue date (NaN if unparsed)."""
    applied = pd.to_datetime(permits["applicationtrackingid"].map(parse_tracking_date))
    issued = pd.to_datetime(permits["permitissuedate"]).dt.normalize()
    return (issued - applied).dt.days.astype(float)


def evaluate_tracking_dates(permits: pd.DataFrame) -> dict:
    """Check whether the tracking-ID date behaves like an application date.

    Passes only if every ID parses, at least 99% of dates are on or before
    the issue date, and the median gap is between 1 and 60 days.
    """
    applied = pd.to_datetime(permits["applicationtrackingid"].map(parse_tracking_date))
    gap = application_gap_days(permits).dropna()
    parsed_share = float(applied.notna().mean())
    not_after_issue_share = float((gap >= 0).mean()) if len(gap) else 0.0
    median_gap_days = float(gap.median()) if len(gap) else float("nan")
    passed = bool(
        parsed_share == 1.0
        and not_after_issue_share >= 0.99
        and 1 <= median_gap_days <= 60
    )
    return {
        "rows": len(permits),
        "parsed_share": parsed_share,
        "not_after_issue_share": not_after_issue_share,
        "median_gap_days": median_gap_days,
        "passed": passed,
    }


def _lead_time_masks(permits: pd.DataFrame, max_days: int) -> dict[str, pd.Series]:
    gap = application_gap_days(permits)
    is_new = permits["applicationtypeshortdesc"] == "New"
    emergency = is_new & permits["emergencyissuedate"].notna()
    candidate = is_new & ~emergency
    unparsed = candidate & gap.isna()
    implausible = candidate & gap.notna() & ~gap.between(0, max_days)
    used = candidate & gap.between(0, max_days)
    return {
        "gap": gap, "not_new": ~is_new, "emergency": emergency,
        "unparsed": unparsed, "implausible": implausible, "used": used,
    }


def lead_time_days(permits: pd.DataFrame, max_days: int = config.MAX_LEAD_TIME_DAYS) -> pd.Series:
    """Days from application to issue, for New non-emergency permits with a plausible gap."""
    masks = _lead_time_masks(permits, max_days)
    return masks["gap"].where(masks["used"])


def lead_time_exclusions(permits: pd.DataFrame, max_days: int = config.MAX_LEAD_TIME_DAYS) -> dict[str, int]:
    """How many permits each lead-time rule removed, and how many were used."""
    masks = _lead_time_masks(permits, max_days)
    return {k: int(masks[k].sum()) for k in ("not_new", "emergency", "unparsed", "implausible", "used")}
