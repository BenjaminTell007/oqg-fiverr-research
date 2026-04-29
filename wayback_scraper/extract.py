"""Parse gig price and metadata from Fiverr HTML snapshots."""

import re
from dataclasses import dataclass, field, asdict
from bs4 import BeautifulSoup


@dataclass
class Gig:
    title: str = ""
    seller: str = ""
    price_usd: float | None = None   # starting price shown on listing card
    rating: float | None = None
    review_count: int | None = None
    seller_level: str = ""
    category: str = ""
    snapshot_timestamp: str = ""
    wayback_url: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# --- Price extraction helpers ---

_PRICE_RE = re.compile(r"\$[\s]?([\d,]+(?:\.\d{1,2})?)")


def parse_price(text: str) -> float | None:
    m = _PRICE_RE.search(text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def parse_rating(text: str) -> float | None:
    try:
        return float(text.strip())
    except ValueError:
        return None


def parse_review_count(text: str) -> int | None:
    # handles "(1.2k)", "(850)", etc.
    cleaned = text.strip().strip("()")
    if cleaned.endswith("k"):
        try:
            return int(float(cleaned[:-1]) * 1000)
        except ValueError:
            return None
    try:
        return int(cleaned.replace(",", ""))
    except ValueError:
        return None


# --- Main extraction entry point ---

def extract_gigs(
    html: str,
    category: str = "",
    snapshot_timestamp: str = "",
    wayback_url: str = "",
) -> list[Gig]:
    """
    Extract gig cards from a Fiverr category page snapshot.

    Fiverr's markup changed several times between 2019-2024, so we attempt
    multiple selector strategies and return whichever yields results.
    """
    soup = BeautifulSoup(html, "html.parser")
    gigs: list[Gig] = []

    # Strategy 1: post-2022 React-rendered cards
    cards = soup.select("[class*='gig-card']")
    if not cards:
        # Strategy 2: older server-rendered listings
        cards = soup.select(".gig-item, .gig-wrapper, li[data-impression-collected]")
    if not cards:
        # Strategy 3: generic product-card fallback
        cards = soup.select("[data-testid*='gig'], article")

    for card in cards:
        gig = Gig(
            category=category,
            snapshot_timestamp=snapshot_timestamp,
            wayback_url=wayback_url,
        )

        title_el = card.select_one("[class*='title'], h3, [itemprop='name']")
        if title_el:
            gig.title = title_el.get_text(strip=True)

        seller_el = card.select_one("[class*='seller'], [class*='username']")
        if seller_el:
            gig.seller = seller_el.get_text(strip=True)

        price_el = card.select_one("[class*='price'], [data-testid*='price']")
        if price_el:
            gig.price_usd = parse_price(price_el.get_text())

        rating_el = card.select_one("[class*='rating-score'], [class*='stars']")
        if rating_el:
            gig.rating = parse_rating(rating_el.get_text())

        reviews_el = card.select_one("[class*='reviews-count'], [class*='rating-count']")
        if reviews_el:
            gig.review_count = parse_review_count(reviews_el.get_text())

        level_el = card.select_one("[class*='seller-level'], [class*='level-badge']")
        if level_el:
            gig.seller_level = level_el.get_text(strip=True)

        if gig.title or gig.price_usd is not None:
            gigs.append(gig)

    return gigs
