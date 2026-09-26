"""Stipulation burden: which codes are boilerplate, and how many distinctive codes a permit has."""
import pandas as pd


def code_shares(stips: pd.DataFrame, permit_numbers: pd.Series) -> pd.Series:
    """Share of the given permits that carry each stipulation code, highest first."""
    permits = set(permit_numbers)
    relevant = stips[stips["permitnumber"].isin(permits)].drop_duplicates(["permitnumber", "stipulationid"])
    counts = relevant.groupby("stipulationid")["permitnumber"].nunique()
    return (counts / len(permits)).sort_values(ascending=False)


def find_boilerplate_codes(shares: pd.Series, cutoff: float) -> set[str]:
    """Codes on more than `cutoff` of permits. They add the same amount everywhere."""
    return set(shares[shares > cutoff].index)


def distinctive_stip_counts(stips: pd.DataFrame, permit_numbers: pd.Series, boilerplate: set[str]) -> pd.Series:
    """Number of non-boilerplate codes per permit, in the order of `permit_numbers`."""
    relevant = stips[~stips["stipulationid"].isin(boilerplate)].drop_duplicates(["permitnumber", "stipulationid"])
    counts = relevant.groupby("permitnumber")["stipulationid"].nunique()
    return counts.reindex(permit_numbers.tolist(), fill_value=0).reset_index(drop=True)


def has_custom_text(text: pd.Series) -> pd.Series:
    """True where DOT wrote site-specific conditions in `specificstipulations`."""
    return text.fillna("").str.strip() != ""
