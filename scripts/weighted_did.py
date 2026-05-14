"""Substitutability-weighted graded-dose DiD (spec §4.1).

Replaces the binary treated/control split with a continuous substitutability
score `S_c` per category and estimates whether higher-substitutability
categories had differentially larger price and BC changes after the start
of the AI shock era (defined as 2022-07, the first image-gen shock month —
common cutoff across categories so the time FE remains identified).

Two specifications, each fit per outcome (price_median, BC):

  Spec A (primary):  Y_ct = γ_c + δ_t + β·(S_c × Post_t) + ε_ct
       — two-way fixed effects (category + month). β is the graded DiD.
       The substitutability main effect is absorbed by γ_c (S is
       time-invariant); the Post main effect is absorbed by δ_t.

  Spec B (with trend interaction):
       Y_ct = γ_c + α·t + β1·(S_c × Post_t) + β2·(S_c × t) + ε_ct
       — drops month FE so S×t is identified, gives the differential
       trend across the whole panel.

Standard errors: cluster-robust by category. With 5 clusters this is
underpowered for asymptotic inference; the small-cluster caveat is
noted in the printed summary.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import kurtosis, skew

PANEL_PATH = "data/output/full_panel.csv"
OUT_CSV = Path("data/output/robustness/weighted_did.csv")

PANEL_START = pd.Timestamp("2021-01-01")
POST_CUTOFF = pd.Timestamp("2022-07-01")  # earliest AI-era shock month
MIN_N_MONTH = 5

SUBSTITUTABILITY = {
    "graphics-design/creative-logo-design": 0.90,
    "graphics-design/social-media-design":  0.85,
    "content-writing/creative-writing":     0.80,
    "transcription-control-medium":         0.40,
    "data/data-entry":                      0.10,
}

SHORT = {
    "graphics-design/creative-logo-design": "logo-design",
    "graphics-design/social-media-design":  "social-media",
    "content-writing/creative-writing":     "creative-writing",
    "transcription-control-medium":         "transcription",
    "data/data-entry":                      "data-entry",
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


def build_panel(monthly: pd.DataFrame) -> pd.DataFrame:
    df = monthly[monthly["category"].isin(SUBSTITUTABILITY)].copy()
    df["S"] = df["category"].map(SUBSTITUTABILITY).astype(float)
    df["post"] = (df["month"] >= POST_CUTOFF).astype(float)
    df["S_x_post"] = df["S"] * df["post"]
    df["S_x_t"] = df["S"] * df["t"].astype(float)
    return df


def add_dummies(df: pd.DataFrame, col: str, prefix: str, drop_first: bool = True) -> tuple[pd.DataFrame, list[str]]:
    d = pd.get_dummies(df[col], prefix=prefix, drop_first=drop_first, dtype=float)
    new_cols = list(d.columns)
    out = pd.concat([df, d], axis=1)
    return out, new_cols


def fit_clustered(X: pd.DataFrame, y: np.ndarray, groups: np.ndarray) -> sm.regression.linear_model.RegressionResultsWrapper:
    model = sm.OLS(y, X.to_numpy()).fit()
    return model.get_robustcov_results(
        cov_type="cluster", groups=groups, use_correction=True,
    )


def run_spec_a(df: pd.DataFrame, outcome: str) -> dict:
    """TWFE: category FE + month FE + S*Post."""
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
        "spec": "A_twfe",
        "outcome": outcome,
        "term": "S_x_post",
        "coef": float(res.params[idx]),
        "se": float(res.bse[idx]),
        "p": float(res.pvalues[idx]),
        "n_obs": int(len(d)),
        "n_categories": int(d["category"].nunique()),
        "rsq": float(res.rsquared),
    }


def run_spec_b(df: pd.DataFrame, outcome: str) -> list[dict]:
    """Category FE + linear t + S*Post + S*t."""
    d = df.dropna(subset=[outcome]).copy()
    d, cat_dummies = add_dummies(d, "category", "cat")
    cols = ["t", "S_x_post", "S_x_t"] + cat_dummies
    X = d[cols].copy()
    X.insert(0, "const", 1.0)
    y = d[outcome].to_numpy(dtype=float)
    groups = d["category"].astype("category").cat.codes.to_numpy()
    res = fit_clustered(X, y, groups)
    rows = []
    for term in ("S_x_post", "S_x_t"):
        idx = list(X.columns).index(term)
        rows.append({
            "spec": "B_trend",
            "outcome": outcome,
            "term": term,
            "coef": float(res.params[idx]),
            "se": float(res.bse[idx]),
            "p": float(res.pvalues[idx]),
            "n_obs": int(len(d)),
            "n_categories": int(d["category"].nunique()),
            "rsq": float(res.rsquared),
        })
    return rows


def annotate(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["sig_05"] = df["p"] < 0.05
    df["sig_10"] = df["p"] < 0.10
    return df


def print_summary(results: pd.DataFrame) -> None:
    print("\n" + "=" * 92)
    print("  SUBSTITUTABILITY-WEIGHTED GRADED-DOSE DiD")
    print("=" * 92)
    print(f"  Substitutability scores:")
    for cat, s in SUBSTITUTABILITY.items():
        print(f"    {SHORT[cat]:18s}  S = {s:.2f}")
    print(f"  Post cutoff: {POST_CUTOFF.date()} (earliest AI-shock month)")
    print(f"  SEs: cluster-robust by category (5 clusters — small; treat as indicative)")

    print("\n  RESULTS (per spec × outcome × term):")
    print("-" * 92)
    with pd.option_context("display.float_format", lambda x: f"{x:.4f}",
                           "display.width", 160):
        print(results.to_string(index=False))

    print("\n" + "=" * 92)
    print("  PLAIN-ENGLISH INTERPRETATION")
    print("=" * 92)
    for outcome, outcome_label, unit in [
        ("price_median", "PRICE (USD)", "USD"),
        ("BC",           "BIMODALITY COEFFICIENT", "BC units"),
    ]:
        print(f"\n[{outcome_label}]")
        sub = results[results["outcome"] == outcome]
        a = sub[sub["spec"] == "A_twfe"].iloc[0]
        sign_a = "+" if a["coef"] >= 0 else "−"
        # Translate S×Post coefficient into a comparison between highest and
        # lowest S categories: difference in post-period change is
        # (S_max − S_min) × beta.
        s_max = max(SUBSTITUTABILITY.values())
        s_min = min(SUBSTITUTABILITY.values())
        spread = (s_max - s_min) * a["coef"]
        sign_spread = "+" if spread >= 0 else "−"
        print(f"  Spec A (TWFE): S×Post = {sign_a}{abs(a['coef']):.4f} "
              f"(SE {a['se']:.4f}, p = {a['p']:.4f})")
        print(f"    Implied gap between highest-S (0.90) and lowest-S (0.10) categories"
              f" in their post-vs-pre change: {sign_spread}{abs(spread):.3f} {unit}.")

        b_post = sub[(sub["spec"] == "B_trend") & (sub["term"] == "S_x_post")].iloc[0]
        b_trend = sub[(sub["spec"] == "B_trend") & (sub["term"] == "S_x_t")].iloc[0]
        print(f"  Spec B (linear trend): S×Post = {b_post['coef']:+.4f} (p={b_post['p']:.4f}),  "
              f"S×t = {b_trend['coef']:+.4f} per month (p={b_trend['p']:.4f})")

        # interpretive sentence
        direction_a = "larger" if a["coef"] > 0 else "smaller"
        if a["p"] < 0.05:
            verdict = (f"  → Significant: higher-substitutability categories saw a {direction_a} "
                       f"change in {outcome} after July 2022 than lower-substitutability ones.")
        elif a["p"] < 0.10:
            verdict = (f"  → Marginally significant (p<0.10): direction suggests higher-S "
                       f"categories had a {direction_a} post-2022 change.")
        else:
            verdict = (f"  → Not significant: cannot reject that the post-2022 change in "
                       f"{outcome} is the same across categories regardless of substitutability.")
        if outcome == "BC" and a["coef"] < 0 and a["p"] < 0.10:
            verdict += ("\n    Note: a negative S×Post on BC means high-substitutability "
                        "categories became LESS bimodal than low-substitutability ones after "
                        "the shock — opposite to the disruption hypothesis.")
        if outcome == "BC" and a["coef"] > 0 and a["p"] < 0.10:
            verdict += ("\n    Note: positive sign matches the disruption hypothesis "
                        "(price polarization rises with AI exposure).")
        print(verdict)

    print("\n" + "=" * 92)


def main():
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(PANEL_PATH)
    monthly = aggregate_monthly(panel)
    df = build_panel(monthly)

    rows = []
    for outcome in ("price_median", "BC"):
        rows.append(run_spec_a(df, outcome))
        rows.extend(run_spec_b(df, outcome))

    results = annotate(rows)
    results.to_csv(OUT_CSV, index=False)
    print(f"Saved {OUT_CSV}  ({len(results)} rows)")
    print_summary(results)


if __name__ == "__main__":
    main()
