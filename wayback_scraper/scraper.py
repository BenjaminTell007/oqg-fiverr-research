"""Fetch and cache raw HTML from Wayback Machine snapshots."""

import time
import hashlib
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

SNAPSHOTS_DIR = Path(__file__).parent.parent / "data" / "snapshots"
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Wayback sometimes needs a real browser for JS-rendered pages
_JS_REQUIRED_SIGNAL = "Please enable JavaScript"


def _cache_path(wayback_url: str) -> Path:
    key = hashlib.md5(wayback_url.encode()).hexdigest()
    return SNAPSHOTS_DIR / f"{key}.html"


def fetch_html(wayback_url: str, use_playwright: bool = False, sleep: float = 1.5) -> str:
    """Return raw HTML for a Wayback URL, reading from disk cache when available."""
    cache = _cache_path(wayback_url)
    if cache.exists():
        return cache.read_text(encoding="utf-8")

    html = (
        _fetch_playwright(wayback_url)
        if use_playwright
        else _fetch_requests(wayback_url)
    )

    # Fall back to Playwright if the page requires JS
    if not use_playwright and _JS_REQUIRED_SIGNAL in html:
        html = _fetch_playwright(wayback_url)

    cache.write_text(html, encoding="utf-8")
    time.sleep(sleep)
    return html


def _fetch_requests(url: str, retries: int = 3) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; OQG-research/1.0; "
            "+https://github.com/BenjaminTell007/oqg-fiverr-research)"
        )
    }
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return ""  # unreachable


def _fetch_playwright(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=45_000)
            html = page.content()
        except PWTimeout:
            html = page.content()
        finally:
            browser.close()
    return html
