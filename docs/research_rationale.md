# Research Design Rationale
## OQG x AISA — Fiverr Price Distribution Study

---

## 1. Why These Four Categories?

The study is a quasi-experiment: we want to see whether the arrival of generative AI tools caused measurable shifts in price distributions on Fiverr. To do that cleanly, we need **treatment categories** (services that AI can plausibly replace or commoditize) and a **control category** (a service that AI did not meaningfully threaten during the study window).

The final panel contains four categories: three treatment, one control.

### Treatment Categories (3)

| Category | AI Threat | Key Events |
|---|---|---|
| `graphics-design/creative-logo-design` | Image generation AI | Midjourney open beta: Jul 2022; Stable Diffusion: Aug 2022; Midjourney V5: Mar 2023 |
| `graphics-design/social-media-design` | Image generation AI | Same as above |
| `content-writing/creative-writing` | Text LLMs | ChatGPT launch: Nov 2022; GPT-4: Mar 2023; GPT-4o free to all: May 2024 |

These three categories represent the **two dominant generative AI disruption vectors** identified in the literature and by AISA:

- **Image generation** tools (Midjourney, Stable Diffusion, DALL-E) directly enable people to produce logo designs and social media graphics without hiring a human designer. Logo design and social media design were among the first professional subcategories cited in reporting on AI disruption of creative work.
- **Text LLMs** (primarily ChatGPT) directly compete with freelance writers for creative copy, stories, and marketing text.

Having two graphics-design subcategories (logo design and social media design) instead of one is intentional: it lets us check whether the disruption effect is consistent within the same parent category, which is a validity test. If both move similarly after image gen AI launches, that strengthens the causal interpretation. If they diverge, it signals something category-specific rather than a platform-wide effect.

### Control Category (1): `data/data-entry`

Data entry is mechanical, high-volume, rule-governed work — transcribing text, filling spreadsheets, cleaning records. Generative AI (as of 2021–2024) does not meaningfully perform this task in the way that end clients on Fiverr buy it. There was no major AI product launch during the study window that commoditized data entry the way ChatGPT commoditized creative writing or Midjourney commoditized logo design.

This makes data-entry the closest available **counterfactual**: a category on the same platform, priced in the same currency, bought by similar clients, but not exposed to the AI disruption signal we are studying. If prices in data-entry move similarly to treatment categories after AI launches, the causal story weakens. If they diverge, it strengthens it.

The median price data already hints at this divergence — creative writing and logo design medians dropped after 2022, while data-entry stayed flatter — which is exactly what the quasi-experimental design predicts.

---

## 2. Why Not the Other Categories That Were Originally Proposed?

Several other subcategories were identified during the feasibility phase as candidates. They were excluded for a combination of research-design and technical reasons.

### Excluded for Zero Wayback Machine Coverage (Technical)

Some originally proposed categories had **no usable archived snapshots** at all. The Internet Archive simply had not crawled those Fiverr URLs on a regular basis:

- **`web-development` / landing pages** — the canonical Fiverr URL for this category returned zero or near-zero CDX results for 2021–2024. Without archived pages, there is nothing to extract.
- **`prompt-engineering` / AI services** — this subcategory did not exist on Fiverr until after 2022, so there is no pre-disruption baseline. The CDX probe also confirmed sparse coverage even for 2023–2024.

This was a hard blocker, not a design choice. Any category with fewer than roughly 24 monthly snapshots across the study window (two per quarter) was not viable for a trend analysis.

### Excluded for Research-Design Reasons

**More graphics-design subcategories** *(digital-illustration, flyer-design, poster-design, etc.)*
Adding more subcategories within the same treatment arm (image generation AI) replicates the same signal without adding a new dimension. We already have two image-generation-exposed categories. A third would make the dataset larger but not more interpretable. `digital-illustration` was flagged as a potential inclusion because illustration is a distinct task from logo design, but scope constraints led to keeping the panel at four categories.

**More writing subcategories** *(articles-blogposts, sales-copy, proofreading-editing)*
`articles-blogposts` was a serious candidate — it is the highest-volume writing subcategory on Fiverr. It was deprioritized because creative writing has a tighter connection to the "AI can generate this" narrative. A client can prompt ChatGPT for a short story more directly than they can for a 3,000-word SEO article requiring specific research and sourcing.

`proofreading-editing` was specifically excluded because it is plausibly *complementary* to AI rather than threatened by it — sellers increasingly use AI drafts and sell the editing step. Including it as a treatment category would be conceptually incorrect given our hypothesis.

**`ai-services`** — this Fiverr category did not exist until after 2022. It has no pre-AI baseline and measures a completely different phenomenon (selling AI-assisted services rather than human services in a market disrupted by AI).

---

## 3. Why Did We Stop at 2024? And Could We Do 2025?

### Why 2024 Was the Cutoff

The study window of **2021–2024** was chosen to bracket the disruption cleanly:

- **2021–mid 2022:** Pre-generative-AI baseline. Midjourney and ChatGPT did not yet exist. This gives 12–18 months of "normal" market behavior to anchor the analysis.
- **Mid-2022:** Image generation AI arrives (Midjourney beta, Stable Diffusion). First potential disruption signal for graphics categories.
- **Late 2022–2023:** Text LLM disruption (ChatGPT launch November 2022, GPT-4 March 2023). Both treatment arms are now exposed.
- **2023–2024:** Post-disruption measurement window.

Ending at December 2024 gives roughly **two years of post-disruption data** against two years of pre-disruption baseline — a balanced window that is sufficient to detect a trend without conflating the initial disruption with subsequent market adaptations.

### Could We Do 2025? Yes — With Caveats

Technically, yes. The Wayback Machine has been archiving Fiverr through 2025 and into 2026. A small number of 2025 snapshots were cached during earlier probes:

- `20251104122505_graphics-design_social-media-design.html` — November 2025
- `20250201194107_probe_ai-services.html` — February 2025

The CDX API returns valid monthly snapshots for the panel categories through at least late 2025, and the price extractor works on them (the HTML markup Fiverr uses has been stable since the May 2023 change fixed during this project). To extend to 2025, one line in `scripts/fill_2023_2024.py` changes:

```python
TO_DATE = "20251231"   # was "20241231"
```

**Why it is a different research question, not just more data:**

By 2025, the market has had 2–3 years to adapt to generative AI. Price changes in 2025 may reflect seller pivots, new buyer segments, platform policy changes, or stabilization — not the original disruption shock. Mixing this into the current dataset requires reframing the research question from *"did AI disrupt prices?"* to *"how did the market adapt after AI disruption?"* That is worth studying, but it is a follow-up study, not an extension of this one.

**Additional caveats:**

1. Months close to the current date have fewer Wayback snapshots (the archive hasn't had as much time to crawl them repeatedly), so monthly coverage may be thinner and less reliable for 2025.
2. Fiverr deploys frontend updates regularly. The extractor has already needed one fix during this project (May 2023 markup change). A 2025 extension would require re-validating that the price selectors still work across the new snapshots before trusting the data.

---

## Summary

| Decision | Choice | Key Reason |
|---|---|---|
| Treatment arm 1 | logo design + social media design | Both exposed to image gen AI; two subcategories allow within-arm consistency check |
| Treatment arm 2 | creative writing | Directly exposed to text LLMs; tight buyer intent |
| Control | data-entry | Mechanical task; no AI product threatened it during study window |
| Excluded: web development, prompt engineering | Zero Wayback coverage | No archived snapshots; hard technical blocker |
| Excluded: more graphics subcategories | Replication of existing signal | Would not add a new treatment dimension |
| Excluded: articles-blogposts | Deprioritized | Valid candidate; creative writing has tighter AI narrative connection |
| Excluded: proofreading-editing | Conceptually wrong | Likely complementary to AI, not threatened; wrong treatment assumption |
| Excluded: ai-services | No baseline | Category didn't exist pre-2022; measures a different phenomenon |
| End date: 2024 | Deliberate scope | Balanced pre/post window around disruption; 2025 is a market-adaptation question |
| 2025 feasibility | Yes, technically | Data and extractor work; requires reframing the research question |
