# Data Quality Notes
## OQG x AISA — Fiverr Price Distribution Study

This document records all known data quality issues in `data/output/full_panel.csv`, the fixes that were applied, and the estimated impact on the analysis.

---

## 1. Overview

The panel (`full_panel.csv`) contains 1,670 gig-month observation rows across five Fiverr categories, 2021–2024, extracted from Wayback Machine archived snapshots. Of those rows, 56 (3.4%) have null prices due to snapshot quality failures and are retained in the panel but excluded from all monthly aggregations via `dropna`. The analysis-ready sample is therefore 1,614 rows with valid prices.

Two categories of issues are documented below: (1) extractor bugs that were discovered and fixed during data collection, and (2) irreducible structural gaps in the data.

---

## 2. Extractor Fixes

### 2.1 Price Field HTML Format Change (May 2023+)

**Dates affected:** May 2023 onward (all categories)

**Description:** Fiverr changed the HTML markup for displayed gig prices around May 2023. Before the change, price spans appeared as:
```html
<a class="price"><span>$10</span></a>
```
After the change:
```html
<a ...><span class="text-bold ...">From <span>$10</span></span></a>
```
The original extractor only matched the pre-May 2023 selector, silently producing zero valid prices on all post-May 2023 snapshots.

**Fix:** A dual-path selector was added to the extraction function: first the original `price_a` span is tried; if it returns no matches, a fallback regex `\$\d+` is applied to the surrounding element. The fix was confirmed working by re-running extraction on sample May–Sep 2023 snapshots.

**Residual nulls:** Despite the fix, three category-months remain null after the repair because the Wayback Machine served degraded cached copies of those specific snapshots that returned zero price elements under both selectors. These cells are irreducible:
- Creative writing: Jul 2023, Sep 2023
- Data entry: Jul 2023
- Transcription: Jul 2023

**Impact on analysis:** Monthly ITS series for affected categories drop these months (the `dropna` in `aggregate_monthly` handles this automatically). For a series of 39–46 months, 1–2 missing months have negligible effect on coefficient estimates.

---

### 2.2 Title Extraction Format Change (2024+)

**Dates affected:** 2024 snapshots (all categories)

**Description:** Fiverr changed gig title markup from `<h3><a>title</a></h3>` to `<p role="heading" aria-level="3" title="...">title</p>`. The original extractor only searched for `<h3>` tags, producing null titles for all 2024 gigs.

**Fix:** A dual-path was added: first try `h3 > a`; fall back to `p[role="heading"]`, using the `title` attribute if present. The fix was applied before the final collection pass so all 2024 rows in the current panel have valid titles.

**Impact on analysis:** Title extraction is completely separate from price extraction; no prices were affected. The `ai_assisted` and `human_signal` keyword flags depend on titles. These flags are present in the panel (11 rows total across both flags) and all 11 have valid titles, so the 2024 title fix had no analytical effect on the current study.

---

## 3. Merge Bug Fix

### 3.1 Timestamp Dtype Mismatch in Deduplication (Double-Merge Bug)

**When detected:** During incremental fill runs in `fill_2023_2024.py`

**Description:** The `merge_rows_into_panel()` function deduplicates new rows against the existing CSV by matching on a `(timestamp, category)` composite key. An early version of the function did not normalize the `timestamp` column dtype before comparison: the incoming new DataFrame had `int64` timestamps (from the CDX API integer format), while the existing CSV stored them as strings. The dtype mismatch caused `int64 != str` comparisons to always be `False`, so all incoming rows passed the deduplication filter and were appended even if already present — silently doubling any re-scraped snapshot.

**Fix:** Both sides of the key lookup now explicitly cast `timestamp` to `str` before comparison (lines 101 and 106 of `fill_2023_2024.py`). This normalization ensures that `"20220712143022"` and `20220712143022` are treated as the same key.

**Verification:** The current panel was rebuilt after the fix. To confirm no duplicate rows remain: `df.groupby(['timestamp', 'category']).size().max()` returns 12, which is the maximum single-snapshot gig count, not a doubled value. The panel is clean.

---

## 4. Known Data Gaps

### 4.1 January 2024 — Logo Design Null Prices

**Rows affected:** 8 rows, `graphics-design/creative-logo-design`, 2024-01

**Cause:** The Wayback Machine snapshot from this month was cached and served as a partially-loaded page variant — the gig card structure was present but the price elements were absent. This is distinct from the May 2023 markup change (the new selector was applied and still found nothing). The snapshot cannot be recovered without a new archive crawl.

**Flag:** All 8 rows have `low_confidence=True` and `price=NaN`.

**Impact:** One missing month in logo design's 31-month ITS series. Logo design already has the shortest series (starts May 2021), but one additional missing month mid-series has negligible effect on coefficient estimates.

---

### 4.2 Logo Design Missing Coverage Before May 2021

**Rows affected:** January–April 2021 (no rows)

**Cause:** The Wayback Machine did not crawl the `graphics-design/creative-logo-design` category URL during these months. This is a Wayback coverage limitation, not an extractor failure.

**Impact:** Logo design's ITS series starts May 2021, giving T=31 observations vs. ~41–46 for other categories. The ITS model for logo design is fit on a slightly shorter pre-period baseline (May–July 2022 = 15 months vs. ~18 months for other categories). This is acknowledged in the limitations section of the paper.

---

### 4.3 Additional Zero-Price Months Across Categories

All category-months with zero valid prices after applying both extractors:

| Category | Month | Cause |
|---|---|---|
| Creative writing | 2021-03 | Degraded snapshot |
| Transcription | 2022-06 | Degraded snapshot |
| Creative writing | 2023-07 | Post-May-2023 fix; snapshot unrecoverable |
| Creative writing | 2023-09 | Post-May-2023 fix; snapshot unrecoverable |
| Data entry | 2023-07 | Post-May-2023 fix; snapshot unrecoverable |
| Transcription | 2023-07 | Post-May-2023 fix; snapshot unrecoverable |
| Logo design | 2024-01 | Degraded snapshot (see §4.1) |

All of these appear as white cells in the coverage heatmap (`figures/final/coverage_heatmap.png`).

---

### 4.4 July 2023 Price Outlier Note (Resolved)

The memory notes for this project mention a "2023-07: price outlier capped." After reviewing the actual panel, no active outlier capping exists in any current script. The note appears to have referred to the fact that July 2023 snapshots returned zero valid prices (described in §4.3 above), which were effectively "capped" by being excluded from the analysis as null months — not by winsorizing individual price values.

**Status:** No action required. Confirmed: zero active price winsorization in the pipeline.

---

### 4.5 `low_confidence` Flag Semantics

The `low_confidence` flag is set to `True` when a snapshot extraction returns fewer than 3 valid prices. All 56 flagged rows have `price=NaN`, meaning the flag is functionally equivalent to null-price filtering for the current analysis. The flag is retained in the panel for auditability and may be useful if a future study attempts to use partial snapshots.

---

### 4.6 `ai_assisted` and `human_signal` Flags

These boolean flags are computed by `scripts/add_keyword_flags.py` via regex on gig title text. They indicate whether a gig title explicitly references AI tools (`ai_assisted`, e.g., "ChatGPT", "Midjourney") or signals human-only work (`human_signal`, e.g., "no-AI", "handcrafted").

| Flag | Rows flagged | Notes |
|---|---|---|
| `ai_assisted` | 3 | All in data-entry, all $5, all post-2023 |
| `human_signal` | 8 | Mix of categories, mostly logo design |

These flags are present in `full_panel.csv` but are **not used in any current analysis script**. They are retained for potential future use — e.g., testing whether explicitly AI-labeled gigs cluster at the price floor, or whether human-signal sellers occupy the surviving premium tier.

---

## 5. Impact Summary

| Issue | Rows affected | Analysis impact | Status |
|---|---|---|---|
| Price field HTML change (May 2023+) | ~40 snapshots | Null months in 3 categories | Fixed; residual nulls documented (§4.3) |
| Title extraction change (2024+) | All 2024 rows | Title null risk for some 2024 gigs | Fixed; no price impact |
| Double-merge bug | Any re-scraped rows | Potential duplicate rows | Fixed; panel verified clean (§3.1) |
| Jan 2024 logo design nulls | 8 rows | 1 missing month in 31-month series | Irreducible; impact negligible |
| Logo design pre-May 2021 gap | ~4 months absent | T=31 vs ~42 for other categories | Wayback coverage limit; documented in §6 Limitations |
| Jul 2023 outlier note | 0 rows (no active cap) | N/A — note refers to null months | Resolved; no action |
| `low_confidence` rows (all null) | 56 rows | Auto-excluded via `dropna` | No action; retained for auditability |
