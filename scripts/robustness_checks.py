"""Robustness checks for the ITS analysis (docs/its_specification.md §4).

1) Placebo ITS: re-run main spec with each shock date shifted -6 months.
   Significant placebo coefficients would suggest a pre-existing trend
   break unrelated to the actual AI launch.

2) Difference-in-Differences: for each treatment category, fit a 2x2
   DiD against the data-entry control with Post defined by the
   treatment's first shock date. The DiD coefficient (treated x post)
   isolates the differential change relative to platform-wide drift.

Writes:
- data/output/robustness/placebo_its_results.csv
- data/output/robustness/did_results.csv
- data/output/robustness/placebo_vs_real.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import kurtosis, skew

PANEL_PATH = "data/output/full_panel.csv"
ITS_RESULTS = "data/output/its_results.csv"
OUT_DIR = Path("data/output/robustness")
PLACEBO_CSV = OUT_DIR / "placebo_its_results.csv"
DID_CSV = OUT_DIR / "did_results.csv"
PLACEBO_PNG = OUT_DIR / "placebo_vs_real.png"

PANEL_START = pd.Timestamp("2021-01-01")
MIN_N_MONTH = 5
PLACEBO_OFFSET_MONTHS = 6

CATEGORY_SHOCKS = {
    "graphics-design/creative-logo-design": ["2022-07-12", "2022-08-22", "2023-03-15"],
    "graphics-design/social-media-design":  ["2022-07-12", "2022-08-22", "2023-03-15"],
    "content-writing/creative-writing":     ["2022-11-30", "2023-02-01", "2023-03-14", "2024-05-13"],
}
CONTROL_CATEGORY = "data/data-entry"

SHORT = {
    "graphics-design/creative-logo-design": "logo-design",
    "graphics-design/social-media-design":  "social-media",
    "content-writing/creative-writing":     "creative-writing",
}


# ---------- shared helpers (mirrors scripts/its_analysis.py) ----------

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


def shock_month_index(date_str: str) -> int:
    ts = pd.Timestamp(date_str).to_period("M").to_timestamp()
    return month_index(ts)


def newey_west_lag(T: int) -> int:
    return max(int(np.floor(4 * (T / 100) ** (2 / 9))), 1)


def fit_its(sub: pd.DataFrame, outcome: str, shock_dates: list[str]) -> dict | None:
    d = sub.dropna(subset=[outcome]).sort_values("t").reset_index(drop=True)
    T = len(d)
    if T < 8:
        return None
    shock_ts = [shock_month_index(s) for s in shock_dates]
    X = pd.DataFrame({"const": 1.0, "t": d["t"].astype(float)})
    for k, Tk in enumerate(shock_ts, start=1):
        X[f"D{k}"] = (d["t"] >= Tk).astype(float).to_numpy()
        X[f"slope{k}"] = np.where(d["t"] >= Tk, d["t"].to_numpy() - Tk, 0.0)
    y = d[outcome].to_numpy(dtype=float)
    L = newey_west_lag(T)
    model = sm.OLS(y, X.to_numpy()).fit()
    hac = model.get_robustcov_results(cov_type="HAC", maxlags=L, use_correction=True)
    return {
        "T": T, "L": L,
        "params": dict(zip(X.columns, hac.params)),
        "pvalues": dict(zip(X.columns, hac.pvalues)),
        "bse": dict(zip(X.columns, hac.bse)),
    }


# ---------- placebo ----------

def shift_dates(dates: list[str], months: int) -> list[str]:
    return [(pd.Timestamp(d) - pd.DateOffset(months=months)).strftime("%Y-%m-%d") for d in dates]


def run_placebo(monthly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cat, real_shocks in CATEGORY_SHOCKS.items():
        placebo_shocks = shift_dates(real_shocks, PLACEBO_OFFSET_MONTHS)
        sub = monthly[monthly["category"] == cat]
        for outcome in ("price_median", "BC"):
            fit = fit_its(sub, outcome, placebo_shocks)
            if fit is None:
                continue
            for k, (real_d, fake_d) in enumerate(zip(real_shocks, placebo_shocks), start=1):
                rows.append({
                    "category": cat,
                    "outcome": outcome,
                    "real_shock_date": real_d,
                    "placebo_shock_date": fake_d,
                    "beta2_level": fit["params"].get(f"D{k}", np.nan),
                    "beta2_se": fit["bse"].get(f"D{k}", np.nan),
                    "beta2_p": fit["pvalues"].get(f"D{k}", np.nan),
                    "beta3_slope": fit["params"].get(f"slope{k}", np.nan),
                    "beta3_se": fit["bse"].get(f"slope{k}", np.nan),
                    "beta3_p": fit["pvalues"].get(f"slope{k}", np.nan),
                })
    return pd.DataFrame(rows)


# ---------- difference-in-differences ----------

def fit_did_pair(monthly: pd.DataFrame, treated_cat: str, post_date: str) -> dict:
    """2x2 DiD: outcome ~ const + treated + post + treated*post + t.
    HAC SEs with auto lag length.
    """
    pair = monthly[monthly["category"].isin([treated_cat, CONTROL_CATEGORY])].copy()
    pair["treated"] = (pair["category"] == treated_cat).astype(float)
    cutoff_t = shock_month_index(post_date)
    pair["post"] = (pair["t"] >= cutoff_t).astype(float)
    pair["treated_x_post"] = pair["treated"] * pair["post"]

    results = {}
    for outcome in ("price_median", "BC"):
        d = pair.dropna(subset=[outcome]).sort_values(["category", "t"]).reset_index(drop=True)
        T = len(d)
        if T < 12:
            results[outcome] = None
            continue
        X = d[["treated", "post", "treated_x_post", "t"]].copy()
        X.insert(0, "const", 1.0)
        y = d[outcome].to_numpy(dtype=float)
        L = newey_west_lag(T)
        m = sm.OLS(y, X.to_numpy()).fit()
        hac = m.get_robustcov_results(cov_type="HAC", maxlags=L, use_correction=True)
        idx = list(X.columns).index("treated_x_post")
        results[outcome] = {
            "T": T, "L": L,
            "did": float(hac.params[idx]),
            "did_se": float(hac.bse[idx]),
            "did_p": float(hac.pvalues[idx]),
            "rsq": float(hac.rsquared),
        }
    return results


def run_did(monthly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cat, shocks in CATEGORY_SHOCKS.items():
        first_shock = shocks[0]
        pair_res = fit_did_pair(monthly, cat, first_shock)
        for outcome, r in pair_res.items():
            if r is None:
                continue
            rows.append({
                "treated_category": cat,
                "control_category": CONTROL_CATEGORY,
                "outcome": outcome,
                "post_cutoff": first_shock,
                "T": r["T"],
                "newey_west_L": r["L"],
                "did_coef": r["did"],
                "did_se": r["did_se"],
                "did_p": r["did_p"],
                "did_sig_05": r["did_p"] < 0.05,
                "did_sig_10": r["did_p"] < 0.10,
                "rsq": r["rsq"],
            })
    return pd.DataFrame(rows)


# ---------- comparison plot ----------

def plot_placebo_vs_real(real: pd.DataFrame, placebo: pd.DataFrame, out_path: Path) -> None:
    """Side-by-side: share of significant coefficients at p<0.05, real vs placebo,
    broken out by outcome × coefficient type."""
    def share(df: pd.DataFrame, p_col: str) -> float:
        s = df[p_col].dropna()
        return float((s < 0.05).mean()) if len(s) else 0.0

    cats_outcomes = [("price_median", "β₂ (level)", "beta2_p"),
                     ("price_median", "β₃ (slope)", "beta3_p"),
                     ("BC",           "β₂ (level)", "beta2_p"),
                     ("BC",           "β₃ (slope)", "beta3_p")]

    labels, real_share, fake_share = [], [], []
    for outcome, coef_lbl, p_col in cats_outcomes:
        labels.append(f"{outcome}\n{coef_lbl}")
        real_share.append(share(real[real["outcome"] == outcome], p_col))
        fake_share.append(share(placebo[placebo["outcome"] == outcome], p_col))

    x = np.arange(len(labels))
    width = 0.38
    fig, ax = plt.subplots(figsize=(9, 5.0))
    ax.bar(x - width / 2, real_share, width, label="Real shocks", color="#1f77b4")
    ax.bar(x + width / 2, fake_share, width, label="Placebo (-6 mo)", color="#bbbbbb")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Share of coefficients with p < 0.05")
    ax.set_ylim(0, 1.0)
    ax.set_title("Placebo robustness: significance share, real vs −6mo shifted shocks", fontsize=11)
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()
    for xi, (r, f) in enumerate(zip(real_share, fake_share)):
        ax.text(xi - width / 2, r + 0.02, f"{r:.2f}", ha="center", fontsize=9)
        ax.text(xi + width / 2, f + 0.02, f"{f:.2f}", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved {out_path}")


# ---------- summary ----------

def sig_share(df: pd.DataFrame, p_col: str) -> tuple[int, int]:
    s = df[p_col].dropna()
    return int((s < 0.05).sum()), int(len(s))


def print_summary(real: pd.DataFrame, placebo: pd.DataFrame, did: pd.DataFrame) -> None:
    print("\n" + "=" * 88)
    print(" ROBUSTNESS SUMMARY")
    print("=" * 88)

    print("\n[1] PLACEBO TEST (shocks shifted -6 months)")
    print("-" * 88)
    for outcome in ("price_median", "BC"):
        for p_col, label in [("beta2_p", "β₂ level"), ("beta3_p", "β₃ slope")]:
            r_sig, r_n = sig_share(real[real["outcome"] == outcome], p_col)
            f_sig, f_n = sig_share(placebo[placebo["outcome"] == outcome], p_col)
            print(f"  {outcome:13s} {label:9s}  real: {r_sig}/{r_n} sig at p<0.05  | "
                  f"placebo: {f_sig}/{f_n}")

    print("\n[2] DIFFERENCE-IN-DIFFERENCES (treated vs data-entry control)")
    print("-" * 88)
    with pd.option_context("display.float_format", lambda x: f"{x:.4f}",
                           "display.width", 160):
        cols = ["treated_category", "outcome", "post_cutoff",
                "did_coef", "did_se", "did_p", "did_sig_05"]
        print(did[cols].to_string(index=False))

    # plain english verdict
    print("\n" + "=" * 88)
    print(" PLAIN-ENGLISH VERDICT")
    print("=" * 88)

    # placebo verdict
    total_real_sig = (real["beta2_p"] < 0.05).sum() + (real["beta3_p"] < 0.05).sum()
    total_real_n = real["beta2_p"].notna().sum() + real["beta3_p"].notna().sum()
    total_fake_sig = (placebo["beta2_p"] < 0.05).sum() + (placebo["beta3_p"] < 0.05).sum()
    total_fake_n = placebo["beta2_p"].notna().sum() + placebo["beta3_p"].notna().sum()
    print(f"\nPlacebo: real shocks → {total_real_sig}/{total_real_n} coefficients significant; "
          f"placebo shocks → {total_fake_sig}/{total_fake_n}.")
    if total_real_n and total_fake_n:
        real_rate = total_real_sig / total_real_n
        fake_rate = total_fake_sig / total_fake_n
        margin = real_rate - fake_rate
        if margin > 0.20:
            print("  → Real significance rate clearly exceeds placebo: the timing of real "
                  "events carries information beyond a generic trend break six months "
                  "earlier. Main result is supported by the placebo check.")
        elif margin > 0.05:
            print("  → Real beats placebo modestly. The timing claim is suggestive but not "
                  "conclusive; the slope-change terms in particular pick up broad inflections "
                  "regardless of the exact pivot date.")
        else:
            print("  → Real and placebo significance rates are essentially indistinguishable. "
                  "Shifting the shock dates six months earlier produces a model that fits the "
                  "data about as well, which means the within-category ITS is NOT time-locked "
                  "to the actual AI launch dates. The β₂/β₃ coefficients should be interpreted "
                  "as describing general trend changes during this period, not as causal "
                  "estimates of effects from the specific events.")

    # DiD verdict
    bc_did = did[did["outcome"] == "BC"]
    price_did = did[did["outcome"] == "price_median"]
    bc_sig = bc_did[bc_did["did_p"] < 0.05]
    price_sig = price_did[price_did["did_p"] < 0.05]

    print(f"\nDiD (BC):    {len(bc_sig)}/{len(bc_did)} treatment-vs-control pairs significant at p<0.05.")
    if len(bc_sig):
        for _, r in bc_sig.iterrows():
            sign = "+" if r["did_coef"] > 0 else "−"
            print(f"   {SHORT[r['treated_category']]:18s}  DiD = {sign}{abs(r['did_coef']):.3f}  (p={r['did_p']:.3f})")

    print(f"\nDiD (price): {len(price_sig)}/{len(price_did)} treatment-vs-control pairs significant at p<0.05.")
    if len(price_sig):
        for _, r in price_sig.iterrows():
            sign = "+" if r["did_coef"] > 0 else "−"
            print(f"   {SHORT[r['treated_category']]:18s}  DiD = {sign}{abs(r['did_coef']):.3f}  (p={r['did_p']:.3f})")

    # Direction check: disruption hypothesis predicts positive DiD on BC
    # (treated becomes more bimodal than control post-shock).
    bc_pos_sig = bc_sig[bc_sig["did_coef"] > 0]
    bc_neg_sig = bc_sig[bc_sig["did_coef"] < 0]

    print()
    if len(bc_sig) == 0 and len(price_sig) == 0:
        print("DiD verdict: no treated-vs-control divergence is significant — the within-category "
              "ITS effects may reflect Fiverr-wide drift rather than AI-specific disruption.")
    elif len(bc_neg_sig) > len(bc_pos_sig) and len(bc_neg_sig) >= 2:
        print("DiD verdict: treated categories DO diverge significantly from the data-entry control, "
              "but the sign on BC is NEGATIVE — treated categories became less bimodal than control "
              "post-shock, the opposite of what the disruption hypothesis predicts. Plausible "
              "readings: (a) data-entry was itself affected by an unmodeled 2022+ shock that drove "
              "its BC up faster than treated, making the control a poor counterfactual; "
              "(b) AI tools compressed rather than polarized treated-category pricing; "
              "(c) the within-category ITS picked up trends shared with control.")
    elif len(bc_pos_sig) >= 2:
        print("DiD verdict: treated categories diverge significantly upward in BC vs control — "
              "consistent with the disruption hypothesis (treated pricing becomes more bimodal "
              "than control after the shock).")
    else:
        print("DiD verdict: mixed — some categories show significant divergence from control, "
              "others do not. Causal interpretation should be cautious and category-specific.")
    print("=" * 88)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(PANEL_PATH)
    monthly = aggregate_monthly(panel)

    placebo = run_placebo(monthly)
    placebo.to_csv(PLACEBO_CSV, index=False)
    print(f"Saved {PLACEBO_CSV}  ({len(placebo)} rows)")

    did = run_did(monthly)
    did.to_csv(DID_CSV, index=False)
    print(f"Saved {DID_CSV}  ({len(did)} rows)")

    real = pd.read_csv(ITS_RESULTS)
    plot_placebo_vs_real(real, placebo, PLACEBO_PNG)

    print_summary(real, placebo, did)


if __name__ == "__main__":
    main()
