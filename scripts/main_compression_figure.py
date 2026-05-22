"""Main price compression figure — two-panel hero figure.

Panel A: Monthly median gig prices (USD, log scale) per category.
Panel B: Price index normalized to each category's 2021 average = 100.

Output: data/output/figures/final/main_compression.png
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

PANEL_PATH = Path("data/output/full_panel.csv")
OUT_PATH   = Path("data/output/figures/final/main_compression.png")
DPI        = 300

# ── style (copied from publication_figures.py) ────────────────────────────────
FONT_FAMILY = "DejaVu Sans"
FS_TITLE   = 13
FS_LABEL   = 11
FS_TICK    = 10
FS_LEGEND  = 9
FS_ANNOT   = 8

mpl.rcParams.update({
    "font.family":        "sans-serif",
    "font.sans-serif":    [FONT_FAMILY, "Arial", "Helvetica"],
    "font.size":          FS_TICK,
    "axes.titlesize":     FS_TITLE,
    "axes.labelsize":     FS_LABEL,
    "xtick.labelsize":    FS_TICK,
    "ytick.labelsize":    FS_TICK,
    "legend.fontsize":    FS_LEGEND,
    "figure.dpi":         DPI,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          True,
    "grid.alpha":         0.3,
    "grid.linewidth":     0.6,
})

CATEGORY_COLORS = {
    "graphics-design/creative-logo-design": "#1f77b4",
    "graphics-design/social-media-design":  "#2ca02c",
    "content-writing/creative-writing":     "#d62728",
    "transcription-control-medium":         "#ff7f0e",
    "data/data-entry":                      "#7f7f7f",
}

CATEGORY_DISPLAY = {
    "graphics-design/creative-logo-design": "Creative logo design (S=0.90)",
    "graphics-design/social-media-design":  "Social media design (S=0.85)",
    "content-writing/creative-writing":     "Creative writing (S=0.80)",
    "transcription-control-medium":         "Transcription (S=0.40, ctrl)",
    "data/data-entry":                      "Data entry (S=0.10, ctrl)",
}

TREATMENT_CATS = {
    "graphics-design/creative-logo-design",
    "graphics-design/social-media-design",
    "content-writing/creative-writing",
}

# All unique shock dates across all categories
ALL_SHOCKS = sorted({
    "2022-07-12", "2022-08-22", "2022-09-21",
    "2022-11-30", "2023-02-01", "2023-03-14", "2023-03-15",
    "2024-05-13",
})

EVENT_SHORT = {
    "2022-07-12": "MJ beta",
    "2022-08-22": "SD release",
    "2022-09-21": "Whisper",
    "2022-11-30": "ChatGPT",
    "2023-02-01": "GPT+ launch",
    "2023-03-14": "GPT-4",
    "2023-03-15": "MJ V5",
    "2024-05-13": "GPT-4o",
}

CATS_ORDER = [
    "graphics-design/creative-logo-design",
    "graphics-design/social-media-design",
    "content-writing/creative-writing",
    "transcription-control-medium",
    "data/data-entry",
]


def draw_shock_vlines(ax, shock_dates, color="#555555", lw=0.9, alpha=0.75,
                      label_top=True, label_color="#333333", min_gap_days=45):
    xform = ax.get_xaxis_transform()
    last_d = None
    tier = 0
    for d_str in shock_dates:
        d = pd.Timestamp(d_str)
        ax.axvline(d, color=color, linestyle="--", linewidth=lw, alpha=alpha, zorder=1)
        if not label_top:
            continue
        if last_d is not None and (d - last_d).days < min_gap_days:
            tier += 1
        else:
            tier = 0
        last_d = d
        y_frac = 0.97 - tier * 0.13
        label = EVENT_SHORT.get(d_str, d_str[:7])
        ax.text(d, y_frac, f" {label}", rotation=90, fontsize=FS_ANNOT - 1,
                va="top", ha="left", color=label_color,
                transform=xform, clip_on=True, zorder=4)


def dollar_formatter(x, _):
    if x >= 1000:
        return f"${x/1000:.0f}k"
    if x == int(x):
        return f"${int(x)}"
    return f"${x:.0f}"


def log_dollar_ticks(ax, axis="y"):
    ticks = [5, 10, 25, 50, 100, 200]
    getattr(ax, f"set_{axis}ticks")(ticks)
    getattr(ax, f"{axis}axis").set_major_formatter(
        mticker.FuncFormatter(dollar_formatter))
    getattr(ax, f"{axis}axis").set_minor_formatter(mticker.NullFormatter())


def load_monthly(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy()
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()
    agg = (
        df.dropna(subset=["price"])
        .groupby(["category", "month"])["price"]
        .median()
        .reset_index()
        .rename(columns={"price": "price_median"})
    )
    return agg


def compute_price_index(monthly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cat in CATS_ORDER:
        sub = monthly[monthly["category"] == cat].copy()
        if cat == "graphics-design/creative-logo-design":
            # starts May 2021; use May–Dec 2021 as baseline
            baseline_months = sub[
                (sub["month"] >= "2021-05-01") & (sub["month"] < "2022-01-01")
            ]["price_median"]
        else:
            baseline_months = sub[sub["month"] < "2022-01-01"]["price_median"]

        if len(baseline_months) == 0:
            continue
        baseline = baseline_months.mean()
        sub = sub.copy()
        sub["price_index"] = sub["price_median"] / baseline * 100
        rows.append(sub)

    return pd.concat(rows, ignore_index=True)


def make_figure(monthly: pd.DataFrame, indexed: pd.DataFrame, out_path: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    for cat in CATS_ORDER:
        sub = monthly[monthly["category"] == cat].sort_values("month")
        color = CATEGORY_COLORS[cat]
        ls = "-" if cat in TREATMENT_CATS else "--"
        lw = 1.8 if cat in TREATMENT_CATS else 1.4
        label = CATEGORY_DISPLAY[cat]
        # Plot with NaN gaps preserved (dropna already applied in load_monthly;
        # months with no data simply won't appear, creating natural line breaks)
        ax1.plot(sub["month"], sub["price_median"],
                 color=color, linestyle=ls, linewidth=lw, label=label,
                 marker="o", markersize=2.5, alpha=0.9, zorder=3)

    ax1.set_yscale("log")
    log_dollar_ticks(ax1)
    ax1.set_ylabel("Median gig price (USD)")
    ax1.set_title("A  Absolute median prices", loc="left", fontsize=FS_TITLE - 1, pad=6)
    draw_shock_vlines(ax1, ALL_SHOCKS, label_top=True)
    ax1.legend(loc="lower left", framealpha=0.85, ncol=1, fontsize=FS_LEGEND)

    for cat in CATS_ORDER:
        sub = indexed[indexed["category"] == cat].sort_values("month")
        color = CATEGORY_COLORS[cat]
        ls = "-" if cat in TREATMENT_CATS else "--"
        lw = 1.8 if cat in TREATMENT_CATS else 1.4
        ax2.plot(sub["month"], sub["price_index"],
                 color=color, linestyle=ls, linewidth=lw,
                 marker="o", markersize=2.5, alpha=0.9, zorder=3)

    ax2.axhline(100, color="#aaaaaa", linewidth=1.0, linestyle="-", zorder=1)
    ax2.set_ylabel("Price index (2021 avg = 100)")
    ax2.set_title("B  Price index relative to 2021 average", loc="left",
                  fontsize=FS_TITLE - 1, pad=6)
    draw_shock_vlines(ax2, ALL_SHOCKS, label_top=False)

    # X-axis formatting (shared)
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=30, ha="right")
    ax2.set_xlim(pd.Timestamp("2021-01-01"), pd.Timestamp("2025-01-01"))

    fig.suptitle(
        "Monthly median gig prices by category — Fiverr, 2021–2024",
        fontsize=FS_TITLE + 1, y=1.01
    )

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


def main():
    panel = pd.read_csv(PANEL_PATH)
    monthly = load_monthly(panel)
    indexed = compute_price_index(monthly)
    make_figure(monthly, indexed, OUT_PATH)


if __name__ == "__main__":
    main()
