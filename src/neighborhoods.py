"""Roll permit-level metrics up to one row per neighborhood (NTA)."""
import numpy as np
import pandas as pd


def rollup_by_nta(permits: pd.DataFrame, ntas: pd.DataFrame, min_permits: int) -> pd.DataFrame:
    """Median metrics per NTA. Every NTA in `ntas` appears, even with zero permits.

    A metric is left blank when its sample is below `min_permits`.
    """
    g = permits.groupby("nta2020")
    stats = pd.DataFrame({
        "n_permits": g.size(),
        "n_new_permits": g["lead_time_days"].count(),
        "median_lead_time_days": g["lead_time_days"].median(),
        "median_distinctive_stips": g["distinctive_stip_count"].median().astype(float),
        "pct_custom_text": g["has_custom_text"].mean().astype(float) * 100,
    })

    table = (
        ntas[["nta2020", "ntaname", "boroname"]]
        .rename(columns={"ntaname": "nta_name", "boroname": "borough"})
        .merge(stats, left_on="nta2020", right_index=True, how="left")
    )
    table[["n_permits", "n_new_permits"]] = table[["n_permits", "n_new_permits"]].fillna(0).astype(int)
    table.loc[table["n_new_permits"] < min_permits, "median_lead_time_days"] = np.nan
    table.loc[table["n_permits"] < min_permits, "median_distinctive_stips"] = np.nan
    table["insufficient_data"] = (
        table["median_lead_time_days"].isna() | table["median_distinctive_stips"].isna()
    )
    return table.sort_values("nta2020").reset_index(drop=True)
