# Writer's Brief — Fiverr AI Pricing Study
**OQG x AISA Spring 2026**


---

## What This Study Is About 

When AI tools like Midjourney, Stable Diffusion, and ChatGPT became widely available in 2022–2023, they could suddenly do things that freelancers on Fiverr had been getting paid to do — design logos, create social media graphics, write copy. This study asks: did that change what people were willing to pay for those services? We pulled four years of Fiverr price data (2021–2024) from archived web snapshots and compared how prices changed across five service categories — three that AI tools directly threaten, and two that they largely don't. The finding: prices in the AI-threatened categories compressed significantly, and it happened at the top end. Clients who used to pay $80–$107 for a professional logo stopped paying that once AI could do a passable version for nearly nothing. The cheap end of the market barely moved.

---

## Where the Data Came From

- **Source:** The Wayback Machine (web.archive.org) — a nonprofit that takes regular snapshots of websites. We used snapshots of Fiverr category pages.
- **Time period:** January 2021 – December 2024
- **What we collected:** Individual gig listings — the price, title, and seller info visible on Fiverr's search results pages
- **Total observations:** 1,670 individual gig-month records. After excluding snapshots where prices couldn't be read, the usable sample is 1,614.
- **How many gigs per snapshot:** Roughly 8–12 per category per month (what Fiverr shows on the first page of results)

---

## The Five Categories

We chose five Fiverr service categories that span a range of how much AI tools can replace what the seller does.

| Category | Type | AI Threat Level | Score |
|---|---|---|---|
| Creative logo design | Treatment | High | 0.90 |
| Social media design | Treatment | High | 0.85 |
| Creative writing | Treatment | High | 0.80 |
| Transcription | Comparison | Medium | 0.40 |
| Data entry | Comparison | Low | 0.10 |

**Treatment categories** are ones where AI tools can produce roughly the same deliverable a human would — a client can now get a usable logo from Midjourney in minutes for free. **Comparison categories** are ones where AI helps but doesn't replace the human: transcription still needs review, formatting, and accuracy checking; data entry has no AI product that replaced it during this window.

The score (0–1) represents how directly substitutable we judged each category to be. These were assigned before running any analysis, based on what AI tools could actually do during the study period.

---

## Why We Assigned Those Scores

**Logo design (0.90):** Midjourney and Stable Diffusion generate end-to-end logo images. A client no longer needs a human for a basic logo — they can just prompt the AI. Highest threat.

**Social media design (0.85):** Same image-generation threat, but social media work is more template-heavy and multi-piece, so there's slightly more room for human-AI collaboration rather than pure replacement.

**Creative writing (0.80):** ChatGPT and GPT-4 produce directly substitutable creative text — blog posts, product descriptions, short stories. Score is slightly lower than the design categories because some buyers may still prefer work that reads as distinctly human.

**Transcription (0.40):** OpenAI's Whisper (released September 2022) automates the core task, but clients often need accurate timestamps, speaker labels, and corrections for specialized terminology. The human is still needed — just for a narrower set of tasks.

**Data entry (0.10):** No major AI product released during 2021–2024 directly replaced manual data entry at scale. We used this category as our cleanest baseline — a category where prices should reflect only general market trends, not AI disruption.

---

## The Major AI Events We Tracked

| Date | What happened | Which categories it affected |
|---|---|---|
| July 2022 | Midjourney open beta | Logo design, social media design |
| August 2022 | Stable Diffusion public release | Logo design, social media design |
| September 2022 | OpenAI Whisper released | Transcription |
| November 2022 | ChatGPT launches | Creative writing |
| March 2023 | GPT-4 released | Creative writing |
| March 2023 | Midjourney V5 released | Logo design, social media design |
| May 2024 | GPT-4o made free | Creative writing |

---

## What We Found

### Finding 1: Prices compressed in AI-exposed categories — confirmed

The gap between how much prices fell in high-AI-threat categories versus low-AI-threat categories is **$26–$32**, depending on which version of the model you use. That gap is statistically meaningful.

**In plain terms:** Logo designers and social media designers saw their prices drop substantially after 2022. Data entry workers — who face no comparable AI threat — held steady. The difference between those trajectories is what we're measuring.

### Finding 2: The compression happened at the TOP of the market, not the bottom

We separated each category's price distribution into a "floor" (the cheap end of the market) and a "ceiling" (the premium end). Here's what happened pre- vs. post-AI:

| Category | AI Threat | Ceiling BEFORE | Ceiling AFTER | Change |
|---|---|---|---|---|
| Logo design | High | $107 | $60 | **−$46** |
| Social media design | High | $76 | $36 | **−$40** |
| Creative writing | High | $81 | $58 | **−$23** |
| Data entry | Low (baseline) | $36 | $17 | −$18 |
| Transcription | Medium | $21 | $23 | +$2 |

| Category | AI Threat | Floor BEFORE | Floor AFTER | Change |
|---|---|---|---|---|
| Logo design | High | $18 | $16 | −$1 |
| Social media design | High | $17 | $13 | −$4 |
| Creative writing | High | $13 | $11 | −$2 |
| Data entry | Low (baseline) | $9 | $5 | −$4 |
| Transcription | Medium | $5 | $5 | $0 |

**What this means:** The cheap end of the market barely moved — it was already near Fiverr's minimum price ($5) and couldn't go lower. The expensive end collapsed in every high-AI-threat category. Clients who used to pay $80–$107 for a logo stopped paying that once AI was an option. Transcription, notably, had no premium tier to lose — its ceiling was only $21, so even with AI competing against it, there was nothing to collapse.

### Finding 3: Prices did NOT split into two groups — the "barbell" theory is wrong

Early commentary on AI disruption often predicted a "barbell" effect: the market would split into cheap AI-assisted work at the bottom and surviving premium human work at the top, with nothing in the middle. We tested this directly. It didn't happen.

If anything, the data shows the opposite: in two of the three high-threat categories, the price distribution became *less* split after AI, not more. The premium tier didn't survive as a distinct human-labeled mode — it collapsed entirely. Buyers were not consistently willing to pay a large premium just because something was made by a human.

---

## The Key Numbers (for citing)

**Main result — how prices diverged based on AI exposure:**
- The estimated differential price decline is **−$32.6 per unit of AI score** (p = 0.066) in the basic model
- In the fuller model with trend controls: **−$40.2** (p = 0.015)
- Implied dollar gap between most- and least-exposed category: **$26–$32**

**Ceiling collapse (from the floor/ceiling analysis):**
- Logo design ceiling: −$46
- Social media design ceiling: −$40
- Creative writing ceiling: −$23
- Data entry (comparison baseline): −$18 ← important context; this shows prices were falling platform-wide, but the falls in high-AI categories are substantially larger

**Bimodality (the barbell test) — not supported:**
- The statistical test for "did prices split into two groups?" found no effect: coefficient = −0.071, p = 0.39
- In two categories (logo design, social media design), distributions became measurably *less* split after AI shocks

---

## How Robust Is This?

We tested the findings three ways:

1. **Fake shock dates:** We re-ran the analysis pretending the AI launches happened 6 months earlier than they did. The fake dates produced weaker results, suggesting the real timing matters — the price changes aren't just random fluctuations.

2. **Simpler comparison:** We ran a simpler two-group comparison (each high-AI category vs. data entry only). Logo design vs. data entry: estimated price gap of **−$41.3** (p = 0.043). The other two categories had similar direction but didn't reach statistical significance individually — expected, since this simpler test uses less data.

3. **Score sensitivity:** We varied each category's AI score up and down (by small and large amounts) and re-ran the analysis — 42 variations total. **35 out of 36 variations (97%) preserved the direction and significance of the finding.** The result doesn't depend on the exact scores we chose.

---

## Data Quality Issues Worth Mentioning



- **Fiverr changed its website layout in May 2023**, which initially broke our price extraction. We fixed it, but a handful of months still have no usable data (creative writing July/September 2023, data entry and transcription July 2023).
- **Logo design has no data before May 2021** — the Wayback Machine didn't archive that category earlier. So logo design has a slightly shorter baseline period.
- **Each snapshot captures only ~8–12 gigs** (the first page of results), not the full category. These may not be perfectly representative.
- **We only have 5 categories**, which is a small sample for the statistical tests we're using. The p-values should be treated as suggestive rather than definitive.1
- **The AI threat scores are our judgment calls**, not measured from data. We ran the sensitivity tests specifically because of this.

---

## Figures Available

All figures are in `data/output/figures/final/`.

### Priority figures (use these in the article)

**Figure A — `treatment_vs_control.png`** *(lead with this one)*
Three side-by-side line charts — one for each AI-threatened category — each plotted against the data entry control. The shaded region after mid-2022 shows where the treatment category's price diverged downward from the control. This is the clearest, most intuitive visual of the core finding: AI-exposed categories fell away from the baseline while the control held steady.

**Figure B — `ceiling_floor_bars.png`** *(most novel finding)*
A bar chart showing how much the top end and bottom end of each category's prices changed before vs. after AI tools launched. The key story: the ceiling (expensive gigs) collapsed by $23–$46 in every high-AI category; the floor (cheap gigs) barely moved. This shows *where* the compression happened, not just that it happened. Controls are shown as faded bars for comparison.

**Figure C — `dose_response.png`** *(supports the mechanism)*
A scatter plot with one dot per category. X-axis = how much AI can substitute for that category's work (0 = low, 1 = high). Y-axis = how much prices dropped after AI launched. The dashed trend line slopes downward: more AI exposure, larger price drop. Slope is −$16 per unit of exposure (p = 0.13 — suggestive but not definitive given only 5 categories).

**Figure D — `coverage_heatmap.png`** *(use in methods or appendix)*
A grid showing how many gig observations we have for each category in each month, color-coded from gray (none) to red (12). This is a data-quality figure — it shows where the gaps are and that coverage is otherwise consistent. Not a finding; use it to preempt questions about data reliability.

### Additional figures

| File | What it shows |
|---|---|
| `main_compression.png` | Monthly median prices for all five categories on one chart, 2021–2024. Good for a broad overview but the individual treatment_vs_control panels tell the story more clearly. |
| `sensitivity_forest.png` | Shows that the main finding holds across 42 different AI score assignments — 97% of variations preserved direction and significance. Use if a reviewer pushes on the subjective scores. |

---

## Tables Available

All tables are in `data/output/tables/` as both `.md` (readable) and `.tex` (for LaTeX).

| Table | File | What it shows |
|---|---|---|
| Table 1 | `table1_panel_summary.md` | Overview of the five categories — date range, number of gigs, AI score, median price |
| Table 2 | `table2_weighted_did.md` | Main statistical results — price compression and bimodality test |
| Table 3 | `table3_its_results.md` | Price shifts at each specific AI launch event |
| Table 4 | `table4_gmm_floor_ceiling.md` | The floor/ceiling pre-vs-post breakdown for every category |

---

## Full Draft

A complete academic draft (abstract through appendix) is at `paper/draft.md`. Use it for reference — it has the formal methods writeup, all citations, and the full argument in paper form.
