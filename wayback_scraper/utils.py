"""Shared helpers: logging, I/O, rate limiting."""

import csv
import logging
import time
from pathlib import Path
from typing import Iterable

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def save_csv(rows: Iterable[dict], path: Path, append: bool = False) -> int:
    """Write dicts to CSV, returning number of rows written."""
    rows = list(rows)
    if not rows:
        return 0
    mode = "a" if append else "w"
    fieldnames = list(rows[0].keys())
    write_header = not (append and path.exists())
    with open(path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)
    return len(rows)


class RateLimiter:
    """Token-bucket rate limiter for polite crawling."""

    def __init__(self, calls_per_second: float = 1.0):
        self._interval = 1.0 / calls_per_second
        self._last = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last
        deficit = self._interval - elapsed
        if deficit > 0:
            time.sleep(deficit)
        self._last = time.monotonic()


def output_path(name: str) -> Path:
    """Return a path in data/output/ for a given filename."""
    return OUTPUT_DIR / name
