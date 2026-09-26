"""Stage 5: four charts of the permit-friction results."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src import config

# One series per chart, so one hue. Validated against the surface with the
# dataviz skill's validate_palette.js (light mode, all checks pass).
SERIES = "#2a78d6"
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_MUTED = "#52514e"
GRID = "#e4e3df"
SCOPE = ", ".join(b.title() for b in config.BOROUGHS)
PERIOD = f"{config.START_DATE[:4]}–present"

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": TEXT_MUTED,
    "figure.constrained_layout.use": True,
    "xtick.color": TEXT_MUTED,
    "ytick.color": TEXT,
    "font.size": 9,
})


def style(ax, grid_axis: str) -> None:
    """Recessive chrome: no box, light grid behind the marks."""
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def title(fig, text: str) -> None:
    """Figure-level title, left-aligned, so long titles are never cut off by the axes."""
    fig.suptitle(text, x=0.01, ha="left", color=TEXT, fontsize=12, fontweight="bold")


def save(fig, name: str) -> None:
    config.OUTPUTS_DIR.mkdir(exist_ok=True)
    fig.savefig(config.OUTPUTS_DIR / name, dpi=150)
    plt.close(fig)
    print(f"  outputs/{name}")


def top_bottom_chart(table: pd.DataFrame, column: str, count_col: str, xlabel: str, heading: str,
                     name: str, n: int = 10) -> None:
    """Highest n and lowest n neighborhoods, highest at the top, with a labeled gap between."""
    ranked = table.dropna(subset=[column]).sort_values([column, count_col], ascending=False)
    top = ranked.head(n)
    bottom = ranked.tail(n)
    bottom = bottom[~bottom["nta2020"].isin(top["nta2020"])]

    labels = list(top["nta_name"]) + [""] + list(bottom["nta_name"])
    values = list(top[column]) + [0] + list(bottom[column])
    y = list(range(len(labels)))[::-1]

    fig, ax = plt.subplots(figsize=(8, 0.32 * len(labels) + 1.6))
    bars = ax.barh(y, values, height=0.62, color=SERIES)
    gap = y[len(top)]
    bars[len(top)].set_visible(False)
    ax.set_yticks(y, labels)
    ax.axhline(gap, color=GRID, linewidth=0.8, linestyle="--")

    for yi, v, label in zip(y, values, labels):
        if label:
            ax.text(v + max(values) * 0.01, yi, f"{v:g}", va="center", color=TEXT_MUTED, fontsize=8)
    ax.text(0, y[0] + 0.9, f"Highest {len(top)}", color=TEXT_MUTED, fontsize=8, fontweight="bold")
    ax.text(0, gap - 0.35, f"Lowest {len(bottom)}", color=TEXT_MUTED, fontsize=8, fontweight="bold", va="top")

    ax.set_xlabel(xlabel)
    title(fig, heading)
    ax.set_xlim(0, max(values) * 1.12)
    ax.set_ylim(min(y) - 0.7, y[0] + 1.6)
    style(ax, "x")
    save(fig, name)


def main() -> None:
    metrics = pd.read_csv(config.PROCESSED_DIR / "crane_permit_metrics.csv")
    table = pd.read_csv(config.PROCESSED_DIR / "permit_friction_by_nta.csv")
    codes = pd.read_csv(config.PROCESSED_DIR / "distinctive_code_frequency.csv")

    # 1. Lead-time distribution
    lead = metrics["lead_time_days"].dropna()
    median = lead.median()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(lead.clip(upper=30), bins=range(0, 32), color=SERIES, edgecolor=SURFACE, linewidth=1)
    top_y = ax.get_ylim()[1] * 1.12
    ax.set_ylim(0, top_y)
    ax.axvline(median + 0.5, color=TEXT, linestyle="--", linewidth=1)
    ax.text(median + 0.8, top_y * 0.96, f"median {median:.0f} days", color=TEXT, va="top",
            bbox={"facecolor": SURFACE, "edgecolor": "none", "pad": 2})
    ax.set_xlabel("Days from application to issue (30+ grouped at 30)")
    ax.set_ylabel("New crane permits")
    title(fig, f"Crane permit lead time, {SCOPE}, {PERIOD} (n={len(lead):,})")
    style(ax, "y")
    save(fig, "p2_lead_time_distribution.png")

    # 2 and 3. Top and bottom neighborhoods
    top_bottom_chart(table, "median_lead_time_days", "n_new_permits",
                     "Median days from application to issue (New permits)",
                     f"Crane permit lead time by neighborhood, {SCOPE}", "p2_lead_time_by_nta.png")
    top_bottom_chart(table, "median_distinctive_stips", "n_permits",
                     "Median distinctive stipulations per permit",
                     f"Crane permit stipulation burden by neighborhood, {SCOPE}", "p2_stipulations_by_nta.png")

    # 4. Most common distinctive codes
    top = codes.head(15).iloc[::-1]
    labels = [f"{c}  {str(t)[:60].strip()}…" for c, t in zip(top["stipulationid"], top["text"])]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(labels, top["share"] * 100, height=0.62, color=SERIES)
    for yi, v in enumerate(top["share"] * 100):
        ax.text(v + 0.8, yi, f"{v:.0f}%", va="center", color=TEXT_MUTED, fontsize=8)
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of crane permits carrying this code")
    title(fig, f"Most common non-boilerplate stipulations, {SCOPE}, {PERIOD}")
    ax.tick_params(axis="y", labelsize=8)
    style(ax, "x")
    save(fig, "p2_top_distinctive_codes.png")


if __name__ == "__main__":
    main()
