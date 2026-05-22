"""Data coverage heatmap — gigs per category per month.

Output: data/output/figures/final/coverage_heatmap.png
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

PANEL_PATH = Path("data/output/full_panel.csv")
OUT_PATH   = Path("data/output/figures/final/coverage_heatmap.png")
DPI        = 300

# ── style (matches publication_figures.py) ────────────────────────────────────
mpl.rcParams.update({
    "font.family":        "sans-serif",
    "font.sans-serif":    ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size":          10,
    "axes.titlesize":     13,
    "axes.labelsize":     11,
    "xtick.labelsize":    10,
    "ytick.labelsize":    10,
    "legend.fontsize":    9,
    "figure.dpi":         DPI,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          False,
    "grid.alpha":         0.3,
})

CATS_ORDER = [
    "graphics-design/creative-logo-design",
    "graphics-design/social-media-design",
    "content-writing/creative-writing",
    "transcription-control-medium",
    "data/data-entry",
]

Y_LABELS = [
    "Logo design\n(treatment)",
    "Social media design\n(treatment)",
    "Creative writing\n(treatment)",
    "Transcription\n(control)",
    "Data entry\n(control)",
]

# Primary shock date clusters to mark
SHOCK_LINES = ["2022-07-01", "2022-11-01", "2023-03-01"]
SHOCK_LABELS = ["Image-gen shocks\n(Jul–Aug '22)", "ChatGPT\n(Nov '22)", "GPT-4 / MJ V5\n(Mar '23)"]


def build_coverage_matrix(panel: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    panel = panel.copy()
    panel["year_month"] = pd.to_datetime(panel["date"]).dt.to_period("M").dt.to_timestamp()

    # count non-null price rows per (category, month)
    counts = (
        panel.dropna(subset=["price"])
        .groupby(["category", "year_month"])
        .size()
        .reset_index(name="n")
    )

    all_months = pd.date_range("2021-01-01", "2024-12-01", freq="MS")

    matrix = counts.pivot(index="category", columns="year_month", values="n")
    matrix = matrix.reindex(index=CATS_ORDER, columns=all_months, fill_value=0)
    matrix = matrix.fillna(0).astype(int)

    return matrix, list(all_months)


def plot_coverage(matrix: pd.DataFrame, all_months: list, out_path: Path) -> None:
    n_cats = len(CATS_ORDER)
    n_months = len(all_months)

    fig, ax = plt.subplots(figsize=(18, 4))

    # Draw heatmap using pcolormesh for proper date axis
    x_edges = np.arange(n_months + 1)
    y_edges = np.arange(n_cats + 1)
    vals = matrix.values.astype(float)
    vals_masked = np.ma.masked_where(vals == 0, vals)

    # Background for zeros: visible grey
    ax.pcolormesh(x_edges, y_edges, np.ones_like(vals),
                  cmap="Greys", vmin=0, vmax=2, shading="flat", alpha=0.35)
    # Colored cells for non-zero
    im = ax.pcolormesh(x_edges, y_edges, vals_masked,
                       cmap="YlOrRd", vmin=1, vmax=12, shading="flat")

    # Annotate all cells — non-zero with count, zero with "0"
    for i in range(n_cats):
        for j in range(n_months):
            v = matrix.iloc[i, j]
            if v > 0:
                ax.text(j + 0.5, i + 0.5, str(v), ha="center", va="center",
                        fontsize=6.5, color="black" if v < 8 else "white")
            else:
                ax.text(j + 0.5, i + 0.5, "0", ha="center", va="center",
                        fontsize=6.0, color="#999999")

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, pad=0.01, shrink=0.85)
    cbar.set_label("Gigs / month", fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    # X-axis: quarterly ticks
    quarterly_idx = [j for j, m in enumerate(all_months) if m.month in (1, 4, 7, 10)]
    quarterly_labels = [m.strftime("%b '%y") for j, m in enumerate(all_months) if m.month in (1, 4, 7, 10)]
    ax.set_xticks([j + 0.5 for j in quarterly_idx])
    ax.set_xticklabels(quarterly_labels, rotation=45, ha="right", fontsize=8)

    # Y-axis
    ax.set_yticks([i + 0.5 for i in range(n_cats)])
    ax.set_yticklabels(Y_LABELS, fontsize=9)
    ax.invert_yaxis()

    ax.set_xlim(0, n_months)
    ax.set_ylim(n_cats, 0)
    ax.set_title("Panel coverage: gig observations per category per month", pad=8)

    # Grid lines between rows
    for i in range(1, n_cats):
        ax.axhline(i, color="white", linewidth=1.0)

    # Grid lines between years
    for j, m in enumerate(all_months):
        if m.month == 1:
            ax.axvline(j, color="white", linewidth=0.8, alpha=0.5)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


def main():
    panel = pd.read_csv(PANEL_PATH)
    matrix, all_months = build_coverage_matrix(panel)
    plot_coverage(matrix, all_months, OUT_PATH)


if __name__ == "__main__":
    main()
