"""Interrupted Time Series (ITS) models per docs/its_specification.md.

For each treatment category, fits segmented OLS regression with Newey-West
HAC standard errors on monthly outcomes (price_median, BC). Extracts level
(beta2) and slope (beta3) coefficients per shock and writes:
- data/output/its_results.csv      (results table)
- data/output/figures/its_coefficients.png  (coefficient plot)
"""

import json
from pathlib import Path

import diptest
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import kurtosis, skew

PANEL = "data/output/full_panel.csv"
EVENTS = "data/ai_events.json"
OUT_CSV = "data/output/its_results.csv"
OUT_PNG = "data/output/figures/its_coefficients.png"

PANEL_START = pd.Timestamp("2021-01-01")
MIN_N_MONTH = 5

CATEGORY_SHOCKS = {
    "graphics-design/creative-logo-design": ["2022-07-12", "2022-08-22", "2023-03-15"],
    "graphics-design/social-media-design":  ["2022-07-12", "2022-08-22", "2023-03-15"],
    "content-writing/creative-writing":     ["2022-11-30", "2023-02-01", "2023-03-14", "2024-05-13"],
}

CONTROL_CATEGORY = "data/data-entry"

CATEGORY_COLORS = {
    "graphics-design/creative-logo-design": "#1f77b4",
    "graphics-design/social-media-design":  "#2ca02c",
    "content-writing/creative-writing":     "#d62728",
}

SHORT_NAME = {
    "graphics-design/creative-logo-design": "logo-design",
    "graphics-design/social-media-design":  "social-media",
    "content-writing/creative-writing":     "creative-writing",
    "data/data-entry":                      "data-entry (control)",
}


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
    """Collapse gig-level panel to one row per (category, month)."""
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
    out = pd.DataFrame(rows).sort_values(["category", "month"]).reset_index(drop=True)
    return out


def shock_month_index(date_str: str) -> int:
    """Bin event date to its calendar month and return t."""
    ts = pd.Timestamp(date_str).to_period("M").to_timestamp()
    return month_index(ts)


def build_design(sub: pd.DataFrame, shock_ts: list[int]) -> tuple[pd.DataFrame, list[str]]:
    """Build design matrix with intercept, trend, and per-shock D/slope terms."""
    X = pd.DataFrame({"const": 1.0, "t": sub["t"].astype(float)})
    term_names = []
    for k, Tk in enumerate(shock_ts, start=1):
        Dk = (sub["t"] >= Tk).astype(float).to_numpy()
        slope_k = np.where(sub["t"] >= Tk, sub["t"].to_numpy() - Tk, 0.0)
        X[f"D{k}"] = Dk
        X[f"slope{k}"] = slope_k
        term_names.append(f"D{k}")
        term_names.append(f"slope{k}")
    return X, term_names


def newey_west_lag(T: int) -> int:
    return int(np.floor(4 * (T / 100) ** (2 / 9)))


def fit_its(sub: pd.DataFrame, outcome: str, shocks: list[str]) -> dict:
    """Fit one OLS with HAC SEs. Returns dict with coefficients and p-values."""
    d = sub.dropna(subset=[outcome]).sort_values("t").reset_index(drop=True)
    T = len(d)
    if T < 8:
        return {"T": T, "ok": False}
    shock_ts = [shock_month_index(s) for s in shocks]
    X, _ = build_design(d, shock_ts)
    y = d[outcome].to_numpy(dtype=float)
    L = max(newey_west_lag(T), 1)
    model = sm.OLS(y, X.to_numpy()).fit()
    hac = model.get_robustcov_results(cov_type="HAC", maxlags=L, use_correction=True)
    params = dict(zip(X.columns, hac.params))
    pvals = dict(zip(X.columns, hac.pvalues))
    ses = dict(zip(X.columns, hac.bse))
    return {
        "T": T,
        "ok": True,
        "L": L,
        "params": params,
        "pvalues": pvals,
        "bse": ses,
        "rsq": hac.rsquared,
    }


def collect_results(monthly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cat, shocks in CATEGORY_SHOCKS.items():
        sub = monthly[monthly["category"] == cat].copy()
        for outcome in ("price_median", "BC"):
            fit = fit_its(sub, outcome, shocks)
            if not fit.get("ok"):
                continue
            for k, shock_date in enumerate(shocks, start=1):
                b2 = fit["params"].get(f"D{k}", np.nan)
                p2 = fit["pvalues"].get(f"D{k}", np.nan)
                se2 = fit["bse"].get(f"D{k}", np.nan)
                b3 = fit["params"].get(f"slope{k}", np.nan)
                p3 = fit["pvalues"].get(f"slope{k}", np.nan)
                se3 = fit["bse"].get(f"slope{k}", np.nan)
                rows.append({
                    "category": cat,
                    "outcome": outcome,
                    "shock_date": shock_date,
                    "T": fit["T"],
                    "newey_west_L": fit["L"],
                    "beta2_level": b2,
                    "beta2_se": se2,
                    "beta2_p": p2,
                    "beta2_sig_05": (p2 < 0.05) if pd.notna(p2) else False,
                    "beta2_sig_10": (p2 < 0.10) if pd.notna(p2) else False,
                    "beta3_slope": b3,
                    "beta3_se": se3,
                    "beta3_p": p3,
                    "beta3_sig_05": (p3 < 0.05) if pd.notna(p3) else False,
                    "beta3_sig_10": (p3 < 0.10) if pd.notna(p3) else False,
                    "rsq": fit["rsq"],
                })
    return pd.DataFrame(rows)


def sig_marker(p: float) -> str:
    if not pd.notna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def plot_coefficients(results: pd.DataFrame, out_path: str) -> None:
    """4-panel grid: rows = outcome, cols = level vs slope. Within each panel,
    one cluster per category, one bar per shock date, with 95% CI whiskers."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))
    plot_specs = [
        ("price_median", "beta2", "Price level change (β₂, USD)",     axes[0, 0]),
        ("price_median", "beta3", "Price slope change (β₃, USD/mo)",  axes[0, 1]),
        ("BC",           "beta2", "BC level change (β₂)",             axes[1, 0]),
        ("BC",           "beta3", "BC slope change (β₃, per month)",  axes[1, 1]),
    ]

    cats = list(CATEGORY_SHOCKS.keys())
    cat_positions = {cat: i for i, cat in enumerate(cats)}

    for outcome, coef, title, ax in plot_specs:
        sub = results[results["outcome"] == outcome].copy()
        if coef == "beta2":
            val_col, se_col, p_col = "beta2_level", "beta2_se", "beta2_p"
        else:
            val_col, se_col, p_col = "beta3_slope", "beta3_se", "beta3_p"

        # Plot each (category, shock) as offset point with 95% CI
        for cat in cats:
            cat_rows = sub[sub["category"] == cat].sort_values("shock_date").reset_index(drop=True)
            n_shocks = len(cat_rows)
            if n_shocks == 0:
                continue
            base_x = cat_positions[cat]
            color = CATEGORY_COLORS[cat]
            # spread offsets so shocks within a category sit side by side
            offsets = np.linspace(-0.28, 0.28, n_shocks) if n_shocks > 1 else np.array([0.0])
            for i, row in cat_rows.iterrows():
                x = base_x + offsets[i]
                val = row[val_col]
                se = row[se_col]
                p = row[p_col]
                ci = 1.96 * se if pd.notna(se) else 0.0
                filled = pd.notna(p) and p < 0.05
                edge = pd.notna(p) and p < 0.10
                ax.errorbar(
                    x, val, yerr=ci,
                    fmt="o", color=color,
                    markerfacecolor=color if filled else "white",
                    markeredgecolor=color, markeredgewidth=1.6,
                    markersize=9, capsize=4, elinewidth=1.2, zorder=3,
                )
                label = pd.Timestamp(row["shock_date"]).strftime("%b-%y")
                marker = sig_marker(p)
                ax.annotate(
                    f"{label}{marker}",
                    (x, val), xytext=(0, 11 if val >= 0 else -16),
                    textcoords="offset points",
                    fontsize=7.5, ha="center", color="black",
                )

        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xticks(range(len(cats)))
        ax.set_xticklabels([SHORT_NAME[c] for c in cats], fontsize=9)
        ax.set_xlim(-0.6, len(cats) - 0.4)
        ax.set_title(title, fontsize=11)
        ax.grid(True, axis="y", alpha=0.3)

    fig.suptitle(
        "ITS coefficients per category and shock date  "
        "(filled = p<0.05, hollow = p≥0.05; whiskers = 95% CI; *** p<0.01, ** p<0.05, * p<0.10)",
        fontsize=11, y=1.00,
    )
    fig.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved {out_path}")


def print_table(results: pd.DataFrame) -> None:
    print("\n" + "=" * 110)
    print("  ITS results: category × shock × outcome")
    print("=" * 110)
    cols = ["category", "outcome", "shock_date",
            "beta2_level", "beta2_se", "beta2_p",
            "beta3_slope", "beta3_se", "beta3_p"]
    with pd.option_context("display.float_format", lambda x: f"{x:.4f}",
                           "display.max_colwidth", 40,
                           "display.width", 160):
        print(results[cols].to_string(index=False))


def main():
    panel = pd.read_csv(PANEL)
    monthly = aggregate_monthly(panel)
    results = collect_results(monthly)

    Path("data/output").mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT_CSV, index=False)
    print(f"Saved {OUT_CSV}  ({len(results)} rows)")

    plot_coefficients(results, OUT_PNG)
    print_table(results)


if __name__ == "__main__":
    main()
