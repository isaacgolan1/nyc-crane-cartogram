"""Stage 2: check whether applicationtrackingid's first 8 digits are an application date."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src import config
from src.permits import application_gap_days, evaluate_tracking_dates


def main() -> None:
    permits = pd.read_csv(config.latest_raw("dot_crane_permits"), dtype=str)
    result = evaluate_tracking_dates(permits)
    gap = application_gap_days(permits)

    print(f"Permits checked:                 {result['rows']:,}")
    print(f"IDs that parse as a real date:   {result['parsed_share']:.2%}   (need 100%)")
    print(f"Date on or before issue date:    {result['not_after_issue_share']:.2%}   (need >= 99%)")
    print(f"Median gap (days):               {result['median_gap_days']:.1f}   (need 1-60)")
    print("\nGap percentiles (days):")
    print(gap.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).round(1).to_string())
    print("\nMedian gap by application type:")
    print(gap.groupby(permits["applicationtypeshortdesc"]).median().to_string())
    print("\nSample of permits with negative gaps:")
    cols = ["permitnumber", "applicationtrackingid", "applicationtypeshortdesc", "permitissuedate"]
    print(permits.loc[gap < 0, cols].head(10).to_string(index=False))

    print("\nRESULT:", "PASS" if result["passed"] else "FAIL")
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
