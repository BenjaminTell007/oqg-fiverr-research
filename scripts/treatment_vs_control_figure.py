"""Treatment vs. control price compression — 3-panel figure.

One panel per treatment category, each paired with data entry (control).
3-month rolling median. Absolute prices. Shaded gap post-shock.

Output: data/output/figures/final/treatment_vs_control.png
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

PANEL_PATH = Path("data/output/full_panel.csv")
OUT_PATH   = Path("data/output/figures/final/treatment_vs_control.png")
DPI        = 300

FONT_FAMILY = "DejaVu Sans"
FS_TITLE    = 13
FS_LABEL    = 11
FS_TICK     = 10
FS_LEGEND   = 9
FS_ANNOT    = 8

mpl.rcParams.update({
    "font.family":       "sans-serif",
    "font.sans-serif":   [FONT_FAMILY, "Arial", "Helvetica"],
    "font.size":         FS_TICK,
    "axes.titlesize":    FS_TITLE,
    "axes.labelsize":    FS_LABEL,
    "xtick.labelsize":   FS_TICK,
    "ytick.labelsize":   FS_TICK,
    "legend.fontsize":   FS_LEGEND,
    "figure.dpi":        DPI,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.25,
    "grid.linewidth":    0.6,
})

CONTROL       = "data/data-entry"
CONTROL_COLOR = "#888888"
CONTROL_LABEL = "Data entry (control)"

TREATMENTS = [
    dict(
        cat          = "graphics-design/creative-logo-design",
        label        = "Creative logo design",
        subtitle     = "High AI exposure",
        color        = "#1f77b4",
        shock        = "2022-07-12",
        shock_label  = "Midjourney open beta",
    ),
    dict(
        cat          = "graphics-design/social-media-design",
        label        = "Social media design",
        subtitle     = "High AI exposure",
        color        = "#2ca02c",
        shock        = "2022-07-12",
        shock_label  = "Midjourney open beta",
    ),
    dict(
        cat          = "content-writing/creative-writing",
        label        = "Creative writing",
        subtitle     = "High AI exposure",
        color        = "#d62728",
        shock        = "2022-11-30",
        shock_label  = "ChatGPT launch",
    ),
]


def load_monthly(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy()
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()
    df = df.dropna(subset=["price"])
    # trim top 5% within each category-month to remove snapshot outliers
    def trimmed_median(g):
        cap = g["price"].quantile(0.95)
        return g.loc[g["price"] <= cap, "price"].median()
    return (
        df.groupby(["category", "month"])
        .apply(trimmed_median, include_groups=False)
        .reset_index()
        .rename(columns={0: "price_median"})
    )


def smooth(series: pd.Series, window: int = 3) -> pd.Series:
    return series.rolling(window=window, center=True, min_periods=2).mean()


def dollar_fmt(x, _):
    return f"${int(x)}"


ALL_CATS = [
    dict(cat="graphics-design/creative-logo-design", label="Logo design",
         color="#1f77b4", linestyle="-",  linewidth=2.2),
    dict(cat="graphics-design/social-media-design",  label="Social media design",
         color="#2ca02c", linestyle="-",  linewidth=2.2),
    dict(cat="content-writing/creative-writing",     label="Creative writing",
         color="#d62728", linestyle="-",  linewidth=2.2),
    dict(cat="transcription-control-medium",         label="Transcription (control)",
         color="#ff7f0e", linestyle="--", linewidth=1.6),
    dict(cat=CONTROL,                                label="Data entry (control)",
         color=CONTROL_COLOR, linestyle="--", linewidth=1.6),
]

# Key shock dates to annotate on the combined chart
COMBINED_SHOCKS = [
    ("2022-07-12", "Midjourney"),
    ("2022-11-30", "ChatGPT"),
    ("2023-03-15", "MJ V5 / GPT-4"),
]


def make_figure(monthly: pd.DataFrame, out_path: Path) -> None:
    control_raw = (
        monthly[monthly["category"] == CONTROL]
        .sort_values("month")
        .set_index("month")["price_median"]
    )
    control_smooth = smooth(control_raw)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=False)

    for ax, t in zip(axes, TREATMENTS):
        treat_raw = (
            monthly[monthly["category"] == t["cat"]]
            .sort_values("month")
            .set_index("month")["price_median"]
        )
        treat_smooth = smooth(treat_raw)
        shock_date   = pd.Timestamp(t["shock"])

        ax.axvspan(pd.Timestamp("2021-01-01"), shock_date,
                   color="#f5f5f5", zorder=0, label="_nolegend_")

        ax.plot(control_smooth.index, control_smooth.values,
                color=CONTROL_COLOR, linewidth=1.8, linestyle="--",
                label=CONTROL_LABEL, zorder=3)

        ax.plot(treat_smooth.index, treat_smooth.values,
                color=t["color"], linewidth=2.4, linestyle="-",
                label=t["label"], zorder=4)

        common   = treat_smooth.index.intersection(control_smooth.index)
        post_idx = common[common >= shock_date]
        if len(post_idx):
            ax.fill_between(post_idx,
                            treat_smooth.reindex(post_idx),
                            control_smooth.reindex(post_idx),
                            color=t["color"], alpha=0.13, zorder=2)

        ax.axvline(shock_date, color="#333333", linestyle="--",
                   linewidth=1.3, alpha=0.85, zorder=5)
        xform = ax.get_xaxis_transform()
        ax.text(shock_date, 0.97, f"  {t['shock_label']}",
                transform=xform, rotation=90, fontsize=FS_ANNOT,
                va="top", ha="left", color="#333333", clip_on=True)

        ax.yaxis.set_major_formatter(mticker.FuncFormatter(dollar_fmt))
        ax.set_title(f"{t['label']}\n{t['subtitle']}", fontsize=FS_TITLE - 1, pad=8)
        ax.set_xlabel("Month", fontsize=FS_LABEL)
        if ax is axes[0]:
            ax.set_ylabel("Median gig price (USD)", fontsize=FS_LABEL)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
        ax.set_xlim(pd.Timestamp("2021-01-01"), pd.Timestamp("2025-01-01"))

        handles, labels = ax.get_legend_handles_labels()
        filtered = [(h, l) for h, l in zip(handles, labels)
                    if l != "_nolegend_"]
        ax.legend(*zip(*filtered), loc="upper right",
                  framealpha=0.92, fontsize=FS_LEGEND - 1,
                  handlelength=1.4, handletextpad=0.5,
                  borderpad=0.4, labelspacing=0.3)

    fig.suptitle(
        "Price compression: AI-exposed categories vs. data entry control\n"
        "3-month rolling median  ·  Shaded region = divergence after AI shock",
        fontsize=FS_TITLE, y=1.03,
    )
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


def make_combined_figure(monthly: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.5))

    for c in ALL_CATS:
        raw = (
            monthly[monthly["category"] == c["cat"]]
            .sort_values("month")
            .set_index("month")["price_median"]
        )
        s = smooth(raw)
        ax.plot(s.index, s.values,
                color=c["color"], linestyle=c["linestyle"],
                linewidth=c["linewidth"], label=c["label"], zorder=4)

    # Shock annotations
    xform = ax.get_xaxis_transform()
    tier = 0
    prev_d = None
    for d_str, label in COMBINED_SHOCKS:
        d = pd.Timestamp(d_str)
        ax.axvline(d, color="#555555", linestyle="--", linewidth=1.0,
                   alpha=0.7, zorder=2)
        if prev_d and (d - prev_d).days < 120:
            tier += 1
        else:
            tier = 0
        prev_d = d
        ax.text(d, 0.97 - tier * 0.13, f"  {label}",
                transform=xform, rotation=90, fontsize=FS_ANNOT,
                va="top", ha="left", color="#444444", clip_on=True)

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(dollar_fmt))
    ax.set_ylabel("Median gig price (USD)", fontsize=FS_LABEL)
    ax.set_xlabel("Month", fontsize=FS_LABEL)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.set_xlim(pd.Timestamp("2021-01-01"), pd.Timestamp("2025-01-01"))

    ax.legend(loc="upper right", framealpha=0.92,
              fontsize=FS_LEGEND, handlelength=1.6,
              handletextpad=0.5, borderpad=0.5, labelspacing=0.35)

    fig.suptitle(
        "All five categories — median gig price, Fiverr 2021–2024\n"
        "Solid = AI-exposed  ·  Dashed = control  ·  3-month rolling median",
        fontsize=FS_TITLE, y=1.02,
    )
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


COMBINED_OUT = Path("data/output/figures/final/all_categories.png")


def main():
    panel   = pd.read_csv(PANEL_PATH)
    monthly = load_monthly(panel)
    make_figure(monthly, OUT_PATH)
    make_combined_figure(monthly, COMBINED_OUT)


if __name__ == "__main__":
    main()
