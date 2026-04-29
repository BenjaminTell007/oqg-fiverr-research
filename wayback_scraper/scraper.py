"""Fetch and cache raw HTML from Wayback Machine snapshots."""

import time
import requests
import pandas as pd
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

SNAPSHOTS_DIR = Path(__file__).parent.parent / "data" / "snapshots"
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "output"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

JS_SHELL_THRESHOLD = 5_000  # chars; below this likely means an empty JS shell


def _wayback_url(timestamp: str, original_url: str) -> str:
    return f"https://web.archive.org/web/{timestamp}/{original_url}"


def _cache_path(timestamp: str, category: str) -> Path:
    safe_category = category.replace("/", "_").replace(" ", "_")
    return SNAPSHOTS_DIR / f"{timestamp}_{safe_category}.html"


# ---------------------------------------------------------------------------
# Public fetch functions
# ---------------------------------------------------------------------------

def fetch_with_requests(timestamp: str, original_url: str, category: str = "") -> str | None:
    """
    Fetch a Wayback snapshot using requests.

    Returns the raw HTML string, or None on any HTTP/network failure.
    Writes to data/snapshots/{timestamp}_{category}.html; skips if already cached.
    """
    cache = _cache_path(timestamp, category)
    if cache.exists():
        return cache.read_text(encoding="utf-8")

    url = _wayback_url(timestamp, original_url)
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        html = resp.text
    except requests.RequestException as exc:
        print(f"[requests] FAIL {timestamp}: {exc}")
        return None

    cache.write_text(html, encoding="utf-8")
    return html


def fetch_with_playwright(timestamp: str, original_url: str, category: str = "") -> str | None:
    """
    Fetch a Wayback snapshot using Playwright (headless Chromium).

    Waits for networkidle so JS-rendered content is present.
    Returns the full rendered HTML string, or None on failure.
    Writes to data/snapshots/{timestamp}_{category}.html; skips if already cached.
    """
    cache = _cache_path(timestamp, category)
    if cache.exists():
        return cache.read_text(encoding="utf-8")

    url = _wayback_url(timestamp, original_url)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            try:
                page.goto(url, wait_until="networkidle", timeout=45_000)
                html = page.content()
            except PWTimeout:
                html = page.content()  # take whatever rendered so far
            finally:
                browser.close()
    except Exception as exc:
        print(f"[playwright] FAIL {timestamp}: {exc}")
        return None

    cache.write_text(html, encoding="utf-8")
    return html


# ---------------------------------------------------------------------------
# Test block
# ---------------------------------------------------------------------------

def _pick_samples(df: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    """Return n evenly-spaced rows (earliest, middle(s), latest)."""
    if len(df) <= n:
        return df
    indices = [0] + [round(i * (len(df) - 1) / (n - 1)) for i in range(1, n - 1)] + [len(df) - 1]
    return df.iloc[sorted(set(indices))]


if __name__ == "__main__":
    inventory_path = OUTPUT_DIR / "snapshot_inventory.csv"
    if not inventory_path.exists():
        print(f"Not found: {inventory_path}. Run cdx.py first.")
        raise SystemExit(1)

    inventory = pd.read_csv(inventory_path)
    inventory = inventory.sort_values("timestamp").reset_index(drop=True)

    print(f"Loaded {len(inventory)} snapshots across categories: "
          f"{inventory['category'].unique().tolist()}\n")

    summary_rows = []

    for category, group in inventory.groupby("category"):
        samples = _pick_samples(group.reset_index(drop=True), n=3)
        print(f"--- {category} ({len(samples)} samples) ---")

        for _, row in samples.iterrows():
            ts      = row["timestamp"]
            orig    = row["url"]
            method  = "requests"

            html = fetch_with_requests(ts, orig, category=category)
            time.sleep(1.5)

            if html is None or len(html) < JS_SHELL_THRESHOLD:
                flag   = " [FLAGGED: too small, trying playwright]"
                method = "playwright"
                print(f"  {ts}  {category:<20}  requests -> {len(html) if html else 0} chars{flag}")
                html = fetch_with_playwright(ts, orig, category=category)
                time.sleep(2)

            size = len(html) if html else 0
            print(f"  {ts}  {category:<20}  {method:<10}  {size:>8} chars")
            summary_rows.append({
                "timestamp": ts,
                "category":  category,
                "method":    method,
                "html_size": size,
                "flagged":   size < JS_SHELL_THRESHOLD,
            })

    print("\n" + "=" * 65)
    print(f"{'timestamp':<16} {'category':<22} {'method':<10} {'chars':>8}  flagged")
    print("=" * 65)
    for r in summary_rows:
        flag = "*" if r["flagged"] else ""
        print(f"  {r['timestamp']:<14} {r['category']:<22} {r['method']:<10} {r['html_size']:>8}  {flag}")
