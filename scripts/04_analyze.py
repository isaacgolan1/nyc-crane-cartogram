"""Stage 4: compute lead time and stipulation burden per permit, then per neighborhood."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import pandas as pd

from src import config
from src.neighborhoods import rollup_by_nta
from src.permits import lead_time_days, lead_time_exclusions
from src.stipulations import code_shares, distinctive_stip_counts, find_boilerplate_codes, has_custom_text


def main() -> None:
    permits = pd.read_csv(config.PROCESSED_DIR / "crane_permits_clean.csv", dtype=str)
    stips = pd.read_csv(config.latest_raw("dot_crane_stipulations"), dtype=str)
    nta = gpd.read_file(config.latest_raw("nta2020", ".geojson"))

    # Boilerplate from ALL citywide crane permits, before location flags, so adding
    # a borough later never changes which codes count.
    shares = code_shares(stips, permits["permitnumber"])
    boilerplate = find_boilerplate_codes(shares, config.BOILERPLATE_CUTOFF)
    shares.rename("share").to_frame().assign(boilerplate=lambda d: d.index.isin(boilerplate)).to_csv(
        config.PROCESSED_DIR / "stipulation_code_shares.csv"
    )
    print(f"{len(shares)} stipulation codes citywide; {len(boilerplate)} boilerplate (> {config.BOILERPLATE_CUTOFF:.0%}):")
    print("  " + ", ".join(sorted(boilerplate)))

    permits["distinctive_stip_count"] = distinctive_stip_counts(stips, permits["permitnumber"], boilerplate).values
    permits["has_custom_text"] = has_custom_text(permits["specificstipulations"])
    permits["lead_time_days"] = lead_time_days(permits)

    in_scope = permits[permits["boroughname"].isin(config.BOROUGHS) & (permits["location_flag"] == "ok")]
    print(f"\nPermits in {config.BOROUGHS} with a usable location: {len(in_scope):,}")
    print("Lead-time funnel (in scope):", lead_time_exclusions(in_scope))

    # Embargo codes depend on timing as well as place; report how much they contribute.
    scope_stips = stips[stips["permitnumber"].isin(in_scope["permitnumber"]) & ~stips["stipulationid"].isin(boilerplate)]
    scope_stips = scope_stips.drop_duplicates(["permitnumber", "stipulationid"])
    embargo_share = scope_stips["stipulationid"].str.startswith("SE").mean()
    print(f"Share of distinctive code uses that are embargo (SE...) codes: {embargo_share:.1%}")

    # Most common distinctive codes in scope, with their text, for chart 4
    scope_shares = code_shares(stips, in_scope["permitnumber"]).drop(list(boilerplate), errors="ignore")
    texts = stips.drop_duplicates("stipulationid").set_index("stipulationid")["stipulationfulltext"]
    scope_shares.rename("share").to_frame().join(texts.rename("text")).to_csv(
        config.PROCESSED_DIR / "distinctive_code_frequency.csv"
    )

    ntas = nta[nta["boroname"].str.upper().isin(config.BOROUGHS)]
    table = rollup_by_nta(in_scope, ntas, config.MIN_PERMITS)
    table.to_csv(config.PROCESSED_DIR / "permit_friction_by_nta.csv", index=False)

    metric_cols = ["permitnumber", "boroughname", "nta2020", "ntaname", "applicationtypeshortdesc",
                   "lead_time_days", "distinctive_stip_count", "has_custom_text"]
    in_scope[metric_cols].to_csv(config.PROCESSED_DIR / "crane_permit_metrics.csv", index=False)

    print(f"\n{len(table)} neighborhoods; {table['insufficient_data'].sum()} flagged insufficient_data")
    ranked = table.dropna(subset=["median_lead_time_days"]).sort_values("median_lead_time_days", ascending=False)
    print("\nHighest median lead time:")
    print(ranked.head(5)[["nta_name", "n_new_permits", "median_lead_time_days"]].to_string(index=False))
    ranked = table.dropna(subset=["median_distinctive_stips"]).sort_values("median_distinctive_stips", ascending=False)
    print("\nHighest median distinctive stipulations:")
    print(ranked.head(5)[["nta_name", "n_permits", "median_distinctive_stips"]].to_string(index=False))


if __name__ == "__main__":
    main()
