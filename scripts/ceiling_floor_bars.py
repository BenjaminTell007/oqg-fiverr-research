"""Before/after ceiling and floor bar chart.

Shows GMM-estimated ceiling and floor price change (post minus pre) per category.
Ordered high to low AI exposure. Reference line at data entry ceiling drop
to show the platform-wide baseline.

Output: data/output/figures/final/ceiling_floor_bars.png
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

GMM_PATH = Path("data/output/gmm_floor_ceiling.csv")
OUT_PATH  = Path("data/output/figures/final/ceiling_floor_bars.png")
DPI       = 300

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

# Order high → low exposure, labels clean
CATS = [
    ("graphics-design/creative-logo-design", "Logo design\n(high exposure)"),
    ("graphics-design/social-media-design",  "Social media design\n(high exposure)"),
    ("content-writing/creative-writing",      "Creative writing\n(high exposure)"),
    ("transcription-control-medium",          "Transcription\n(control)"),
    ("data/data-entry",                       "Data entry\n(control)"),
]

CEILING_COLOR = "#c0392b"   # dark red — ceiling
FLOOR_COLOR   = "#5dade2"   # blue — floor
CTRL_ALPHA    = 0.55        # fade control category bars slightly


def make_figure(gmm: pd.DataFrame, out_path: Path) -> None:
    rows = []
    for cat, label in CATS:
        row = gmm[gmm["category"] == cat].iloc[0]
        ceiling_delta = row["post_ceiling_mean"] - row["pre_ceiling_mean"]
        floor_delta   = row["post_floor_mean"]   - row["pre_floor_mean"]
        rows.append({
            "label":         label,
            "ceiling_delta": ceiling_delta,
            "floor_delta":   floor_delta,
            "is_control":    "control" in label,
        })
    df = pd.DataFrame(rows)

    n      = len(df)
    x      = np.arange(n)
    width  = 0.35

    fig, ax = plt.subplots(figsize=(11, 5.5))

    for i, row in df.iterrows():
        alpha = CTRL_ALPHA if row["is_control"] else 1.0
        # Ceiling bar
        ax.bar(x[i] - width / 2, row["ceiling_delta"], width,
               color=CEILING_COLOR, alpha=alpha, zorder=3,
               label="Ceiling change" if i == 0 else "_nolegend_")
        # Floor bar
        ax.bar(x[i] + width / 2, row["floor_delta"], width,
               color=FLOOR_COLOR, alpha=alpha, zorder=3,
               label="Floor change" if i == 0 else "_nolegend_")

        # Annotate dollar amounts on bars
        for val, offset in [(row["ceiling_delta"], -width / 2),
                            (row["floor_delta"],   +width / 2)]:
            sign = -1 if val < 0 else 1
            pad  = sign * 1.2
            ax.text(x[i] + offset, val + pad, f"${val:+.0f}",
                    ha="center", va="bottom" if val >= 0 else "top",
                    fontsize=8.5, fontweight="bold",
                    color=CEILING_COLOR if offset < 0 else FLOOR_COLOR)


    # Divider between treatment and control
    ax.axvline(2.5, color="#bbbbbb", linewidth=1.2, linestyle="--", zorder=1)

    # Zero line
    ax.axhline(0, color="black", linewidth=0.9, zorder=2)

    # Axes
    ax.set_xticks(x)
    ax.set_xticklabels(df["label"], fontsize=9.5)
    ax.set_ylabel("Price change before vs. after AI tools launched (USD)", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:+.0f}"))

    ax.legend(loc="lower right", framealpha=0.9, fontsize=9,
              handlelength=1.4, handletextpad=0.5,
              borderpad=0.5, labelspacing=0.3)

    ax.set_title(
        "Top-end prices collapsed in AI-exposed categories; bottom-end prices held steady\n"
        "Faded bars = control categories",
        fontsize=12, pad=10,
    )

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


def main():
    gmm = pd.read_csv(GMM_PATH)
    make_figure(gmm, OUT_PATH)


if __name__ == "__main__":
    main()
