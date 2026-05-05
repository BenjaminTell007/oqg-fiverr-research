"""
Fetch the 2023-2024 gap for three under-covered categories and merge into
data/output/full_panel.csv incrementally (written after every success).

Retry logic:
  - 10-15 s randomized delay between every request
  - 3 consecutive failures  → 5 min pause, resume
  - 5 consecutive failures after first pause → 15 min pause, resume
  - Logs every success and failure with wall-clock timestamp
  - Runs until complete; only exits on total failure (all snapshots exhausted)
"""

import sys
import time
import random
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from wayback_scraper.cdx import get_snapshots
from wayback_scraper.scraper import (
    fetch_with_requests, fetch_with_playwright,
    JS_SHELL_THRESHOLD, _cache_path,
)
from wayback_scraper.extract import extract_gigs

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CATEGORIES = {
    "content-writing/creative-writing": (
        "https://www.fiverr.com/categories/writing-translation/creative-writing"
    ),
    "graphics-design/social-media-design": (
        "https://www.fiverr.com/categories/graphics-design/social-media-design"
    ),
    "data/data-entry": (
        "https://www.fiverr.com/categories/data/data-entry"
    ),
}

FROM_DATE  = "20230101"
TO_DATE    = "20241231"
DELAY_MIN  = 10.0
DELAY_MAX  = 15.0

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "output"
LOG_DIR    = Path(__file__).parent.parent / "data"
PANEL_PATH = OUTPUT_DIR / "full_panel.csv"
LOG_PATH   = LOG_DIR / "fill_2023_2024.log"

# Consecutive-failure thresholds and pause durations (seconds)
_PAUSE_TIERS = [
    (3, 5 * 60),    # tier 1: 3 failures → 5 min
    (5, 15 * 60),   # tier 2: 5 failures → 15 min
]

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ts_to_date(ts: str) -> str:
    return f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"


def merge_rows_into_panel(new_rows: list[dict]) -> None:
    """Append new_rows into full_panel.csv, deduplicating on timestamp+category."""
    if not new_rows:
        return

    COLS = ["timestamp", "date", "category", "price",
            "title", "seller", "tier", "rating", "reviews", "low_confidence"]

    new_df = pd.DataFrame(new_rows)
    for col in COLS:
        if col not in new_df.columns:
            new_df[col] = None
    new_df = new_df[COLS]
    new_df["date"] = pd.to_datetime(new_df["date"])
    # Normalize timestamp to str so key lookup works regardless of CSV dtype
    new_df["timestamp"] = new_df["timestamp"].astype(str)

    if PANEL_PATH.exists():
        old_df = pd.read_csv(PANEL_PATH, parse_dates=["date"])
        old_df["timestamp"] = old_df["timestamp"].astype(str)
        incoming_keys = set(zip(new_df["timestamp"], new_df["category"]))
        mask = old_df.apply(
            lambda r: (r["timestamp"], r["category"]) in incoming_keys, axis=1
        )
        old_df = old_df[~mask]
        combined = pd.concat([old_df, new_df], ignore_index=True)
    else:
        combined = new_df

    combined = combined.sort_values(["category", "timestamp"]).reset_index(drop=True)
    combined.to_csv(PANEL_PATH, index=False)


# ---------------------------------------------------------------------------
# Core fetch loop with retry / back-off
# ---------------------------------------------------------------------------

def get_snapshots_with_retry(url: str, from_date: str, to_date: str,
                             max_attempts: int = 8) -> pd.DataFrame:
    """Call get_snapshots with exponential back-off on transient failures."""
    for attempt in range(1, max_attempts + 1):
        df = get_snapshots(url, from_date, to_date)
        if not df.empty:
            return df
        wait = min(30 * 2 ** (attempt - 1), 600)   # 30 s, 60 s, 120 s … cap 10 min
        log.warning("CDX returned empty (attempt %d/%d) — waiting %d s before retry",
                    attempt, max_attempts, wait)
        time.sleep(wait)
    return pd.DataFrame(columns=["timestamp", "statuscode", "url"])


def scrape_category(label: str, url: str) -> int:
    """
    Fetch every 2023-2024 snapshot for one category.
    Returns the total number of gig rows written.
    """
    log.info("=== START %s ===", label)
    df_snaps = get_snapshots_with_retry(url, FROM_DATE, TO_DATE)

    if df_snaps.empty:
        log.warning("No snapshots returned for %s after all CDX retries", label)
        return 0

    df_snaps = df_snaps[df_snaps["statuscode"] == "200"].copy()
    df_snaps = df_snaps.sort_values("timestamp").reset_index(drop=True)
    log.info("%s: %d snapshots to process", label, len(df_snaps))

    consecutive = 0
    tier_idx    = 0          # index into _PAUSE_TIERS
    total_rows  = 0

    for i, (_, snap) in enumerate(df_snaps.iterrows(), 1):
        ts   = snap["timestamp"]
        orig = snap["url"]
        already_cached = _cache_path(ts, label).exists()

        log.info("[%d/%d] %s  %s", i, len(df_snaps), label, ts)

        # ── Fetch ───────────────────────────────────────────────────────────
        html = fetch_with_requests(ts, orig, category=label)

        used_playwright = False
        if html is None or len(html) < JS_SHELL_THRESHOLD:
            used_playwright = True
            html = fetch_with_playwright(ts, orig, category=label)

        # ── Failure path ────────────────────────────────────────────────────
        if not html:
            consecutive += 1
            method = "playwright" if used_playwright else "requests"
            log.warning("FAIL  ts=%s  method=%s  consecutive=%d", ts, method, consecutive)

            threshold, pause_secs = _PAUSE_TIERS[min(tier_idx, len(_PAUSE_TIERS) - 1)]
            if consecutive >= threshold:
                pause_mins = pause_secs // 60
                log.warning(
                    "Hit %d consecutive failures — pausing %d min (tier %d)",
                    consecutive, pause_mins, tier_idx + 1,
                )
                time.sleep(pause_secs)
                consecutive = 0
                tier_idx = min(tier_idx + 1, len(_PAUSE_TIERS) - 1)

            if not already_cached:
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            continue

        # ── Success path ─────────────────────────────────────────────────────
        consecutive = 0
        tier_idx    = 0      # reset escalation on any success

        gigs = extract_gigs(html, timestamp=ts, category=label)
        n_prices = sum(1 for g in gigs if g["price"] is not None)
        for g in gigs:
            g["date"] = ts_to_date(ts)

        merge_rows_into_panel(gigs)
        total_rows += len(gigs)

        method = "playwright" if used_playwright else "requests"
        cached_note = " [cached]" if already_cached else ""
        log.info(
            "OK    ts=%s  method=%s  gigs=%d  prices=%d%s",
            ts, method, len(gigs), n_prices, cached_note,
        )

        if not already_cached:
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    log.info("=== DONE %s  total_rows=%d ===", label, total_rows)
    return total_rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log.info("fill_2023_2024.py start — categories: %s", list(CATEGORIES))
    grand_total = 0

    for label, url in CATEGORIES.items():
        grand_total += scrape_category(label, url)

    log.info("All categories complete.  Grand total rows written: %d", grand_total)

    # Final summary from panel
    if PANEL_PATH.exists():
        df = pd.read_csv(PANEL_PATH, parse_dates=["date"])
        df["year"] = df["date"].dt.year
        pivot = df.groupby(["category", "year"])["timestamp"].nunique().unstack(fill_value=0)
        log.info("Panel snapshot counts by category × year:\n%s", pivot.to_string())


if __name__ == "__main__":
    main()
