"""Score sensitivity analysis — how robust is the graded-dose DiD finding
to perturbations of individual substitutability scores?

Reruns Spec A (TWFE) on price_median for:
  - One category's score varied at a time (±0.05, ±0.10, ±0.20)
  - All scores shifted simultaneously (same deltas)

Outputs:
  data/output/sensitivity/score_sensitivity.csv
  data/output/figures/final/sensitivity_forest.png
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import kurtosis, skew

PANEL_PATH = Path("data/output/full_panel.csv")
OUT_CSV    = Path("data/output/sensitivity/score_sensitivity.csv")
OUT_PNG    = Path("data/output/figures/final/sensitivity_forest.png")
DPI        = 300

PANEL_START = pd.Timestamp("2021-01-01")
POST_CUTOFF = pd.Timestamp("2022-07-01")
MIN_N_MONTH = 5

BASELINE_S = {
    "graphics-design/creative-logo-design": 0.90,
    "graphics-design/social-media-design":  0.85,
    "content-writing/creative-writing":     0.80,
    "transcription-control-medium":         0.40,
    "data/data-entry":                      0.10,
}

DISPLAY_SHORT = {
    "graphics-design/creative-logo-design": "Logo design",
    "graphics-design/social-media-design":  "Social media",
    "content-writing/creative-writing":     "Creative writing",
    "transcription-control-medium":         "Transcription",
    "data/data-entry":                      "Data entry",
    "all":                                  "All scores",
}

DELTAS = [-0.20, -0.10, -0.05, 0.00, 0.05, 0.10, 0.20]

# ── style (matches publication_figures.py) ────────────────────────────────────
mpl.rcParams.update({
    "font.family":        "sans-serif",
    "font.sans-serif":    ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size":          10,
    "axes.titlesize":     11,
    "axes.labelsize":     10,
    "xtick.labelsize":    9,
    "ytick.labelsize":    9,
    "figure.dpi":         DPI,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          True,
    "grid.alpha":         0.3,
    "grid.linewidth":     0.6,
})


# ── core DiD functions (copied from weighted_did.py) ──────────────────────────

def bimodality_coefficient(x: np.ndarray) -> float:
    n = len(x)
    if n < 4:
        return np.nan
    g = skew(x, bias=False)
    k = kurtosis(x, bias=False, fisher=True)
    correction = 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
    return (g ** 2 + 1) / (k + correction)


def month_index(ts: pd.Timestamp) -> int:
    return (ts.year - PANEL_START.year) * 12 + (ts.month - PANEL_START.month)


def aggregate_monthly(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy()
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()
    rows = []
    for (cat, m), g in df.groupby(["category", "month"]):
        prices = g["price"].dropna().to_numpy(dtype=float)
        n = len(prices)
        if n == 0:
            continue
        rows.append({
            "category": cat,
            "month": m,
            "t": month_index(m),
            "n": n,
            "price_median": float(np.median(prices)),
            "BC": bimodality_coefficient(prices) if n >= MIN_N_MONTH else np.nan,
        })
    return pd.DataFrame(rows).sort_values(["category", "month"]).reset_index(drop=True)


def add_dummies(df, col, prefix, drop_first=True):
    d = pd.get_dummies(df[col], prefix=prefix, drop_first=drop_first, dtype=float)
    new_cols = list(d.columns)
    out = pd.concat([df, d], axis=1)
    return out, new_cols


def fit_clustered(X, y, groups):
    model = sm.OLS(y, X.to_numpy()).fit()
    return model.get_robustcov_results(
        cov_type="cluster", groups=groups, use_correction=True,
    )


def run_spec_a(monthly: pd.DataFrame, scores: dict, outcome: str = "price_median") -> dict:
    df = monthly[monthly["category"].isin(scores)].copy()
    df["S"] = df["category"].map(scores).astype(float)
    df["post"] = (df["month"] >= POST_CUTOFF).astype(float)
    df["S_x_post"] = df["S"] * df["post"]

    d = df.dropna(subset=[outcome]).copy()
    d, cat_dummies = add_dummies(d, "category", "cat")
    d, month_dummies = add_dummies(d, "month", "m")
    cols = ["S_x_post"] + cat_dummies + month_dummies
    X = d[cols].copy()
    X.insert(0, "const", 1.0)
    y = d[outcome].to_numpy(dtype=float)
    groups = d["category"].astype("category").cat.codes.to_numpy()
    res = fit_clustered(X, y, groups)
    idx = list(X.columns).index("S_x_post")
    return {
        "coef": float(res.params[idx]),
        "se": float(res.bse[idx]),
        "p": float(res.pvalues[idx]),
        "n_obs": int(len(d)),
    }


# ── perturbation analysis ─────────────────────────────────────────────────────

def run_perturbation_analysis(monthly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    cats = list(BASELINE_S.keys())

    # Level 1: vary one category at a time
    for cat in cats:
        for delta in DELTAS:
            perturbed = BASELINE_S.copy()
            new_s = float(np.clip(BASELINE_S[cat] + delta, 0.01, 0.99))
            perturbed[cat] = new_s
            r = run_spec_a(monthly, perturbed)
            rows.append({
                "perturbed_category": cat,
                "delta": delta,
                "new_score": new_s,
                "coef": r["coef"],
                "se": r["se"],
                "p": r["p"],
                "n_obs": r["n_obs"],
                "sig_10": r["p"] < 0.10,
                "sig_05": r["p"] < 0.05,
            })

    # Level 2: shift all scores simultaneously
    for delta in DELTAS:
        perturbed = {c: float(np.clip(s + delta, 0.01, 0.99)) for c, s in BASELINE_S.items()}
        r = run_spec_a(monthly, perturbed)
        rows.append({
            "perturbed_category": "all",
            "delta": delta,
            "new_score": np.nan,
            "coef": r["coef"],
            "se": r["se"],
            "p": r["p"],
            "n_obs": r["n_obs"],
            "sig_10": r["p"] < 0.10,
            "sig_05": r["p"] < 0.05,
        })

    return pd.DataFrame(rows)


# ── forest plot ────────────────────────────────────────────────────────────────

def plot_sensitivity_forest(results: pd.DataFrame, baseline_coef: float,
                            baseline_se: float, out_path: Path) -> None:
    panel_keys = list(BASELINE_S.keys()) + ["all"]
    n_panels = len(panel_keys)
    fig, axes = plt.subplots(1, n_panels, figsize=(18, 4.5), sharey=True)

    for ax, cat in zip(axes, panel_keys):
        sub = results[results["perturbed_category"] == cat].sort_values("delta")
        deltas = sub["delta"].values
        coefs  = sub["coef"].values
        ses    = sub["se"].values
        pvals  = sub["p"].values

        # Error bar colors: green=p<0.10, red=p>=0.10, blue=baseline (delta=0)
        for d, c, s, p in zip(deltas, coefs, ses, pvals):
            if d == 0.0:
                color = "#1f77b4"
                zorder = 4
                ms = 7
            elif p < 0.10:
                color = "#2ca02c"
                zorder = 3
                ms = 5
            else:
                color = "#d62728"
                zorder = 3
                ms = 5
            ax.errorbar(d, c, yerr=1.96 * s, fmt="o", color=color,
                        capsize=3, capthick=1.0, linewidth=1.0,
                        markersize=ms, zorder=zorder)

        # Reference lines
        ax.axhline(0, color="#aaaaaa", linewidth=0.8, linestyle="-", zorder=1)
        ax.axhline(baseline_coef, color="#555555", linewidth=1.2, linestyle="-",
                   zorder=2, label=f"Baseline: {baseline_coef:.1f}")

        ax.set_xticks([-0.20, -0.10, 0.0, 0.10, 0.20])
        ax.set_xticklabels(["-0.20", "-0.10", "0", "+0.10", "+0.20"], fontsize=8)
        ax.set_xlabel("Δ score", fontsize=9)
        ax.set_title(DISPLAY_SHORT[cat], fontsize=10)
        ax.axvline(0, color="#dddddd", linewidth=0.8, linestyle=":")

    axes[0].set_ylabel("S×Post coefficient (USD)", fontsize=10)

    # Legend (outside last panel)
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="o", color="#2ca02c", lw=0, markersize=6, label="p < 0.10"),
        Line2D([0], [0], marker="o", color="#d62728", lw=0, markersize=6, label="p ≥ 0.10"),
        Line2D([0], [0], marker="o", color="#1f77b4", lw=0, markersize=8, label="Baseline (δ=0)"),
        Line2D([0], [0], color="#555555", lw=1.5, label=f"Baseline coef: {baseline_coef:.1f}"),
    ]
    axes[-1].legend(handles=legend_elements, fontsize=8, loc="lower right",
                    framealpha=0.85)

    fig.suptitle(
        "Score Sensitivity: S×Post coefficient (Spec A TWFE, price_median)\n"
        "under ±perturbation of substitutability scores",
        fontsize=11, y=1.03
    )
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out_path}")


def main():
    panel = pd.read_csv(PANEL_PATH)
    monthly = aggregate_monthly(panel)

    print("Running 42 perturbation models...")
    results = run_perturbation_analysis(monthly)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT_CSV, index=False)
    print(f"  Saved {OUT_CSV}  ({len(results)} rows)")

    baseline = results[(results["perturbed_category"] == list(BASELINE_S.keys())[0]) &
                       (results["delta"] == 0.0)].iloc[0]
    baseline_coef = float(baseline["coef"])
    baseline_se   = float(baseline["se"])

    print(f"\nBaseline: S×Post = {baseline_coef:.3f} (SE {baseline_se:.3f}, p={baseline['p']:.3f})")

    # Summarize stability
    non_baseline = results[results["delta"] != 0.0]
    n_sig = non_baseline["sig_10"].sum()
    n_total = len(non_baseline)
    print(f"Perturbation stability: {n_sig}/{n_total} runs still p<0.10 "
          f"({100*n_sig/n_total:.0f}%)")

    plot_sensitivity_forest(results, baseline_coef, baseline_se, OUT_PNG)


if __name__ == "__main__":
    main()
