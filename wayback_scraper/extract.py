"""Parse gig price and metadata from Fiverr HTML snapshots."""

import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup

SNAPSHOTS_DIR = Path(__file__).parent.parent / "data" / "snapshots"
OUTPUT_DIR    = Path(__file__).parent.parent / "data" / "output"


def extract_gigs(html: str, timestamp: str, category: str) -> list[dict]:
    """
    Extract gig data from a Fiverr subcategory listing snapshot.

    Confirmed selectors (verified against Wayback HTML, 2022-2024 era):
      Card root : <div class="gig-card-layout">
      Price     : <a class="price"> → first <span> child  e.g. "$10"
      Title     : <h3> → <a> child text
      Seller    : <div class="seller-name"> → <a> child text
      Tier      : <span class="level …"> text  e.g. "Level 2 Seller"
      Rating    : <span class="gig-rating …"> first text node
      Reviews   : <span> inside gig-rating parens

    Returns one dict per card; low_confidence=True when fewer than 3 prices found.
    """
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("div", class_="gig-card-layout")

    rows = []
    for card in cards:
        # Price — two formats seen in the wild:
        #   Pre-May 2023: <a class="price"><span>$10</span></a>
        #   May 2023+:    <a ...><span class="text-bold ...">From <span>$10</span></span></a>
        import re as _re
        price = None
        price_a = card.find("a", class_="price")
        if price_a:
            span = price_a.find("span")
            if span:
                raw = span.get_text(strip=True).lstrip("$").replace(",", "")
                try:
                    price = float(raw)
                except ValueError:
                    pass
        if price is None:
            # Fallback: find any <span> whose sole text looks like "$NNN"
            for span in card.find_all("span"):
                txt = span.get_text(strip=True)
                m = _re.fullmatch(r"\$(\d[\d,]*(?:\.\d+)?)", txt)
                if m:
                    try:
                        price = float(m.group(1).replace(",", ""))
                        break
                    except ValueError:
                        pass

        # Title — two formats:
        #   Pre-2024: <h3><a>title</a></h3>
        #   2024+:    <p role="heading" aria-level="3" title="...">title</p>
        title = None
        h3 = card.find("h3")
        if h3:
            a = h3.find("a")
            title = (a or h3).get_text(strip=True) or None
        if not title:
            p = card.find("p", attrs={"role": "heading"})
            if p:
                title = p.get("title") or p.get_text(strip=True) or None

        # Seller: <div class="seller-name"> > <a>
        seller = None
        seller_div = card.find("div", class_="seller-name")
        if seller_div:
            a = seller_div.find("a")
            seller = (a or seller_div).get_text(strip=True) or None

        # Tier: first <span> whose class list contains "level"
        tier = None
        tier_span = card.find("span", class_=lambda c: c and "level" in c)
        if tier_span:
            tier = tier_span.get_text(strip=True) or None

        # Rating + review count: <span class="gig-rating …">
        rating, reviews = None, None
        rating_span = card.find("span", class_="gig-rating")
        if not rating_span:
            rating_span = card.find("span", class_=lambda c: c and "gig-rating" in c)
        if rating_span:
            texts = [t.strip() for t in rating_span.find_all(string=True) if t.strip()]
            for t in texts:
                try:
                    v = float(t)
                    if 1.0 <= v <= 5.0:
                        rating = v
                except ValueError:
                    pass
            paren = rating_span.get_text()
            import re
            m = re.search(r'\(([0-9,k]+)\)', paren)
            if m:
                raw_r = m.group(1).replace(",", "")
                if raw_r.endswith("k"):
                    reviews = int(float(raw_r[:-1]) * 1000)
                else:
                    try:
                        reviews = int(raw_r)
                    except ValueError:
                        pass

        if price is not None or title:
            rows.append({
                "timestamp":      timestamp,
                "category":       category,
                "price":          price,
                "title":          title,
                "seller":         seller,
                "tier":           tier,
                "rating":         rating,
                "reviews":        reviews,
                "low_confidence": False,
            })

    low_confidence = sum(1 for r in rows if r["price"] is not None) < 3
    for r in rows:
        r["low_confidence"] = low_confidence

    if not rows:
        rows.append({
            "timestamp": timestamp, "category": category,
            "price": None, "title": None, "seller": None,
            "tier": None, "rating": None, "reviews": None,
            "low_confidence": True,
        })

    return rows


# ---------------------------------------------------------------------------
# Test block
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cached = sorted(SNAPSHOTS_DIR.glob("*.html"))
    if not cached:
        print("No cached HTML files found in data/snapshots/. Run scraper.py first.")
        raise SystemExit(1)

    print(f"Found {len(cached)} cached snapshot(s)\n")

    all_rows = []
    for path in cached:
        # Filename format: {timestamp}_{category}.html
        stem = path.stem
        underscore = stem.index("_")
        timestamp = stem[:underscore]
        category  = stem[underscore + 1:].replace("_", "-")

        html = path.read_text(encoding="utf-8")
        rows = extract_gigs(html, timestamp=timestamp, category=category)
        all_rows.extend(rows)
        flag = " [LOW CONFIDENCE]" if (rows and rows[0]["low_confidence"]) else ""
        n_prices = sum(1 for r in rows if r["price"] is not None)
        print(f"  {timestamp}  {category:<22}  {len(rows):>5} rows  "
              f"{n_prices} prices{flag}")

    # Save full results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(all_rows)
    out_path = OUTPUT_DIR / "extraction_test.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved {len(df)} rows to {out_path}")

    # Summary: per category and year
    df = df[df["price"].notna()].copy()
    if df.empty:
        print("\nNo prices extracted — cannot build summary.")
        raise SystemExit(0)

    df["year"] = df["timestamp"].astype(str).str[:4]
    summary = (
        df.groupby(["category", "year"])
        .agg(
            gigs_extracted=("price", "count"),
            pct_low_confidence=("low_confidence", lambda x: f"{x.mean()*100:.0f}%"),
            min_price=("price", "min"),
            max_price=("price", "max"),
            median_price=("price", "median"),
        )
        .reset_index()
    )

    print("\n" + "=" * 75)
    print(f"{'category':<22} {'year'}  {'gigs':>5}  {'low_conf':>8}  "
          f"{'min':>6}  {'max':>7}  {'median':>7}")
    print("=" * 75)
    for _, r in summary.iterrows():
        print(f"  {r['category']:<20} {r['year']}  {r['gigs_extracted']:>5}  "
              f"{r['pct_low_confidence']:>8}  "
              f"${r['min_price']:>5.0f}  ${r['max_price']:>6.0f}  ${r['median_price']:>6.0f}")
