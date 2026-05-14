"""Refined bimodality analysis: quarterly aggregation + sustained-shift metrics.

Replaces the noisy monthly first-crossing approach. Computes:
- Quarterly BC and Hartigan dip (with p-value) per category
- 6-month rolling-mean BC from monthly data (smoothed view)
- Treatment-minus-control BC differential per quarter (DiD-style proxy)
- Pre-shock vs post-shock mean BC per category (Welch t-test on quarterly BCs)

Outputs:
- data/output/bimodality_timeseries_v2.png
- data/output/bimodality_quarterly.csv
- stdout: pre/post mean BC table
"""

import json
from pathlib import Path

import diptest
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew, ttest_ind

PANEL = "data/output/full_panel.csv"
EVENTS = "data/ai_events.json"
OUT_PNG = "data/output/bimodality_timeseries_v2.png"
OUT_CSV = "data/output/bimodality_quarterly.csv"

BC_THRESHOLD = 0.555
DIP_ALPHA = 0.05
MIN_N_QUARTER = 10
MIN_N_MONTH = 5
LOW_CONTROL = "data-entry-control-low"
MEDIUM_CONTROL = "transcription-control-medium"
CONTROL_CATEGORY = LOW_CONTROL  # baseline for differentials

CATEGORY_SHOCKS = {
    "graphics-design/creative-logo-design":  ["2022-07-12", "2022-08-22", "2023-03-15"],
    "graphics-design/social-media-design":   ["2022-07-12", "2022-08-22", "2023-03-15"],
    "content-writing/creative-writing":      ["2022-11-30", "2023-02-01", "2023-03-14", "2024-05-13"],
    MEDIUM_CONTROL:                          ["2022-09-21"],
    LOW_CONTROL:                             [],
}

CATEGORY_COLORS = {
    "graphics-design/creative-logo-design":  "#1f77b4",
    "graphics-design/social-media-design":   "#2ca02c",
    "content-writing/creative-writing":      "#d62728",
    MEDIUM_CONTROL:                          "#ff7f0e",
    LOW_CONTROL:                             "#7f7f7f",
}


def bimodality_coefficient(x: np.ndarray) -> float:
    n = len(x)
    if n < 4:
        return np.nan
    g = skew(x, bias=False)
    k = kurtosis(x, bias=False, fisher=True)
    correction = 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    return (g ** 2 + 1) / (k + correction)


def per_period_stats(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """freq='Q' for quarterly, 'M' for monthly."""
    min_n = MIN_N_QUARTER if freq == "Q" else MIN_N_MONTH
    df = df.copy()
    df["period"] = pd.to_datetime(df["date"]).dt.to_period(freq).dt.to_timestamp()
    rows = []
    for (cat, p), g in df.groupby(["category", "period"]):
        prices = g["price"].dropna().to_numpy(dtype=float)
        n = len(prices)
        if n < min_n:
            rows.append({"category": cat, "period": p, "n": n,
                         "BC": np.nan, "dip": np.nan, "dip_p": np.nan})
            continue
        bc = bimodality_coefficient(prices)
        dip, p_val = diptest.diptest(prices)
        rows.append({"category": cat, "period": p, "n": n,
                     "BC": bc, "dip": dip, "dip_p": p_val})
    return pd.DataFrame(rows).sort_values(["category", "period"]).reset_index(drop=True)


def add_rolling_bc(monthly: pd.DataFrame, window: int = 6) -> pd.DataFrame:
    """Trailing 6-month rolling mean of monthly BC, per category."""
    out = []
    for cat, sub in monthly.groupby("category"):
        sub = sub.sort_values("period").copy()
        sub["BC_roll6"] = sub["BC"].rolling(window=window, min_periods=3).mean()
        out.append(sub)
    return pd.concat(out, ignore_index=True)


def differential_vs_control(quarterly: pd.DataFrame) -> pd.DataFrame:
    """For each quarter, treatment_BC - control_BC."""
    pivot = quarterly.pivot(index="period", columns="category", values="BC")
    if CONTROL_CATEGORY not in pivot.columns:
        raise ValueError(f"Control category {CONTROL_CATEGORY} missing")
    diffs = pivot.sub(pivot[CONTROL_CATEGORY], axis=0).drop(columns=[CONTROL_CATEGORY])
    return diffs.reset_index().melt(id_vars="period", var_name="category", value_name="BC_minus_control")


def pre_post_table(quarterly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cat, shocks in CATEGORY_SHOCKS.items():
        sub = quarterly[(quarterly["category"] == cat) & quarterly["BC"].notna()]
        if not shocks:
            rows.append({
                "category": cat,
                "primary_shock": None,
                "n_pre": len(sub), "mean_BC_pre": sub["BC"].mean(),
                "n_post": 0, "mean_BC_post": np.nan,
                "delta": np.nan, "welch_p": np.nan,
                "dip_p<0.05_share_pre": (sub["dip_p"] < DIP_ALPHA).mean() if len(sub) else np.nan,
                "dip_p<0.05_share_post": np.nan,
            })
            continue
        T = pd.to_datetime(shocks[0])
        pre = sub[sub["period"] < T]
        post = sub[sub["period"] >= T]
        if len(pre) >= 2 and len(post) >= 2:
            stat, p = ttest_ind(post["BC"], pre["BC"], equal_var=False, nan_policy="omit")
        else:
            p = np.nan
        rows.append({
            "category": cat,
            "primary_shock": T.date(),
            "n_pre": len(pre), "mean_BC_pre": pre["BC"].mean(),
            "n_post": len(post), "mean_BC_post": post["BC"].mean(),
            "delta": post["BC"].mean() - pre["BC"].mean(),
            "welch_p": p,
            "dip_p<0.05_share_pre": (pre["dip_p"] < DIP_ALPHA).mean() if len(pre) else np.nan,
            "dip_p<0.05_share_post": (post["dip_p"] < DIP_ALPHA).mean() if len(post) else np.nan,
        })
    return pd.DataFrame(rows)


def plot_v2(quarterly: pd.DataFrame, monthly_roll: pd.DataFrame,
            diffs: pd.DataFrame, events: dict, out_path: str) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(13, 11), sharex=True)
    ax_q, ax_roll, ax_diff = axes

    # Panel 1: Quarterly BC, with significant-dip markers filled
    for cat, sub in quarterly.groupby("category"):
        color = CATEGORY_COLORS.get(cat, "black")
        label = cat.split("/", 1)[-1]
        ax_q.plot(sub["period"], sub["BC"], "-", color=color, alpha=0.7, label=label)
        sig = sub[sub["dip_p"] < DIP_ALPHA]
        nonsig = sub[~(sub["dip_p"] < DIP_ALPHA)]
        ax_q.scatter(sig["period"], sig["BC"], color=color, s=42,
                     edgecolor="black", linewidth=0.7, zorder=3)
        ax_q.scatter(nonsig["period"], nonsig["BC"], color=color, s=22,
                     facecolors="white", edgecolor=color, linewidth=1.0, zorder=2)
    ax_q.axhline(BC_THRESHOLD, color="black", linestyle=":", linewidth=1)
    ax_q.set_ylabel("Quarterly BC")
    ax_q.set_title("Bimodality v2 — quarterly aggregation, rolling smoother, vs-control differential")
    ax_q.legend(loc="lower left", fontsize=8, ncol=4, framealpha=0.9)
    ax_q.grid(True, alpha=0.3)
    ax_q.text(0.01, 0.97, "filled marker = dip p<0.05 (reject unimodality)",
              transform=ax_q.transAxes, fontsize=8, va="top", color="dimgrey")

    # Panel 2: 6-month rolling mean BC
    for cat, sub in monthly_roll.groupby("category"):
        color = CATEGORY_COLORS.get(cat, "black")
        ax_roll.plot(sub["period"], sub["BC_roll6"], "-", color=color, linewidth=1.8,
                     label=cat.split("/", 1)[-1])
    ax_roll.axhline(BC_THRESHOLD, color="black", linestyle=":", linewidth=1)
    ax_roll.set_ylabel("6-month rolling mean BC")
    ax_roll.grid(True, alpha=0.3)

    # Panel 3: Treatment - control differential (quarterly)
    for cat, sub in diffs.groupby("category"):
        color = CATEGORY_COLORS.get(cat, "black")
        ax_diff.plot(sub["period"], sub["BC_minus_control"], "-o", ms=4, color=color,
                     label=cat.split("/", 1)[-1])
    ax_diff.axhline(0, color="black", linestyle="-", linewidth=0.7)
    ax_diff.set_ylabel("BC − control BC")
    ax_diff.set_xlabel("Quarter")
    ax_diff.grid(True, alpha=0.3)
    ax_diff.legend(loc="lower left", fontsize=8, ncol=3, framealpha=0.9)

    # Event verticals on all three panels
    for vector_key, vector in events.items():
        for ev in vector["events"]:
            d = pd.to_datetime(ev["date"])
            for ax in axes:
                ax.axvline(d, color="grey", linestyle="--", linewidth=0.6, alpha=0.45)

    fig.text(0.99, 0.005, "Dashed verticals: AI event dates (ai_events.json)",
             ha="right", va="bottom", fontsize=8, color="grey")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved {out_path}")


def main():
    df = pd.read_csv(PANEL)
    with open(EVENTS) as f:
        events = json.load(f)

    quarterly = per_period_stats(df, freq="Q")
    monthly = per_period_stats(df, freq="M")
    monthly_roll = add_rolling_bc(monthly, window=6)
    diffs = differential_vs_control(quarterly)

    Path("data/output").mkdir(parents=True, exist_ok=True)
    quarterly.to_csv(OUT_CSV, index=False)

    plot_v2(quarterly, monthly_roll, diffs, events, OUT_PNG)

    summary = pre_post_table(quarterly)
    print("\n" + "=" * 100)
    print("  Pre- vs post-shock mean BC (quarterly, primary shock = first event date)")
    print("=" * 100)
    with pd.option_context("display.float_format", lambda x: f"{x:.3f}"):
        print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
