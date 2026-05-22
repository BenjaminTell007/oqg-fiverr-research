"""Publication-ready tables from existing CSVs.

Outputs Markdown and LaTeX for four tables to data/output/tables/:
  table1_panel_summary   — panel overview per category
  table2_weighted_did    — graded-dose DiD results
  table3_its_results     — ITS coefficients (price_median, selected shocks)
  table4_gmm_floor_ceiling — GMM pre/post floor and ceiling
"""

from pathlib import Path

import numpy as np
import pandas as pd

PANEL_PATH = Path("data/output/full_panel.csv")
WDID_CSV   = Path("data/output/robustness/weighted_did.csv")
ITS_CSV    = Path("data/output/its_results.csv")
GMM_CSV    = Path("data/output/gmm_graded_exposure_table.csv")
OUT_DIR    = Path("data/output/tables")

SUBSTITUTABILITY = {
    "graphics-design/creative-logo-design": 0.90,
    "graphics-design/social-media-design":  0.85,
    "content-writing/creative-writing":     0.80,
    "transcription-control-medium":         0.40,
    "data/data-entry":                      0.10,
}

DISPLAY_NAMES = {
    "graphics-design/creative-logo-design": "Creative logo design",
    "graphics-design/social-media-design":  "Social media design",
    "content-writing/creative-writing":     "Creative writing",
    "transcription-control-medium":         "Transcription",
    "data/data-entry":                      "Data entry",
}

EXPOSURE = {
    "graphics-design/creative-logo-design": "High",
    "graphics-design/social-media-design":  "High",
    "content-writing/creative-writing":     "High",
    "transcription-control-medium":         "Medium",
    "data/data-entry":                      "Low",
}

ROLE = {
    "graphics-design/creative-logo-design": "Treatment",
    "graphics-design/social-media-design":  "Treatment",
    "content-writing/creative-writing":     "Treatment",
    "transcription-control-medium":         "Control (medium)",
    "data/data-entry":                      "Control (low)",
}

CATS_ORDER = [
    "graphics-design/creative-logo-design",
    "graphics-design/social-media-design",
    "content-writing/creative-writing",
    "transcription-control-medium",
    "data/data-entry",
]

# Selected shocks to display in Table 3 — one or two per category
KEY_SHOCKS = {
    "graphics-design/creative-logo-design": ["2022-07-12", "2023-03-15"],
    "graphics-design/social-media-design":  ["2022-07-12", "2022-08-22", "2023-03-15"],
    "content-writing/creative-writing":     ["2022-11-30", "2024-05-13"],
}

EVENT_NAMES = {
    "2022-07-12": "Midjourney beta",
    "2022-08-22": "Stable Diffusion release",
    "2022-11-30": "ChatGPT launch",
    "2023-02-01": "ChatGPT Plus",
    "2023-03-14": "GPT-4",
    "2023-03-15": "Midjourney V5",
    "2024-05-13": "GPT-4o (free)",
    "2022-09-21": "Whisper (open-source)",
}


def sig_stars(p: float) -> str:
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def fmt_p(p: float) -> str:
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def make_table1(panel: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    panel["date_ts"] = pd.to_datetime(panel["date"])
    panel["year_month"] = panel["date_ts"].dt.to_period("M")

    rows = []
    for cat in CATS_ORDER:
        sub = panel[panel["category"] == cat]
        valid = sub.dropna(subset=["price"])
        n_gigs = len(valid)
        months = sub["year_month"].nunique()
        if len(sub) > 0:
            d_min = sub["date_ts"].min().strftime("%Y-%m")
            d_max = sub["date_ts"].max().strftime("%Y-%m")
            date_range = f"{d_min} – {d_max}"
        else:
            date_range = "—"
        med = f"${valid['price'].median():.0f}" if n_gigs > 0 else "—"
        rows.append({
            "Category": DISPLAY_NAMES[cat],
            "Role": ROLE[cat],
            "Exposure": EXPOSURE[cat],
            "S": f"{SUBSTITUTABILITY[cat]:.2f}",
            "N gigs": n_gigs,
            "Months covered": months,
            "Date range": date_range,
            "Median price": med,
        })

    df = pd.DataFrame(rows)
    caption = (
        "Table 1: Panel Summary. Five Fiverr service categories, monthly 2021–2024, "
        "extracted from Wayback Machine archived snapshots. N gigs excludes rows with null "
        "prices (low_confidence snapshots). S = AI substitutability score (researcher-assigned; "
        "see §2.3). 'Months covered' counts calendar months with at least one extracted gig."
    )
    return df, caption


def make_table2(wdid: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    keep_rows = [
        ("A_twfe",  "price_median", "S_x_post"),
        ("B_trend", "price_median", "S_x_post"),
        ("A_twfe",  "BC",           "S_x_post"),
        ("B_trend", "BC",           "S_x_post"),
    ]
    rows = []
    for spec, outcome, term in keep_rows:
        r = wdid[(wdid["spec"] == spec) & (wdid["outcome"] == outcome) & (wdid["term"] == term)]
        if len(r) == 0:
            continue
        r = r.iloc[0]
        spec_label = "Spec A (TWFE)" if spec == "A_twfe" else "Spec B (trend)"
        outcome_label = "Price median (USD)" if outcome == "price_median" else "Bimodality coeff. (BC)"
        implied = 0.80 * r["coef"]  # (S_max - S_min) = 0.90 - 0.10 = 0.80
        rows.append({
            "Outcome": outcome_label,
            "Spec": spec_label,
            "S×Post coef": f"{r['coef']:.3f}",
            "SE": f"({r['se']:.3f})",
            "p-value": fmt_p(r["p"]),
            "Sig.": sig_stars(r["p"]),
            "Implied gap": f"{implied:.1f}",
            "N obs": int(r["n_obs"]),
        })

    df = pd.DataFrame(rows)
    caption = (
        "Table 2: Substitutability-Weighted Graded-Dose DiD Results. "
        "Dependent variables: monthly median gig price (USD) and Sarle's bimodality coefficient (BC). "
        "Spec A = two-way fixed effects (category + month FE). "
        "Spec B = category FE + linear trend + S×Post + S×t. "
        "Standard errors are cluster-robust by category (5 clusters). "
        "Post cutoff = 2022-07-01. "
        "'Implied gap' = (S_max − S_min) × β = 0.80 × β: estimated differential post-2022 change "
        "between highest-exposure (logo design, S=0.90) and lowest-exposure (data entry, S=0.10). "
        "* p<0.10; ** p<0.05; *** p<0.01."
    )
    return df, caption


def make_table3(its: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    sub = its[its["outcome"] == "price_median"].copy()
    rows = []
    for cat, shocks in KEY_SHOCKS.items():
        for shock in shocks:
            r = sub[(sub["category"] == cat) & (sub["shock_date"] == shock)]
            if len(r) == 0:
                continue
            r = r.iloc[0]
            rows.append({
                "Category": DISPLAY_NAMES[cat],
                "Shock date": shock,
                "Event": EVENT_NAMES.get(shock, shock),
                "β₂ level": f"{r['beta2_level']:.2f}",
                "SE": f"({r['beta2_se']:.2f})",
                "p": fmt_p(r["beta2_p"]) + sig_stars(r["beta2_p"]),
                "β₃ slope": f"{r['beta3_slope']:.2f}",
                "SE.1": f"({r['beta3_se']:.2f})",
                "p.1": fmt_p(r["beta3_p"]) + sig_stars(r["beta3_p"]),
            })

    df = pd.DataFrame(rows)
    caption = (
        "Table 3: Interrupted Time Series (ITS) Results — Price Median Outcome (USD). "
        "Selected shocks per treatment category (full results available on request). "
        "β₂ = immediate level change at the shock date; β₃ = post-shock monthly slope change "
        "(relative to pre-shock trend). Standard errors via Newey-West HAC (L=3 lags). "
        "ITS is fit per category separately and should be interpreted alongside the "
        "cross-category graded-dose DiD (Table 2). * p<0.10; ** p<0.05; *** p<0.01."
    )
    return df, caption


def make_table4(gmm: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    name_map = {v: k for k, v in {
        k: v.split(" (")[0] for k, v in DISPLAY_NAMES.items()
    }.items()}

    def strip_exposure(s: str) -> str:
        return s.split(" (")[0]

    rows = []
    for _, r in gmm.iterrows():
        display = strip_exposure(r["category"])
        cat_key = next((k for k, v in DISPLAY_NAMES.items() if v == display), None)
        exposure = EXPOSURE.get(cat_key, "—") if cat_key else "—"
        rows.append({
            "Category": display,
            "Exposure": exposure,
            "Pre floor ($)": f"{r['pre_floor']:.2f}",
            "Post floor ($)": f"{r['post_floor']:.2f}",
            "Floor Δ ($)": f"{r['floor_Δ']:+.2f}",
            "Pre ceiling ($)": f"{r['pre_ceiling']:.2f}",
            "Post ceiling ($)": f"{r['post_ceiling']:.2f}",
            "Ceiling Δ ($)": f"{r['ceiling_Δ']:+.2f}",
        })

    df = pd.DataFrame(rows)
    df["_sort"] = df["Ceiling Δ ($)"].str.replace("+", "", regex=False).astype(float)
    df = df.sort_values("_sort").drop(columns="_sort").reset_index(drop=True)

    caption = (
        "Table 4: GMM (k=2) Pre- vs. Post-Shock Price Distribution Components. "
        "Floor = lower-mean Gaussian component; ceiling = upper-mean component; "
        "fitted to log-prices separately for pre- and post-primary-shock periods. "
        "Pre/post split at each category's primary AI shock date "
        "(logo design and social media: 2022-07-12; creative writing: 2022-11-30; "
        "transcription: 2022-09-21; data entry: 2022-07-12 as reference). "
        "Ceiling collapse dominates in high-exposure categories (−$23 to −$46); "
        "floor compression is modest (−$1.4 to −$3.6). "
        "Transcription's ceiling rose slightly (+$1.58) — no pre-existing premium tier to collapse."
    )
    return df, caption


def write_markdown(df: pd.DataFrame, caption: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(df.to_markdown(index=False))
        f.write(f"\n\n_{caption}_\n")
    print(f"  Saved {path}")


def write_latex(df: pd.DataFrame, caption: str, label: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    inner = df.to_latex(escape=True, index=False)
    full = (
        "\\begin{table}[htbp]\n"
        "\\centering\n"
        f"\\caption{{{caption}}}\n"
        f"\\label{{{label}}}\n"
        f"{inner}"
        "\\end{table}\n"
    )
    with open(path, "w") as f:
        f.write(full)
    print(f"  Saved {path}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(PANEL_PATH)
    wdid  = pd.read_csv(WDID_CSV)
    its   = pd.read_csv(ITS_CSV)
    gmm   = pd.read_csv(GMM_CSV)

    tables = [
        ("table1_panel_summary",    *make_table1(panel)),
        ("table2_weighted_did",     *make_table2(wdid)),
        ("table3_its_results",      *make_table3(its)),
        ("table4_gmm_floor_ceiling", *make_table4(gmm)),
    ]

    for name, df, caption in tables:
        write_markdown(df, caption, OUT_DIR / f"{name}.md")
        write_latex(df, caption, f"tab:{name}", OUT_DIR / f"{name}.tex")

    print(f"\nAll tables written to {OUT_DIR}/")


if __name__ == "__main__":
    main()
