"""
Scrape Fiverr transcription category 2021-2024 and append to full_panel.csv.

Single-category run; label rows as 'transcription-control-medium' to mark
medium AI exposure (Whisper / speech-to-text models) in the graded DiD design.
Modeled on fill_2023_2024.py — same retry / backoff / incremental-write logic.
"""

import sys
import time
import random
import logging
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from wayback_scraper.cdx import get_snapshots
from wayback_scraper.scraper import (
    fetch_with_requests, fetch_with_playwright,
    JS_SHELL_THRESHOLD, _cache_path,
)
from wayback_scraper.extract import extract_gigs

CATEGORY_LABEL = "transcription-control-medium"
CATEGORY_URL = "https://www.fiverr.com/categories/writing-translation/transcription"

FROM_DATE = "20210101"
TO_DATE   = "20241231"
DELAY_MIN = 8.0
DELAY_MAX = 12.0

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "output"
LOG_DIR    = Path(__file__).parent.parent / "data"
PANEL_PATH = OUTPUT_DIR / "full_panel.csv"
LOG_PATH   = LOG_DIR / "scrape_transcription.log"

_PAUSE_TIERS = [
    (3, 5 * 60),
    (5, 15 * 60),
]

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


def ts_to_date(ts: str) -> str:
    return f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"


def merge_rows_into_panel(new_rows: list[dict]) -> None:
    """Append new_rows into full_panel.csv, deduped on (timestamp, category).

    Keeps the existing 11 columns intact (incl. ai_assisted/human_signal).
    New transcription rows get False for those flag columns by default;
    they can be regenerated end-to-end via add_keyword_flags.py if desired.
    """
    if not new_rows:
        return

    BASE_COLS = ["timestamp", "date", "category", "price",
                 "title", "seller", "tier", "rating", "reviews", "low_confidence"]

    new_df = pd.DataFrame(new_rows)
    for col in BASE_COLS:
        if col not in new_df.columns:
            new_df[col] = None
    new_df = new_df[BASE_COLS]
    new_df["date"] = pd.to_datetime(new_df["date"])
    new_df["timestamp"] = new_df["timestamp"].astype(str)

    if PANEL_PATH.exists():
        old_df = pd.read_csv(PANEL_PATH, parse_dates=["date"])
        old_df["timestamp"] = old_df["timestamp"].astype(str)
        # Pad new_df with any extra cols the old panel has (e.g. flag columns).
        for col in old_df.columns:
            if col not in new_df.columns:
                new_df[col] = False if old_df[col].dtype == bool else None
        new_df = new_df[old_df.columns]
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


def get_snapshots_with_retry(url: str, from_date: str, to_date: str,
                             max_attempts: int = 8) -> pd.DataFrame:
    for attempt in range(1, max_attempts + 1):
        df = get_snapshots(url, from_date, to_date)
        if not df.empty:
            return df
        wait = min(30 * 2 ** (attempt - 1), 600)
        log.warning("CDX returned empty (attempt %d/%d) — waiting %d s",
                    attempt, max_attempts, wait)
        time.sleep(wait)
    return pd.DataFrame(columns=["timestamp", "statuscode", "url"])


def scrape() -> int:
    log.info("=== START %s ===", CATEGORY_LABEL)
    df_snaps = get_snapshots_with_retry(CATEGORY_URL, FROM_DATE, TO_DATE)
    if df_snaps.empty:
        log.warning("No snapshots returned after CDX retries")
        return 0

    df_snaps = df_snaps[df_snaps["statuscode"] == "200"].copy()
    df_snaps = df_snaps.sort_values("timestamp").reset_index(drop=True)
    log.info("%d snapshots to process (2021-2024)", len(df_snaps))

    consecutive = 0
    tier_idx = 0
    total_rows = 0

    for i, (_, snap) in enumerate(df_snaps.iterrows(), 1):
        ts = snap["timestamp"]
        orig = snap["url"]
        already_cached = _cache_path(ts, CATEGORY_LABEL).exists()
        log.info("[%d/%d] ts=%s", i, len(df_snaps), ts)

        html = fetch_with_requests(ts, orig, category=CATEGORY_LABEL)
        used_playwright = False
        if html is None or len(html) < JS_SHELL_THRESHOLD:
            used_playwright = True
            html = fetch_with_playwright(ts, orig, category=CATEGORY_LABEL)

        if not html:
            consecutive += 1
            method = "playwright" if used_playwright else "requests"
            log.warning("FAIL  ts=%s  method=%s  consecutive=%d",
                        ts, method, consecutive)
            threshold, pause_secs = _PAUSE_TIERS[min(tier_idx, len(_PAUSE_TIERS) - 1)]
            if consecutive >= threshold:
                log.warning("Hit %d consecutive failures — pausing %d min",
                            consecutive, pause_secs // 60)
                time.sleep(pause_secs)
                consecutive = 0
                tier_idx = min(tier_idx + 1, len(_PAUSE_TIERS) - 1)
            if not already_cached:
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
            continue

        consecutive = 0
        tier_idx = 0

        gigs = extract_gigs(html, timestamp=ts, category=CATEGORY_LABEL)
        n_prices = sum(1 for g in gigs if g["price"] is not None)
        for g in gigs:
            g["date"] = ts_to_date(ts)

        merge_rows_into_panel(gigs)
        total_rows += len(gigs)

        method = "playwright" if used_playwright else "requests"
        cached_note = " [cached]" if already_cached else ""
        log.info("OK    ts=%s  method=%s  gigs=%d  prices=%d%s",
                 ts, method, len(gigs), n_prices, cached_note)

        if not already_cached:
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    log.info("=== DONE total_rows=%d ===", total_rows)
    return total_rows


def main():
    log.info("scrape_transcription.py start")
    grand_total = scrape()
    log.info("Grand total rows written: %d", grand_total)

    if PANEL_PATH.exists():
        df = pd.read_csv(PANEL_PATH, parse_dates=["date"])
        df["year"] = df["date"].dt.year
        sub = df[df["category"] == CATEGORY_LABEL]
        if not sub.empty:
            pivot = sub.groupby("year")["timestamp"].nunique()
            log.info("Transcription snapshots by year:\n%s", pivot.to_string())
            log.info("Total transcription rows: %d", len(sub))
            log.info("Rows with price: %d", sub["price"].notna().sum())


if __name__ == "__main__":
    main()
