"""
Full panel scrape across 3 confirmed Fiverr categories, 2021-2024.

Fetches every monthly Wayback snapshot, extracts gig prices, and writes
data/output/full_panel.csv.  Uses requests first; falls back to Playwright
if the returned HTML is under JS_SHELL_THRESHOLD chars.
"""

import sys
import time
import random
import pandas as pd
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))
from wayback_scraper.cdx import get_snapshots
from wayback_scraper.scraper import (
    fetch_with_requests, fetch_with_playwright,
    JS_SHELL_THRESHOLD, _cache_path,
)
from wayback_scraper.extract import extract_gigs

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CATEGORIES = {
    "content-writing/creative-writing": (
        "https://www.fiverr.com/categories/writing-translation/creative-writing"
    ),
    "graphics-design/creative-logo-design": (
        "https://www.fiverr.com/categories/graphics-design/creative-logo-design"
    ),
    "graphics-design/social-media-design": (
        "https://www.fiverr.com/categories/graphics-design/social-media-design"
    ),
}

FROM_DATE = "20210101"
TO_DATE   = "20241231"
DELAY_MIN = 2.0
DELAY_MAX = 3.0

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUTPUT_DIR / "full_panel.csv"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ts_to_date(ts: str) -> str:
    return f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"


def scrape_category(label: str, url: str) -> list[dict]:
    print(f"\n[{label}]  Querying CDX …")
    df_snaps = get_snapshots(url, FROM_DATE, TO_DATE)

    if df_snaps.empty:
        print(f"  WARNING: no snapshots returned for {label}")
        return []

    # Filter to 200 OK, sort chronologically
    df_snaps = df_snaps[df_snaps["statuscode"] == "200"].copy()
    df_snaps = df_snaps.sort_values("timestamp").reset_index(drop=True)
    print(f"  {len(df_snaps)} snapshots in range")

    rows = []
    skipped = 0
    playwright_used = 0

    for _, snap in tqdm(df_snaps.iterrows(), total=len(df_snaps),
                        desc=label.split("/")[-1], unit="snap"):
        ts  = snap["timestamp"]
        orig = snap["url"]

        # ── Fetch ────────────────────────────────────────────────────────────
        already_cached = _cache_path(ts, label).exists()

        html = fetch_with_requests(ts, orig, category=label)

        if html is None or len(html) < JS_SHELL_THRESHOLD:
            playwright_used += 1
            html = fetch_with_playwright(ts, orig, category=label)

        if not html:
            skipped += 1
            if not already_cached:
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            continue

        # ── Extract ──────────────────────────────────────────────────────────
        gigs = extract_gigs(html, timestamp=ts, category=label)
        for g in gigs:
            g["date"] = ts_to_date(ts)
        rows.extend(gigs)

        # Only sleep when we actually hit the network (not a cache read)
        if not already_cached:
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    print(f"  → {len(rows)} rows extracted  |  "
          f"{playwright_used} playwright fallbacks  |  {skipped} fetch failures")
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    all_rows = []

    for label, url in CATEGORIES.items():
        rows = scrape_category(label, url)
        all_rows.extend(rows)

    if not all_rows:
        print("\nNo data extracted. Exiting.")
        sys.exit(1)

    # ── Build DataFrame ──────────────────────────────────────────────────────
    COLS = ["timestamp", "date", "category", "price",
            "title", "seller", "tier", "rating", "reviews", "low_confidence"]
    df = pd.DataFrame(all_rows)[COLS]
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["category", "timestamp"]).reset_index(drop=True)

    df.to_csv(OUT_PATH, index=False)
    print(f"\nSaved {len(df):,} rows → {OUT_PATH}")

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("SCRAPE SUMMARY")
    print("=" * 72)

    df_prices = df[df["price"].notna()].copy()

    for cat, grp in df.groupby("category"):
        grp_p = df_prices[df_prices["category"] == cat]
        low_conf_pct = grp["low_confidence"].mean() * 100
        date_min = grp["date"].min().strftime("%Y-%m-%d")
        date_max = grp["date"].max().strftime("%Y-%m-%d")
        rows_total = len(grp)
        rows_price = len(grp_p)

        print(f"\n  {cat}")
        print(f"    Rows total / with price : {rows_total:>5} / {rows_price}")
        print(f"    Date range              : {date_min} → {date_max}")
        print(f"    Low-confidence rows     : {low_conf_pct:.1f}%")
        if not grp_p.empty:
            print(f"    Price  min / median / max : "
                  f"${grp_p['price'].min():.0f} / "
                  f"${grp_p['price'].median():.0f} / "
                  f"${grp_p['price'].max():.0f}")


if __name__ == "__main__":
    main()
