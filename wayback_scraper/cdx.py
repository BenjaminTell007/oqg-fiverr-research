"""CDX API querying for Wayback Machine snapshots."""

import json
import time
import requests
import pandas as pd
from pathlib import Path

CDX_API = "http://web.archive.org/cdx/search/cdx"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "output"


def get_snapshots(category_url: str, from_date: str, to_date: str) -> pd.DataFrame:
    """
    Query the Wayback CDX API for archived snapshots of a URL.

    Args:
        category_url: The original URL to look up (e.g. https://www.fiverr.com/...)
        from_date:    Start date as YYYYMMdd string, e.g. "20210101"
        to_date:      End date   as YYYYMMdd string, e.g. "20260401"

    Returns:
        DataFrame with columns [timestamp, statuscode, url], one row per snapshot.
        Empty DataFrame on no results or error.
    """
    params = {
        "url": category_url,
        "output": "json",
        "fl": "timestamp,statuscode,original",
        "filter": "statuscode:200",
        "collapse": "timestamp:6",
        "from": from_date,
        "to": to_date,
    }

    try:
        resp = requests.get(CDX_API, params=params, timeout=30)
        resp.raise_for_status()
    except requests.HTTPError as exc:
        print(f"[cdx] HTTP error for {category_url}: {exc}")
        return pd.DataFrame(columns=["timestamp", "statuscode", "url"])
    except requests.RequestException as exc:
        print(f"[cdx] Request failed for {category_url}: {exc}")
        return pd.DataFrame(columns=["timestamp", "statuscode", "url"])

    try:
        rows = resp.json()
    except ValueError:
        print(f"[cdx] Invalid JSON response for {category_url}")
        return pd.DataFrame(columns=["timestamp", "statuscode", "url"])

    if not rows or len(rows) < 2:
        return pd.DataFrame(columns=["timestamp", "statuscode", "url"])

    # CDX returns [header_row, ...data_rows] when output=json
    header, *data = rows
    df = pd.DataFrame(data, columns=header)
    df = df.rename(columns={"original": "url"})
    df = df[["timestamp", "statuscode", "url"]]
    return df


# ---------------------------------------------------------------------------
# URL probing
# ---------------------------------------------------------------------------

def probe_category_urls(
    candidate_urls: list[str],
    from_date: str = "20210101",
    to_date: str = "20260401",
    sleep: float = 1.0,
) -> dict:
    """
    Query the CDX API for each candidate URL and pick the one with the most snapshots.

    Args:
        candidate_urls: URL variants to try for a single category.
        from_date:      CDX from date (YYYYMMdd).
        to_date:        CDX to date   (YYYYMMdd).
        sleep:          Seconds to wait between requests.

    Returns:
        {
            "canonical_url": str,       # variant with the most snapshots
            "snapshot_count": int,
            "results": [                # all variants, sorted by count desc
                {"url": str, "snapshot_count": int},
                ...
            ]
        }
    """
    results = []
    for url in candidate_urls:
        df = get_snapshots(url, from_date, to_date)
        results.append({"url": url, "snapshot_count": len(df)})
        time.sleep(sleep)

    results.sort(key=lambda r: r["snapshot_count"], reverse=True)
    best = results[0]
    return {
        "canonical_url": best["url"],
        "snapshot_count": best["snapshot_count"],
        "results": results,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _label(url: str) -> str:
    if "query=" in url:
        return url.split("query=")[-1].replace("+", " ")
    parts = [p for p in url.rstrip("/").split("/") if p]
    return parts[-1] if parts else url


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    FROM_DATE = "20210101"
    TO_DATE   = "20260401"

    PROBE_GROUPS = {
        "content-writing": [
            "https://www.fiverr.com/categories/writing-translation/content-writing",
            "https://www.fiverr.com/categories/writing-translation",
            "https://www.fiverr.com/search/gigs?query=content+writing",
            "https://www.fiverr.com/search/gigs?query=copywriting",
        ],
        "prompt-engineering": [
            "https://www.fiverr.com/search/gigs?query=prompt+engineering",
            "https://www.fiverr.com/search/gigs?query=ai+prompt",
            "https://www.fiverr.com/categories/ai-services",
        ],
    }

    canonical = {}
    all_rows   = []   # for the flat display table

    for group_name, variants in PROBE_GROUPS.items():
        print(f"\nProbing: {group_name}")
        print("-" * 60)
        probe = probe_category_urls(variants, from_date=FROM_DATE, to_date=TO_DATE)

        for r in probe["results"]:
            marker = " <-- winner" if r["url"] == probe["canonical_url"] else ""
            print(f"  {r['snapshot_count']:>4}  {r['url']}{marker}")
            all_rows.append({
                "group":          group_name,
                "url":            r["url"],
                "snapshot_count": r["snapshot_count"],
                "is_canonical":   r["url"] == probe["canonical_url"],
            })

        canonical[group_name] = {
            "canonical_url":  probe["canonical_url"],
            "snapshot_count": probe["snapshot_count"],
        }

    # Print summary table
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    summary_df = pd.DataFrame([
        {"category": k, "canonical_url": v["canonical_url"], "snapshots": v["snapshot_count"]}
        for k, v in canonical.items()
    ])
    print(summary_df.to_string(index=False))

    # Save canonical URLs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "canonical_urls.json"
    out_path.write_text(json.dumps(canonical, indent=2))
    print(f"\nSaved canonical URLs to {out_path}")
