"""Publication-ready bimodality outputs.

Reads data/output/bimodality_quarterly.csv (from bimodality_analysis_v2.py).
Produces:
- data/output/figures/bc_differential.png  (300 DPI, single-panel differential plot)
- data/output/dip_rejection_table.csv      (tidy CSV)
- data/output/dip_rejection_table.md       (markdown table for paper)
- stdout: same table, formatted
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

QUARTERLY = "data/output/bimodality_quarterly.csv"
EVENTS = "data/ai_events.json"
FIG_DIR = Path("data/output/figures")
TABLE_CSV = "data/output/dip_rejection_table.csv"
TABLE_MD = "data/output/dip_rejection_table.md"
DIFF_PNG = FIG_DIR / "bc_differential.png"

DIP_ALPHA = 0.05
CONTROL_CATEGORY = "data/data-entry"

CATEGORY_SHOCKS = {
    "graphics-design/creative-logo-design":  ["2022-07-12", "2022-08-22", "2023-03-15"],
    "graphics-design/social-media-design":   ["2022-07-12", "2022-08-22", "2023-03-15"],
    "content-writing/creative-writing":      ["2022-11-30", "2023-02-01", "2023-03-14", "2024-05-13"],
    CONTROL_CATEGORY:                        [],
}

CATEGORY_COLORS = {
    "graphics-design/creative-logo-design":  "#1f77b4",
    "graphics-design/social-media-design":   "#2ca02c",
    "content-writing/creative-writing":      "#d62728",
}

CATEGORY_DISPLAY = {
    "graphics-design/creative-logo-design":  "Creative logo design",
    "graphics-design/social-media-design":   "Social media design",
    "content-writing/creative-writing":      "Creative writing",
    CONTROL_CATEGORY:                        "Data entry (control)",
}

# Reference shock = first event for treatment categories; pooled image-gen
# launch date for the control comparison columns (so pre/post windows align).
CONTROL_REFERENCE_SHOCK = "2022-07-12"


def dip_rejection_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cat, shocks in CATEGORY_SHOCKS.items():
        sub = df[(df["category"] == cat) & df["dip_p"].notna()].copy()
        ref = pd.to_datetime(shocks[0]) if shocks else pd.to_datetime(CONTROL_REFERENCE_SHOCK)
        sub["period"] = pd.to_datetime(sub["period"])
        pre = sub[sub["period"] < ref]
        post = sub[sub["period"] >= ref]
        rows.append({
            "category": CATEGORY_DISPLAY[cat],
            "primary_shock": pd.to_datetime(shocks[0]).date() if shocks else "—",
            "pre_n_quarters": len(pre),
            "pre_reject_rate": (pre["dip_p"] < DIP_ALPHA).mean() if len(pre) else float("nan"),
            "post_n_quarters": len(post),
            "post_reject_rate": (post["dip_p"] < DIP_ALPHA).mean() if len(post) else float("nan"),
            "delta_pp": ((post["dip_p"] < DIP_ALPHA).mean() - (pre["dip_p"] < DIP_ALPHA).mean()) * 100
                        if len(pre) and len(post) else float("nan"),
        })
    return pd.DataFrame(rows)


def write_markdown_table(table: pd.DataFrame, path: str) -> None:
    lines = [
        "| Category | Primary shock | Pre n (quarters) | Pre dip-reject rate | Post n (quarters) | Post dip-reject rate | Δ (pp) |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, r in table.iterrows():
        pre_rate = "—" if pd.isna(r["pre_reject_rate"]) else f"{r['pre_reject_rate']*100:.0f}%"
        post_rate = "—" if pd.isna(r["post_reject_rate"]) else f"{r['post_reject_rate']*100:.0f}%"
        delta = "—" if pd.isna(r["delta_pp"]) else f"{r['delta_pp']:+.0f}"
        lines.append(
            f"| {r['category']} | {r['primary_shock']} | {r['pre_n_quarters']} | {pre_rate} | "
            f"{r['post_n_quarters']} | {post_rate} | {delta} |"
        )
    Path(path).write_text("\n".join(lines) + "\n")


def plot_differential(df: pd.DataFrame, events: dict, out_path: Path) -> None:
    df = df.copy()
    df["period"] = pd.to_datetime(df["period"])
    pivot = df.pivot(index="period", columns="category", values="BC")
    if CONTROL_CATEGORY not in pivot.columns:
        raise ValueError(f"control category {CONTROL_CATEGORY} missing")
    diffs = pivot.sub(pivot[CONTROL_CATEGORY], axis=0).drop(columns=[CONTROL_CATEGORY])

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for cat in diffs.columns:
        color = CATEGORY_COLORS[cat]
        ax.plot(diffs.index, diffs[cat], "-o", ms=5, linewidth=1.6,
                color=color, label=CATEGORY_DISPLAY[cat])

    ax.axhline(0, color="black", linewidth=0.8)

    seen = set()
    for vector in events.values():
        for ev in vector["events"]:
            d = pd.to_datetime(ev["date"])
            if d.year < 2021 or d.year > 2024:
                continue
            ax.axvline(d, color="grey", linestyle="--", linewidth=0.6, alpha=0.55)
            seen.add(ev["name"])

    ax.set_ylabel("BC (treatment) − BC (control)", fontsize=11)
    ax.set_xlabel("Quarter", fontsize=11)
    ax.set_title("Bimodality differential vs. data-entry control\n"
                 "Quarterly Sarle BC, treatment categories minus control",
                 fontsize=12)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
    ax.grid(True, alpha=0.3)
    ax.text(0.99, 0.02, "dashed verticals = AI event dates",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8, color="dimgrey")

    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}  (300 DPI)")


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(QUARTERLY)
    with open(EVENTS) as f:
        events = json.load(f)

    table = dip_rejection_table(df)
    table.to_csv(TABLE_CSV, index=False)
    write_markdown_table(table, TABLE_MD)

    print("\n" + "=" * 100)
    print("  Hartigan dip-test rejection of unimodality (dip_p < 0.05): pre- vs post-shock")
    print("=" * 100)
    pretty = table.copy()
    pretty["pre_reject_rate"] = pretty["pre_reject_rate"].apply(
        lambda x: "—" if pd.isna(x) else f"{x*100:.0f}%")
    pretty["post_reject_rate"] = pretty["post_reject_rate"].apply(
        lambda x: "—" if pd.isna(x) else f"{x*100:.0f}%")
    pretty["delta_pp"] = pretty["delta_pp"].apply(
        lambda x: "—" if pd.isna(x) else f"{x:+.0f}")
    print(pretty.to_string(index=False))

    plot_differential(df, events, DIFF_PNG)
    print(f"\nWrote {TABLE_CSV}")
    print(f"Wrote {TABLE_MD}")


if __name__ == "__main__":
    main()
