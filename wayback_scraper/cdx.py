"""CDX API querying for Wayback Machine snapshots."""

import time
import requests
from dataclasses import dataclass
from typing import Iterator

CDX_API = "http://web.archive.org/cdx/search/cdx"


@dataclass
class Snapshot:
    timestamp: str  # YYYYMMDDHHmmss
    original_url: str
    status_code: str
    wayback_url: str

    @property
    def year(self) -> int:
        return int(self.timestamp[:4])

    @property
    def month(self) -> int:
        return int(self.timestamp[4:6])


def query_snapshots(
    url_pattern: str,
    from_year: int = 2019,
    to_year: int = 2024,
    limit: int = 500,
    status_filter: str = "200",
    collapse: str = "timestamp:6",  # one per month
) -> list[Snapshot]:
    """Fetch CDX index records for a URL pattern across a date range."""
    params = {
        "url": url_pattern,
        "output": "json",
        "fl": "timestamp,original,statuscode",
        "from": f"{from_year}0101",
        "to": f"{to_year}1231",
        "limit": limit,
        "filter": f"statuscode:{status_filter}",
        "collapse": collapse,
    }
    resp = requests.get(CDX_API, params=params, timeout=30)
    resp.raise_for_status()

    rows = resp.json()
    if not rows:
        return []

    # First row is the field header when output=json
    fields, *records = rows
    snapshots = []
    for row in records:
        record = dict(zip(fields, row))
        ts = record["timestamp"]
        orig = record["original"]
        sc = record["statuscode"]
        wb_url = f"https://web.archive.org/web/{ts}/{orig}"
        snapshots.append(Snapshot(ts, orig, sc, wb_url))
    return snapshots


def iter_category_snapshots(
    categories: list[str],
    from_year: int = 2019,
    to_year: int = 2024,
    limit_per_category: int = 100,
    sleep: float = 1.0,
) -> Iterator[tuple[str, Snapshot]]:
    """Yield (category, Snapshot) for each category URL pattern."""
    for category in categories:
        url_pattern = f"fiverr.com/categories/{category}*"
        snapshots = query_snapshots(
            url_pattern,
            from_year=from_year,
            to_year=to_year,
            limit=limit_per_category,
        )
        for snap in snapshots:
            yield category, snap
        time.sleep(sleep)
