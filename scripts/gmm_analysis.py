"""GMM (k=2) fits to post-treatment price distributions per category.

Outputs:
- data/output/figures/gmm_fits.png
    Overlaid pre vs post density curves per category (KDE) with GMM components.
- data/output/figures/floor_ceiling_trajectories.png
    Monthly p10 (floor) and p90 (ceiling) per category with shock-date verticals.
- data/output/gmm_floor_ceiling.csv
    Tidy CSV with floor mean/weight and ceiling mean/weight per category.
- stdout: floor/ceiling pre vs post comparison table.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde
from sklearn.mixture import GaussianMixture

PANEL = "data/output/full_panel.csv"
EVENTS = "data/ai_events.json"
FIG_DIR = Path("data/output/figures")
GMM_FITS_PNG = FIG_DIR / "gmm_fits.png"
TRAJ_PNG = FIG_DIR / "floor_ceiling_trajectories.png"
SUMMARY_CSV = "data/output/gmm_floor_ceiling.csv"

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
    CONTROL_CATEGORY:                        "#7f7f7f",
}

CATEGORY_DISPLAY = {
    "graphics-design/creative-logo-design":  "Creative logo design",
    "graphics-design/social-media-design":   "Social media design",
    "content-writing/creative-writing":      "Creative writing",
    CONTROL_CATEGORY:                        "Data entry (control)",
}

CONTROL_REFERENCE_SHOCK = "2022-07-12"

RNG = 42


def fit_gmm_k2(prices: np.ndarray) -> dict:
    """Fit 2-component GMM on log-prices for stability; return floor/ceiling stats in price units."""
    if len(prices) < 10:
        return {"floor_mean": np.nan, "floor_weight": np.nan,
                "ceiling_mean": np.nan, "ceiling_weight": np.nan, "n": len(prices)}
    X = np.log(prices.reshape(-1, 1))
    gmm = GaussianMixture(n_components=2, random_state=RNG, n_init=5).fit(X)
    means_log = gmm.means_.flatten()
    weights = gmm.weights_
    means_price = np.exp(means_log)
    order = np.argsort(means_price)
    floor_idx, ceil_idx = order[0], order[1]
    return {
        "floor_mean": float(means_price[floor_idx]),
        "floor_weight": float(weights[floor_idx]),
        "ceiling_mean": float(means_price[ceil_idx]),
        "ceiling_weight": float(weights[ceil_idx]),
        "n": len(prices),
    }


def split_pre_post(df: pd.DataFrame, cat: str):
    sub = df[df["category"] == cat].copy()
    shocks = CATEGORY_SHOCKS[cat]
    cut = pd.to_datetime(shocks[0]) if shocks else pd.to_datetime(CONTROL_REFERENCE_SHOCK)
    sub["date"] = pd.to_datetime(sub["date"])
    pre = sub[sub["date"] < cut]["price"].dropna().to_numpy(dtype=float)
    post = sub[sub["date"] >= cut]["price"].dropna().to_numpy(dtype=float)
    return pre, post, cut


def plot_gmm_fits(df: pd.DataFrame, out_path: Path) -> pd.DataFrame:
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    axes = axes.flatten()
    rows = []

    for ax, cat in zip(axes, CATEGORY_SHOCKS.keys()):
        pre, post, cut = split_pre_post(df, cat)
        color = CATEGORY_COLORS[cat]

        # KDE in log-space, plot in price-space
        x_grid = np.linspace(np.log(2), np.log(max(pre.max() if len(pre) else 1,
                                                    post.max() if len(post) else 1, 10)), 400)
        x_price = np.exp(x_grid)

        if len(pre) >= 5:
            kde_pre = gaussian_kde(np.log(pre))
            ax.plot(x_price, kde_pre(x_grid), "-", color=color, alpha=0.5,
                    linewidth=1.8, label=f"Pre  (n={len(pre)})")
        if len(post) >= 5:
            kde_post = gaussian_kde(np.log(post))
            ax.plot(x_price, kde_post(x_grid), "-", color=color, alpha=1.0,
                    linewidth=2.2, label=f"Post (n={len(post)})")

        # GMM fit on post — overlay component means
        gmm_post = fit_gmm_k2(post) if len(post) >= 10 else None
        gmm_pre = fit_gmm_k2(pre) if len(pre) >= 10 else None
        if gmm_post:
            ax.axvline(gmm_post["floor_mean"], color="black", linestyle=":", linewidth=1.0)
            ax.axvline(gmm_post["ceiling_mean"], color="black", linestyle=":", linewidth=1.0)
            ax.text(gmm_post["floor_mean"], ax.get_ylim()[1] * 0.95,
                    f" floor ${gmm_post['floor_mean']:.0f}\n  w={gmm_post['floor_weight']:.2f}",
                    fontsize=8, va="top", color="black")
            ax.text(gmm_post["ceiling_mean"], ax.get_ylim()[1] * 0.95,
                    f" ceil ${gmm_post['ceiling_mean']:.0f}\n  w={gmm_post['ceiling_weight']:.2f}",
                    fontsize=8, va="top", color="black")

        ax.set_xscale("log")
        ax.set_xlabel("Price (USD, log)")
        ax.set_ylabel("Density (log-price KDE)")
        ax.set_title(f"{CATEGORY_DISPLAY[cat]}\nshock cut: {cut.date()}", fontsize=10)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.3)

        rows.append({
            "category": cat,
            "pre_n": len(pre),
            "post_n": len(post),
            "pre_floor_mean": gmm_pre["floor_mean"] if gmm_pre else np.nan,
            "pre_floor_weight": gmm_pre["floor_weight"] if gmm_pre else np.nan,
            "pre_ceiling_mean": gmm_pre["ceiling_mean"] if gmm_pre else np.nan,
            "pre_ceiling_weight": gmm_pre["ceiling_weight"] if gmm_pre else np.nan,
            "post_floor_mean": gmm_post["floor_mean"] if gmm_post else np.nan,
            "post_floor_weight": gmm_post["floor_weight"] if gmm_post else np.nan,
            "post_ceiling_mean": gmm_post["ceiling_mean"] if gmm_post else np.nan,
            "post_ceiling_weight": gmm_post["ceiling_weight"] if gmm_post else np.nan,
        })

    fig.suptitle("Pre- vs post-shock price densities and GMM (k=2) modes",
                 fontsize=13, y=1.005)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}  (300 DPI)")
    return pd.DataFrame(rows)


def monthly_floor_ceiling(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()
    rows = []
    for (cat, m), g in df.groupby(["category", "month"]):
        prices = g["price"].dropna().to_numpy(dtype=float)
        if len(prices) < 5:
            rows.append({"category": cat, "month": m, "n": len(prices),
                         "p10": np.nan, "p50": np.nan, "p90": np.nan})
            continue
        rows.append({
            "category": cat, "month": m, "n": len(prices),
            "p10": float(np.percentile(prices, 10)),
            "p50": float(np.percentile(prices, 50)),
            "p90": float(np.percentile(prices, 90)),
        })
    return pd.DataFrame(rows).sort_values(["category", "month"]).reset_index(drop=True)


def plot_trajectories(traj: pd.DataFrame, events: dict, out_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharex=True)
    axes = axes.flatten()

    for ax, cat in zip(axes, CATEGORY_SHOCKS.keys()):
        sub = traj[traj["category"] == cat]
        color = CATEGORY_COLORS[cat]
        ax.plot(sub["month"], sub["p10"], "-o", ms=3, color=color, alpha=0.55,
                linewidth=1.0, label="p10 (floor)")
        ax.plot(sub["month"], sub["p90"], "-o", ms=3, color=color, alpha=1.0,
                linewidth=1.8, label="p90 (ceiling)")
        ax.fill_between(sub["month"], sub["p10"], sub["p90"], color=color, alpha=0.08)

        for d_str in CATEGORY_SHOCKS[cat]:
            d = pd.to_datetime(d_str)
            ax.axvline(d, color="black", linestyle="--", linewidth=0.7, alpha=0.7)

        ax.set_yscale("log")
        ax.set_title(CATEGORY_DISPLAY[cat], fontsize=11)
        ax.set_ylabel("Price (USD, log)")
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Month")
    axes[-2].set_xlabel("Month")
    fig.suptitle("Monthly p10 (floor) and p90 (ceiling) trajectories\n"
                 "Dashed verticals: AI shock dates per category",
                 fontsize=13, y=1.005)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}  (300 DPI)")


def summary_table(gmm_summary: pd.DataFrame) -> pd.DataFrame:
    out = []
    for _, r in gmm_summary.iterrows():
        cat = r["category"]
        if pd.isna(r["pre_floor_mean"]) or pd.isna(r["post_floor_mean"]):
            verdict = "insufficient n"
        else:
            floor_compressed = r["post_floor_mean"] < r["pre_floor_mean"]
            ceiling_rose = r["post_ceiling_mean"] > r["pre_ceiling_mean"]
            if floor_compressed and ceiling_rose:
                verdict = "floor compressed AND ceiling rose"
            elif floor_compressed:
                verdict = "floor compressed only"
            elif ceiling_rose:
                verdict = "ceiling rose only"
            else:
                verdict = "neither (floor up, ceiling down)"
        out.append({
            "category": CATEGORY_DISPLAY[cat],
            "pre_floor": r["pre_floor_mean"],
            "post_floor": r["post_floor_mean"],
            "floor_Δ": (r["post_floor_mean"] - r["pre_floor_mean"])
                       if pd.notna(r["pre_floor_mean"]) and pd.notna(r["post_floor_mean"]) else np.nan,
            "pre_ceiling": r["pre_ceiling_mean"],
            "post_ceiling": r["post_ceiling_mean"],
            "ceiling_Δ": (r["post_ceiling_mean"] - r["pre_ceiling_mean"])
                         if pd.notna(r["pre_ceiling_mean"]) and pd.notna(r["post_ceiling_mean"]) else np.nan,
            "verdict": verdict,
        })
    return pd.DataFrame(out)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(PANEL)
    with open(EVENTS) as f:
        events = json.load(f)

    gmm_summary = plot_gmm_fits(df, GMM_FITS_PNG)
    gmm_summary.to_csv(SUMMARY_CSV, index=False)

    traj = monthly_floor_ceiling(df)
    plot_trajectories(traj, events, TRAJ_PNG)

    print("\n" + "=" * 110)
    print("  GMM (k=2) floor/ceiling means: pre- vs post-shock per category")
    print("=" * 110)
    table = summary_table(gmm_summary)
    with pd.option_context("display.float_format", lambda x: f"{x:.2f}"):
        print(table.to_string(index=False))


if __name__ == "__main__":
    main()
