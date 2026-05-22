"""Dose-response figure.

Each category is one dot. X-axis = AI exposure level. Y-axis = median price
change after AI tools launched (post-July 2022 median minus pre-July 2022 median).
A fitted trend line shows that higher exposure predicts a larger price drop.

Output: data/output/figures/final/dose_response.png
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy import stats

PANEL_PATH = Path("data/output/full_panel.csv")
OUT_PATH   = Path("data/output/figures/final/dose_response.png")
DPI        = 300
CUTOFF     = pd.Timestamp("2022-07-01")

mpl.rcParams.update({
    "font.family":       "sans-serif",
    "font.sans-serif":   ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size":         10,
    "axes.titlesize":    13,
    "axes.labelsize":    11,
    "xtick.labelsize":   10,
    "ytick.labelsize":   10,
    "figure.dpi":        DPI,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.25,
    "grid.linewidth":    0.6,
})

CATS = [
    dict(cat="graphics-design/creative-logo-design", label="Logo design",
         score=0.90, color="#1f77b4", is_treatment=True),
    dict(cat="graphics-design/social-media-design",  label="Social media design",
         score=0.85, color="#2ca02c", is_treatment=True),
    dict(cat="content-writing/creative-writing",     label="Creative writing",
         score=0.80, color="#d62728", is_treatment=True),
    dict(cat="transcription-control-medium",         label="Transcription",
         score=0.40, color="#ff7f0e", is_treatment=False),
    dict(cat="data/data-entry",                      label="Data entry",
         score=0.10, color="#888888", is_treatment=False),
]

# Label offsets (x, y) to avoid overlapping dot labels
LABEL_OFFSETS = {
    "Logo design":         ( 0.01,  1.5),
    "Social media design": ( 0.01, -4.0),
    "Creative writing":    ( 0.01,  1.5),
    "Transcription":       ( 0.02,  1.5),
    "Data entry":          ( 0.02,  1.5),
}


def compute_price_changes(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy()
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()
    df = df.dropna(subset=["price"])

    rows = []
    for c in CATS:
        sub = df[df["category"] == c["cat"]]
        pre_med  = sub[sub["month"] < CUTOFF]["price"].median()
        post_med = sub[sub["month"] >= CUTOFF]["price"].median()
        rows.append({**c, "pre_median": pre_med, "post_median": post_med,
                     "change": post_med - pre_med})
    return pd.DataFrame(rows)


def make_figure(data: pd.DataFrame, out_path: Path) -> None:
    scores  = data["score"].values.astype(float)
    changes = data["change"].values.astype(float)

    # Fit trend line
    slope, intercept, r, p, _ = stats.linregress(scores, changes)
    x_line = np.linspace(0.0, 1.0, 200)
    y_line = slope * x_line + intercept

    fig, ax = plt.subplots(figsize=(9, 6))

    # Trend line behind dots
    ax.plot(x_line, y_line, color="#333333", linewidth=1.6,
            linestyle="--", zorder=2, label=f"Trend  (slope = ${slope:.0f} per unit, p = {p:.2f})")

    # Dots
    for _, row in data.iterrows():
        ax.scatter(row["score"], row["change"],
                   color=row["color"], s=130, zorder=4,
                   edgecolors="white", linewidths=1.2)
        dx, dy = LABEL_OFFSETS.get(row["label"], (0.01, 1.5))
        ax.text(row["score"] + dx, row["change"] + dy,
                row["label"], fontsize=9.5, color=row["color"],
                va="bottom", ha="left")

    # Zero reference
    ax.axhline(0, color="black", linewidth=0.9, zorder=1)

    # Axes
    ax.set_xlabel("AI exposure level  (low                                    high)",
                  fontsize=11)
    ax.set_ylabel("Price change after AI tools launched (USD)", fontsize=11)
    ax.set_xlim(-0.05, 1.05)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.1f}"))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:+.0f}"))

    ax.legend(loc="upper left", framealpha=0.9, fontsize=9,
              handlelength=1.6, borderpad=0.5)

    ax.set_title(
        "Higher AI exposure predicts larger price drops\n"
        "Each dot is one Fiverr category  (comparing average prices before and after AI tools launched)",
        fontsize=12, pad=10,
    )

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


def main():
    panel = pd.read_csv(PANEL_PATH)
    data  = compute_price_changes(panel)
    make_figure(data, OUT_PATH)


if __name__ == "__main__":
    main()
