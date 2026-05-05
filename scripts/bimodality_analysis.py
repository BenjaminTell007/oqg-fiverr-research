"""Per-month bimodality coefficient and Hartigan dip statistic by category.

Outputs:
- data/output/bimodality_timeseries.png  (BC + dip on dual axis, all 4 categories)
- stdout:  summary table of first month BC > 0.555 vs. primary shock date
"""

import json
from pathlib import Path

import diptest
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew

PANEL = "data/output/full_panel.csv"
EVENTS = "data/ai_events.json"
OUT_PNG = "data/output/bimodality_timeseries.png"

BC_THRESHOLD = 0.555
MIN_N = 5

CATEGORY_SHOCKS = {
    "graphics-design/creative-logo-design":  ["2022-07-12", "2022-08-22", "2023-03-15"],
    "graphics-design/social-media-design":   ["2022-07-12", "2022-08-22", "2023-03-15"],
    "content-writing/creative-writing":      ["2022-11-30", "2023-02-01", "2023-03-14", "2024-05-13"],
    "data/data-entry":                       [],
}

CATEGORY_COLORS = {
    "graphics-design/creative-logo-design":  "#1f77b4",
    "graphics-design/social-media-design":   "#2ca02c",
    "content-writing/creative-writing":      "#d62728",
    "data/data-entry":                       "#7f7f7f",
}


def bimodality_coefficient(x: np.ndarray) -> float:
    """Sarle's BC.  BC = (g^2 + 1) / (k + 3(n-1)^2/((n-2)(n-3)))."""
    n = len(x)
    if n < 4:
        return np.nan
    g = skew(x, bias=False)
    k = kurtosis(x, bias=False, fisher=True)  # excess kurtosis
    correction = 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    return (g ** 2 + 1) / (k + correction)


def per_month_stats(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()
    rows = []
    for (cat, m), g in df.groupby(["category", "month"]):
        prices = g["price"].dropna().to_numpy(dtype=float)
        n = len(prices)
        if n < MIN_N:
            rows.append({"category": cat, "month": m, "n": n,
                         "BC": np.nan, "dip": np.nan, "dip_p": np.nan})
            continue
        bc = bimodality_coefficient(prices)
        dip, p = diptest.diptest(prices)
        rows.append({"category": cat, "month": m, "n": n,
                     "BC": bc, "dip": dip, "dip_p": p})
    return pd.DataFrame(rows).sort_values(["category", "month"]).reset_index(drop=True)


def plot_timeseries(stats: pd.DataFrame, events: dict, out_path: str) -> None:
    fig, (ax_bc, ax_dip) = plt.subplots(2, 1, figsize=(13, 9), sharex=True)

    for cat, sub in stats.groupby("category"):
        color = CATEGORY_COLORS.get(cat, "black")
        label = cat.split("/", 1)[-1]
        ax_bc.plot(sub["month"], sub["BC"], "-o", ms=3, color=color, label=label, alpha=0.85)
        ax_dip.plot(sub["month"], sub["dip"], "-o", ms=3, color=color, label=label, alpha=0.85)

    ax_bc.axhline(BC_THRESHOLD, color="black", linestyle=":", linewidth=1,
                  label=f"BC = {BC_THRESHOLD} (bimodality threshold)")

    seen_event_labels = set()
    for vector_key, vector in events.items():
        for ev in vector["events"]:
            d = pd.to_datetime(ev["date"])
            label = ev["name"] if ev["name"] not in seen_event_labels else None
            seen_event_labels.add(ev["name"])
            for ax in (ax_bc, ax_dip):
                ax.axvline(d, color="grey", linestyle="--", linewidth=0.7, alpha=0.5)

    ax_bc.set_ylabel("Bimodality coefficient (Sarle)")
    ax_bc.set_title("Per-month bimodality by category — Fiverr panel 2021–2024")
    ax_bc.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax_bc.grid(True, alpha=0.3)

    ax_dip.set_ylabel("Hartigan dip statistic")
    ax_dip.set_xlabel("Month")
    ax_dip.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax_dip.grid(True, alpha=0.3)

    fig.text(0.99, 0.01, "Dashed lines: AI event dates (ai_events.json)",
             ha="right", va="bottom", fontsize=8, color="grey")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved {out_path}")


def first_crossing_summary(stats: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cat, shocks in CATEGORY_SHOCKS.items():
        sub = stats[(stats["category"] == cat) & (stats["BC"].notna())]
        crossed = sub[sub["BC"] > BC_THRESHOLD]
        first = crossed["month"].min() if len(crossed) else pd.NaT
        primary = pd.to_datetime(shocks[0]) if shocks else pd.NaT
        if pd.notna(first) and pd.notna(primary):
            after = first >= primary.to_period("M").to_timestamp()
            after_str = "yes" if after else "no"
        elif not shocks:
            after_str = "n/a (control)"
        else:
            after_str = "BC never exceeded threshold"
        rows.append({
            "category": cat,
            "primary_shock": primary.date() if pd.notna(primary) else None,
            "first_BC>0.555": first.date() if pd.notna(first) else None,
            "after_primary_shock?": after_str,
            "n_months_BC>thr": int(len(crossed)),
        })
    return pd.DataFrame(rows)


def main():
    df = pd.read_csv(PANEL)
    with open(EVENTS) as f:
        events = json.load(f)

    stats = per_month_stats(df)
    Path("data/output").mkdir(parents=True, exist_ok=True)
    stats.to_csv("data/output/bimodality_per_month.csv", index=False)

    plot_timeseries(stats, events, OUT_PNG)

    summary = first_crossing_summary(stats)
    print("\n" + "=" * 78)
    print("  First month BC exceeded 0.555 vs. primary shock date")
    print("=" * 78)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
