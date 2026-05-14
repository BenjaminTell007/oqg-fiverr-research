"""Publication-ready figures — all four, consistent style.

Outputs (300 DPI) to data/output/figures/final/:
  gmm_fits.png                 — pre/post KDE densities with GMM modes
  floor_ceiling_trajectories.png — monthly p10/p90 per category
  bc_differential.png          — BC differential vs data-entry control
  its_coefficients.png         — ITS β₂/β₃ per shock, per outcome
"""

import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde
from sklearn.mixture import GaussianMixture

# ── paths ────────────────────────────────────────────────────────────────────
PANEL_PATH  = Path("data/output/full_panel.csv")
EVENTS_PATH = Path("data/ai_events.json")
QUARTERLY_PATH = Path("data/output/bimodality_quarterly.csv")
ITS_PATH    = Path("data/output/its_results.csv")
OUT_DIR     = Path("data/output/figures/final")

# ── shared style ─────────────────────────────────────────────────────────────
DPI        = 300
FONT_FAMILY = "DejaVu Sans"
FS_TITLE   = 13   # figure/panel title
FS_LABEL   = 11   # axis labels
FS_TICK    = 10   # tick labels
FS_LEGEND  = 9    # legend entries
FS_ANNOT   = 8    # small annotations / shock labels

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

# ── category metadata ─────────────────────────────────────────────────────────
CATEGORY_COLORS = {
    "graphics-design/creative-logo-design": "#1f77b4",
    "graphics-design/social-media-design":  "#2ca02c",
    "content-writing/creative-writing":     "#d62728",
    "transcription-control-medium":         "#ff7f0e",
    "data/data-entry":                      "#7f7f7f",
}

CATEGORY_DISPLAY = {
    "graphics-design/creative-logo-design": "Creative logo design",
    "graphics-design/social-media-design":  "Social media design",
    "content-writing/creative-writing":     "Creative writing",
    "transcription-control-medium":         "Transcription",
    "data/data-entry":                      "Data entry",
}

EXPOSURE_LABEL = {
    "graphics-design/creative-logo-design": "high",
    "graphics-design/social-media-design":  "high",
    "content-writing/creative-writing":     "high",
    "transcription-control-medium":         "medium",
    "data/data-entry":                      "low",
}

CATEGORY_SHOCKS = {
    "graphics-design/creative-logo-design": ["2022-07-12", "2022-08-22", "2023-03-15"],
    "graphics-design/social-media-design":  ["2022-07-12", "2022-08-22", "2023-03-15"],
    "content-writing/creative-writing":     ["2022-11-30", "2023-02-01", "2023-03-14", "2024-05-13"],
    "transcription-control-medium":         ["2022-09-21"],
    "data/data-entry":                      [],
}

EVENT_SHORT = {
    "2022-07-12": "MJ beta",
    "2022-08-22": "SD release",
    "2023-03-15": "MJ V5",
    "2022-11-30": "ChatGPT",
    "2023-02-01": "GPT+ launch",
    "2023-03-14": "GPT-4",
    "2024-05-13": "GPT-4o",
    "2022-09-21": "Whisper",
}

CATS_ORDER = [
    "graphics-design/creative-logo-design",
    "graphics-design/social-media-design",
    "content-writing/creative-writing",
    "transcription-control-medium",
    "data/data-entry",
]

LOW_CONTROL = "data/data-entry"
RNG = 42


# ── helpers ───────────────────────────────────────────────────────────────────

def draw_shock_vlines(ax, shock_dates: list[str], color: str = "#555555",
                      lw: float = 0.9, alpha: float = 0.75,
                      label_top: bool = True, label_color: str = "#333333",
                      min_gap_days: int = 45) -> None:
    """Draw labeled vertical lines for each shock date.

    Uses get_xaxis_transform() so x is in data coords and y is in axes-fraction
    coords — labels stay inside the axes regardless of the data scale.
    Shock labels within min_gap_days of a prior label are shifted down to
    prevent stacking.
    """
    xform = ax.get_xaxis_transform()   # x=data, y=axes fraction
    last_d: pd.Timestamp | None = None
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
        y_frac = 0.95 - tier * 0.13
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
    """Set log-scale ticks at natural price points and format as dollars."""
    ticks = [5, 10, 25, 50, 100, 200, 500]
    getattr(ax, f"set_{axis}ticks")(ticks)
    getattr(ax, f"{axis}axis").set_major_formatter(
        mticker.FuncFormatter(dollar_formatter))
    getattr(ax, f"{axis}axis").set_minor_formatter(mticker.NullFormatter())


def save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


# ── Figure 1: GMM fits ────────────────────────────────────────────────────────

def fit_gmm(prices: np.ndarray) -> dict | None:
    if len(prices) < 10:
        return None
    X = np.log(prices.reshape(-1, 1))
    gmm = GaussianMixture(n_components=2, random_state=RNG, n_init=5).fit(X)
    means_log = gmm.means_.flatten()
    weights = gmm.weights_
    means_price = np.exp(means_log)
    order = np.argsort(means_price)
    return {
        "floor_mean":    float(means_price[order[0]]),
        "floor_weight":  float(weights[order[0]]),
        "ceiling_mean":  float(means_price[order[1]]),
        "ceiling_weight": float(weights[order[1]]),
        "n": len(prices),
    }


def fig_gmm_fits(panel: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes_flat = axes.flatten()

    for ax, cat in zip(axes_flat, CATS_ORDER):
        sub = panel[panel["category"] == cat].copy()
        shocks = CATEGORY_SHOCKS[cat]
        cut = pd.to_datetime(shocks[0]) if shocks else pd.to_datetime("2022-07-12")
        sub["date"] = pd.to_datetime(sub["date"])
        pre  = sub[sub["date"] < cut]["price"].dropna().to_numpy(dtype=float)
        post = sub[sub["date"] >= cut]["price"].dropna().to_numpy(dtype=float)

        color = CATEGORY_COLORS[cat]
        x_grid = np.linspace(np.log(3), np.log(600), 500)
        x_price = np.exp(x_grid)

        if len(pre) >= 5:
            ax.plot(x_price, gaussian_kde(np.log(pre))(x_grid),
                    color=color, alpha=0.45, linewidth=1.8,
                    linestyle="--", label=f"Pre-shock  (n={len(pre)})")
        if len(post) >= 5:
            ax.plot(x_price, gaussian_kde(np.log(post))(x_grid),
                    color=color, alpha=0.95, linewidth=2.2,
                    label=f"Post-shock (n={len(post)})")

        ax.set_xscale("log")
        log_dollar_ticks(ax, "x")
        ax.set_xlabel("Price (USD)")
        ax.set_ylabel("Density (log-price KDE)")
        exposure = EXPOSURE_LABEL[cat]
        ax.set_title(f"{CATEGORY_DISPLAY[cat]}  [{exposure} exposure]\n"
                     f"Shock cut: {cut.date()}", fontsize=FS_TITLE - 1)
        ax.legend(loc="upper right", framealpha=0.9)
        ax.autoscale(axis="y")

        # GMM modes — annotate after autoscale so y-fraction is meaningful
        g = fit_gmm(post) if len(post) >= 10 else None
        if g:
            xform = ax.get_xaxis_transform()   # x=data, y=axes fraction
            for val, wt_key, y_frac in [
                (g["floor_mean"],   "floor_weight",   0.92),
                (g["ceiling_mean"], "ceiling_weight", 0.78),
            ]:
                ax.axvline(val, color="black", linestyle=":", linewidth=0.9, alpha=0.8)
                ax.text(val * 1.07, y_frac, f"${val:.0f}\nw={g[wt_key]:.2f}",
                        fontsize=FS_ANNOT, va="top", color="#333333",
                        transform=xform, clip_on=True)

    axes_flat[-1].set_visible(False)

    fig.suptitle("Pre- vs. post-shock price distributions and GMM (k=2) modes",
                 fontsize=FS_TITLE + 1, y=1.01)
    fig.tight_layout()
    save(fig, out_path)


# ── Figure 2: Floor / ceiling trajectories ────────────────────────────────────

def fig_floor_ceiling(panel: pd.DataFrame, out_path: Path) -> None:
    panel = panel.copy()
    panel["month"] = pd.to_datetime(panel["date"]).dt.to_period("M").dt.to_timestamp()

    traj_rows = []
    for (cat, m), g in panel.groupby(["category", "month"]):
        prices = g["price"].dropna().to_numpy(dtype=float)
        n = len(prices)
        traj_rows.append({
            "category": cat, "month": m, "n": n,
            "p10": float(np.percentile(prices, 10)) if n >= 5 else np.nan,
            "p90": float(np.percentile(prices, 90)) if n >= 5 else np.nan,
        })
    traj = pd.DataFrame(traj_rows).sort_values(["category", "month"])

    fig, axes = plt.subplots(2, 3, figsize=(15, 9), sharex=True)
    axes_flat = axes.flatten()

    date_fmt = mdates.DateFormatter("%b %Y")
    date_loc = mdates.MonthLocator(interval=6)

    for ax, cat in zip(axes_flat, CATS_ORDER):
        sub = traj[traj["category"] == cat]
        color = CATEGORY_COLORS[cat]
        exposure = EXPOSURE_LABEL[cat]

        p10 = sub.dropna(subset=["p10"])
        p90 = sub.dropna(subset=["p90"])
        both = sub.dropna(subset=["p10", "p90"])

        ax.plot(p10["month"], p10["p10"], linestyle=":", marker="o", ms=3.5,
                color=color, alpha=0.6, linewidth=1.4, label="p10 — floor")
        ax.plot(p90["month"], p90["p90"], linestyle="-", marker="o", ms=3.5,
                color=color, alpha=1.0, linewidth=2.0, label="p90 — ceiling")
        if len(both):
            ax.fill_between(both["month"], both["p10"], both["p90"],
                            color=color, alpha=0.08)

        ax.set_yscale("log")
        log_dollar_ticks(ax, "y")
        ax.set_title(f"{CATEGORY_DISPLAY[cat]}  [{exposure}]", fontsize=FS_TITLE - 1)
        ax.set_ylabel("Price (USD)")
        ax.legend(loc="upper right", framealpha=0.9)
        ax.xaxis.set_major_locator(date_loc)
        ax.xaxis.set_major_formatter(date_fmt)

        # shock verticals — draw after autoscale
        ax.autoscale(axis="y")
        draw_shock_vlines(ax, CATEGORY_SHOCKS[cat])

    for ax in axes[1]:
        ax.set_xlabel("Month")
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    for ax in axes[0]:
        plt.setp(ax.get_xticklabels(), visible=False)

    axes_flat[-1].set_visible(False)

    fig.suptitle("Monthly price floor (p10) and ceiling (p90) by category\n"
                 "Dashed verticals: AI shock dates",
                 fontsize=FS_TITLE + 1, y=1.01)
    fig.tight_layout()
    save(fig, out_path)


# ── Figure 3: BC differential ─────────────────────────────────────────────────

def fig_bc_differential(quarterly: pd.DataFrame, out_path: Path) -> None:
    quarterly = quarterly.copy()
    quarterly["period"] = pd.to_datetime(quarterly["period"])

    # pivot and difference against data-entry (LOW_CONTROL)
    bc_col = "BC"
    pivot = quarterly.pivot_table(index="period", columns="category", values=bc_col)

    # the control column key may be "data/data-entry" or the low-control alias
    control_key = None
    for k in pivot.columns:
        if "data-entry" in k or k == LOW_CONTROL:
            control_key = k
            break
    if control_key is None:
        raise ValueError(f"Control column not found in {list(pivot.columns)}")

    diffs = pivot.subtract(pivot[control_key], axis=0).drop(columns=[control_key])

    treatment_cats = [c for c in CATS_ORDER if c != LOW_CONTROL and c in diffs.columns]

    fig, ax = plt.subplots(figsize=(11, 5.5))

    for cat in treatment_cats:
        if cat not in diffs.columns:
            continue
        color = CATEGORY_COLORS[cat]
        exposure = EXPOSURE_LABEL[cat]
        ax.plot(diffs.index, diffs[cat], "-o", ms=5.5, linewidth=1.8,
                color=color,
                label=f"{CATEGORY_DISPLAY[cat]} [{exposure}]")

    ax.axhline(0, color="black", linewidth=1.0, zorder=2)

    # shock verticals — draw one set for all treatment shocks, deduplicated
    all_shock_dates = sorted({d for cat in treatment_cats
                               for d in CATEGORY_SHOCKS.get(cat, [])})
    ax.autoscale(axis="y")
    draw_shock_vlines(ax, all_shock_dates, color="#888888", lw=0.75, alpha=0.6)

    ax.set_ylabel("BC (treatment) − BC (data-entry control)", fontsize=FS_LABEL)
    ax.set_xlabel("Quarter", fontsize=FS_LABEL)
    ax.set_title("Bimodality coefficient differential vs. data-entry control\n"
                 "Quarterly Sarle BC — treatment categories minus control",
                 fontsize=FS_TITLE)
    ax.legend(loc="upper left", framealpha=0.95)
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    fig.tight_layout()
    save(fig, out_path)


# ── Figure 4: ITS coefficients ────────────────────────────────────────────────

SHORT_NAME = {
    "graphics-design/creative-logo-design": "Logo design",
    "graphics-design/social-media-design":  "Social media",
    "content-writing/creative-writing":     "Creative writing",
}

CAT_COLORS_ITS = {
    "graphics-design/creative-logo-design": "#1f77b4",
    "graphics-design/social-media-design":  "#2ca02c",
    "content-writing/creative-writing":     "#d62728",
}

CATS_ITS = [
    "graphics-design/creative-logo-design",
    "graphics-design/social-media-design",
    "content-writing/creative-writing",
]


def sig_marker(p: float) -> str:
    if not pd.notna(p):
        return ""
    if p < 0.01:  return "***"
    if p < 0.05:  return "**"
    if p < 0.10:  return "*"
    return ""


def fig_its_coefficients(results: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))

    specs = [
        ("price_median", "beta2", "Price level change (β₂, USD)",    axes[0, 0]),
        ("price_median", "beta3", "Price slope change (β₃, USD/mo)", axes[0, 1]),
        ("BC",           "beta2", "BC level change (β₂)",            axes[1, 0]),
        ("BC",           "beta3", "BC slope change (β₃, per month)", axes[1, 1]),
    ]

    cat_positions = {cat: i for i, cat in enumerate(CATS_ITS)}
    x_labels = [SHORT_NAME[c] for c in CATS_ITS]

    for outcome, coef, title, ax in specs:
        sub = results[results["outcome"] == outcome].copy()
        val_col = "beta2_level" if coef == "beta2" else "beta3_slope"
        se_col  = "beta2_se"    if coef == "beta2" else "beta3_se"
        p_col   = "beta2_p"     if coef == "beta2" else "beta3_p"

        for cat in CATS_ITS:
            rows = sub[sub["category"] == cat].sort_values("shock_date").reset_index(drop=True)
            n = len(rows)
            if n == 0:
                continue
            color = CAT_COLORS_ITS[cat]
            base_x = cat_positions[cat]
            offsets = np.linspace(-0.28, 0.28, n) if n > 1 else np.array([0.0])

            for i, (_, row) in enumerate(rows.iterrows()):
                x   = base_x + offsets[i]
                val = row[val_col]
                se  = row[se_col]
                p   = row[p_col]
                ci  = 1.96 * se if pd.notna(se) else 0.0
                filled = pd.notna(p) and p < 0.05

                ax.errorbar(
                    x, val, yerr=ci, fmt="o",
                    color=color,
                    markerfacecolor=color if filled else "white",
                    markeredgecolor=color, markeredgewidth=1.8,
                    markersize=9.5, capsize=4.5, elinewidth=1.4,
                    capthick=1.4, zorder=3,
                )
                label = pd.Timestamp(row["shock_date"]).strftime("%b '%y")
                marker = sig_marker(p)
                offset_pts = 13 if val >= 0 else -18
                ax.annotate(
                    f"{label}{marker}",
                    (x, val), xytext=(0, offset_pts),
                    textcoords="offset points",
                    fontsize=FS_ANNOT, ha="center", color="#222222",
                )

        ax.axhline(0, color="black", linewidth=0.9, zorder=2)
        ax.set_xticks(range(len(CATS_ITS)))
        ax.set_xticklabels(x_labels, fontsize=FS_TICK)
        ax.set_xlim(-0.65, len(CATS_ITS) - 0.35)
        ax.set_title(title, fontsize=FS_TITLE - 1)

    fig.suptitle(
        "ITS coefficients: immediate level change (β₂) and slope change (β₃)\n"
        "per category and AI shock date   "
        "(filled = p < 0.05; whiskers = 95% CI;  *** p<0.01  ** p<0.05  * p<0.10)",
        fontsize=FS_TITLE, y=1.01,
    )
    fig.tight_layout()
    save(fig, out_path)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    panel    = pd.read_csv(PANEL_PATH)
    quarterly = pd.read_csv(QUARTERLY_PATH)
    its      = pd.read_csv(ITS_PATH)

    print("Generating Figure 1: GMM fits …")
    fig_gmm_fits(panel, OUT_DIR / "gmm_fits.png")

    print("Generating Figure 2: Floor/ceiling trajectories …")
    fig_floor_ceiling(panel, OUT_DIR / "floor_ceiling_trajectories.png")

    print("Generating Figure 3: BC differential …")
    fig_bc_differential(quarterly, OUT_DIR / "bc_differential.png")

    print("Generating Figure 4: ITS coefficients …")
    fig_its_coefficients(its, OUT_DIR / "its_coefficients.png")

    print(f"\nAll figures written to {OUT_DIR}/")


if __name__ == "__main__":
    main()
