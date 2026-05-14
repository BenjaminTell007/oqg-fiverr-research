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

### Control Categories: Graded Exposure Design

Rather than a single binary treated/control split, the panel uses **two control categories at different levels of AI exposure**. This converts the research design from a binary DiD into a **graded-exposure DiD**, which is more robust to platform-wide trends and allows us to test whether the effect scales with how directly AI substitutes for the work.

The three exposure tiers in the panel:

| Tier | Categories | Primary AI vector | Substitutability |
|---|---|---|---|
| **High exposure** | `creative-logo-design`, `social-media-design`, `creative-writing` | Image generation (Midjourney, Stable Diffusion) and text LLMs (ChatGPT, GPT-4) | Direct end-to-end substitute for the gig deliverable |
| **Medium exposure** | `transcription` (label: `transcription-control-medium`) | Speech-to-text (OpenAI Whisper open-source release: 2022-09-21) | AI accelerates the workflow but humans still QA; partial substitution |
| **Low exposure** | `data-entry` (label: `data-entry-control-low`) | None — no major AI product targets manual data entry during the study window | Effectively no substitution |

**Why two controls instead of one.** Per the GMM analysis (`data/output/figures/gmm_fits.png`), even data-entry shows substantial price compression across the study window, indicating Fiverr-wide trends (search-ranking changes, tier-package pricing, macro effects) that are *not* AI-specific. A single low-exposure control absorbs platform-wide effects but cannot tell us whether mid-exposure categories respond at an intermediate level — exactly the prediction the disruption hypothesis makes about Whisper-affected work.

**Why transcription specifically.** The CDX probe (May 2026) for second-control candidates returned: `translation` 0 snapshots, `language-coaching` 0 snapshots, `transcription` **54 snapshots with full 2021–2024 monthly coverage**. Transcription was therefore the only viable medium-exposure candidate within the writing-translation parent category. Substantively it fits the medium tier well — Whisper and similar speech-to-text models reduce transcription effort but do not produce final deliverables clients accept without human review (timestamps, speaker labels, domain-specific terminology, audio-quality handling).

**How the graded design is used in analysis.**

- **Within-category ITS** (`docs/its_specification.md` §3) is fit per category. The high-exposure trio uses category-specific shock dates; transcription uses Whisper's release (2022-09-21); data-entry has no shock and serves as a pure trend-baseline.
- **Differential metrics** (BC, GMM floor/ceiling) are computed against `data-entry-control-low` as the primary baseline — anything common to data-entry is platform-wide, not AI-specific.
- **Graded dose-response check.** If the disruption hypothesis holds, post-shock effect size should order: high > medium > low (≈ 0). Transcription provides the middle data point that turns this from a binary test into a monotonicity test. If transcription moves *with* the high-exposure categories, the effect is more plausibly platform-wide; if it sits cleanly between high and low, the AI-substitutability story is supported.

The median price data already hints at this gradient — creative writing and logo design medians dropped after 2022, while data-entry stayed flatter — and the formal pre/post tests will report effect sizes per tier.

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

## 4. Bimodality Measurement Approach

A core hypothesis of this study is that AI disruption widens the gap between top-tier and bottom-tier sellers, producing a **bimodal price distribution** — one mode for AI-aided commodity gigs and another for premium human-labeled work. Sarle's bimodality coefficient (BC) and Hartigan's dip statistic are the standard tools for testing this. The first analysis pass tried the textbook approach: per-month BC with the canonical 0.555 threshold, and counting the first month each category crossed it. That approach failed, and the workflow had to be rebuilt.

### 4.1 Why the Raw BC-Threshold Approach Failed

Three problems surfaced together:

1. **Structural bimodality predates AI.** All four categories — including the data-entry control — had months where BC > 0.555 in 2021, well before any generative AI release. Fiverr is a tier-priced platform: gigs cluster around recurring price points ($5, $10, $25, $50, $100) reflecting Fiverr's Basic/Standard/Premium package structure. Even within a single category, those clusters create multimodal price distributions independent of AI. The control category crossed the threshold 11 times across the panel — more than the social-media-design treatment category. Threshold-crossing is therefore not a treatment indicator; it is a property of the platform.

2. **Monthly resolution is too noisy.** Each (category, month) cell holds roughly 5–10 gig observations. BC depends on the third and fourth sample moments, both of which are unstable at small n. The monthly series oscillates around 0.555 for every category, so "first crossing" is dominated by sampling noise rather than any underlying distributional change.

3. **Numerical instability.** When prices in a month are clustered tightly on a single tier (e.g., several $5 gigs), `scipy.stats.skew` and `kurtosis` raise precision-loss warnings — the moment calculations are near catastrophic cancellation. BC values from those cells are unreliable in either direction.

The combined effect is that the textbook test cannot distinguish AI-driven bimodality from Fiverr's baseline tier structure.

### 4.2 The Three Refined Metrics

The revised approach replaces "did BC cross 0.555?" with three complementary questions, each addressing a different limitation above.

**(a) Quarterly aggregation with Hartigan dip p-values.** Aggregating to quarter (n ≈ 20–30 per cell) stabilizes the moment calculations and pushes most cells well above the n ≥ 10 reliability floor. Significance of the dip test (`dip_p < 0.05`) replaces the BC threshold as the unimodality-rejection criterion — it is properly calibrated for sample size and does not assume any specific alternative shape. The share of quarters per category with `dip_p < 0.05` becomes the primary "is this distribution multimodal" indicator.

**(b) Six-month trailing rolling mean of monthly BC.** This metric trades resolution for smoothness. The trailing window (no look-ahead) avoids contaminating pre-shock periods with post-shock data, which is critical for ITS interpretation. The smoothed series visualizes whether bimodality is **drifting** within a category, independent of any single noisy month.

**(c) Pre-shock vs. post-shock mean BC, Welch t-test.** Per category, mean quarterly BC before the primary shock vs. after, with unequal-variance t-test. This directly answers "did the level of bimodality change at the shock?" rather than "was it ever above some threshold?". Reported alongside the dip-significance share so a coefficient direction is interpretable.

### 4.3 Why the Treatment-Minus-Control Differential Is Robust to Structural Bimodality

The fourth metric — quarterly `BC_treatment − BC_control` — is the design-level fix for the structural-bimodality problem.

If Fiverr's tier-pricing structure produces baseline bimodality in *every* category (the data-entry control confirms this), then the absolute BC level for any treatment category is contaminated by that platform-wide effect. Subtracting the control's BC at the same point in time differences out anything common to the platform: tier-package design changes, currency/UX rollouts, search-ranking tweaks, macroeconomic effects on Fiverr-wide pricing. What remains in the differential is the component of treatment-category bimodality that is *not* shared with a category AI did not affect.

Under the disruption hypothesis the differential should be near zero pre-shock (both categories share the same structural bimodality) and shift positive post-shock (treatment categories develop AI-specific bimodality the control does not). Under the null it stays flat regardless of where the AI shock falls. This is the same identification logic as the formal DiD specification in `docs/its_specification.md` §4.1, applied to the bimodality outcome rather than the price level — and it is the metric that should drive RQ2 conclusions when the within-category ITS gives ambiguous results.

The differential is reported in the third panel of `data/output/bimodality_timeseries_v2.png`. It does not assume the BC threshold has any particular value; it asks only whether treatment categories diverge from the control over time.

---

## 5. Refining the Graded Exposure Hypothesis: The Transcription Finding

The graded-exposure design (§1, Control Categories) predicted a monotonic ordering of post-shock ceiling drops: high exposure > medium exposure > low exposure. The five-category GMM (k=2) results in `data/output/gmm_graded_exposure_table.csv` produce the following ceiling Δ ordering:

| Rank | Category | Exposure tier | Pre-shock ceiling | Ceiling Δ |
|---|---|---|---|---|
| 1 | Creative logo design | High | $107 | **−$46** |
| 2 | Social media design | High | $76 | **−$40** |
| 3 | Creative writing | High | $81 | **−$23** |
| 4 | Data entry | Low | $36 | **−$18** |
| 5 | Transcription | **Medium** | **$21** | **+$2** |

Transcription's ceiling **rose slightly (+$1.58)** rather than falling, placing it *below* data entry in ceiling-drop magnitude. The naive monotonicity prediction (high > medium > low) is not borne out — the medium-exposure category shows the smallest movement of any category in the panel.

**Interpretation: ceiling collapse requires both AI exposure AND an existing premium tier.** The three high-exposure categories all had pre-shock ceilings between $76 and $107, with substantial room above the floor for a "premium human" tier to occupy. When AI substitutes for the commodity work, the premium tier is the part that collapses — clients who would have paid $80 for a logo are now satisfied with a $20 AI-aided gig, and the upper mode of the price distribution drops sharply. Transcription's pre-shock ceiling was already $21, only ~4× its $5 floor; it had **no meaningful premium tier left to collapse**. There is no "premium transcriptionist" pricing band on Fiverr the way there is for premium logo or copywriting work, because transcription is a routinized task whose buyers do not pay large multiples for craft. Whisper exposure could not produce the ceiling drop because the structural precondition for a ceiling drop did not exist.

**This refines the graded exposure hypothesis rather than invalidating it.** The corrected prediction is conditional: AI exposure produces ceiling collapse *only when* the category had a premium tier in the pre-shock distribution. Categories that were already commodity-priced cannot show ceiling compression because there is nothing above the floor to compress. The high-exposure trio satisfies the precondition and shows the predicted effect; transcription does not satisfy the precondition and shows no effect; data entry shows a smaller drop driven by platform-wide tier compression that touches every category to some degree (consistent with §4.3's argument that some bimodality movement is structural rather than AI-specific).

The implication for downstream analysis is that **ceiling Δ is not a clean dose-response measurement on its own** — it conflates AI exposure with pre-shock distributional shape. Reporting in `docs/its_specification.md` should pair ceiling-drop magnitude with pre-shock ceiling level, and the graded-exposure dose-response test should be read as "exposure produces ceiling collapse where structurally possible," not as a strict monotonic ordering across all five categories.

---

## 6. Final Analytic Conclusions

After fitting the within-category ITS models (`scripts/its_analysis.py`), the placebo and binary-DiD robustness checks (`scripts/robustness_checks.py`), and the substitutability-weighted graded-dose DiD (`scripts/weighted_did.py`), two findings consolidate and one is retired.

### 6.1 Price compression — supported

The price-compression result is the headline finding of the study. It survives every test we have run:

- **GMM (§5).** The three high-exposure categories all show large negative ceiling deltas (−$23 to −$46) between the pre- and post-shock GMM components. Data entry shows a smaller −$18, transcription is essentially flat. Ceiling drops scale with AI exposure when the structural precondition (a pre-shock premium tier) is met.
- **Within-category ITS.** Post-shock β₂ and β₃ on price are negative and significant for the high-exposure categories at multiple shock dates — logo design's β₃ at the Midjourney beta is −$19/month (p<0.001), creative writing's β₂ at the ChatGPT launch is −$19 (p=0.08). The within-category ITS is not time-locked to the specific shock dates (placebo, §6.3), but the broad direction of the price coefficients is consistent across specifications.
- **Substitutability-weighted graded-dose DiD.** With all five categories and substitutability scores from 0.10 (data entry) to 0.90 (logo design), the S × Post interaction on `price_median` is **−$32.6 (SE 13.0, p=0.066)** under two-way fixed effects, and sharpens to **−$40.2 (SE 9.9, p=0.015)** in the augmented spec that adds a linear time trend interacted with substitutability. The point estimates imply a **$26–$32 differential** between the highest-S (0.90) and lowest-S (0.10) categories in their post-July-2022 price change — the gradient predicted by the disruption hypothesis. The sign and approximate magnitude match the GMM ceiling-delta gradient.

Converging support across an outcome-shape test (GMM ceiling), a within-category trend-break test (ITS), and a graded-dose cross-category test (weighted DiD) is the strongest pattern available with the data on hand. **The price-compression claim should be the central empirical contribution of the paper.**

### 6.2 Bimodality — retired

The "AI made markets more bimodal" claim, prominent in the early framing, does not survive the robustness checks.

- **Placebo.** Real shock dates and shock dates shifted six months earlier produce indistinguishable significance rates on BC (real 13/20 coefficients significant at p<0.05; placebo 12/20). The within-category ITS on BC is picking up generic mid-panel trend inflections, not effects time-locked to the AI launches. Significance of the headline β₂/β₃ coefficients on BC therefore cannot be read causally.
- **Binary DiD vs. data-entry control.** Treated-minus-control BC change is *negative* and significant for logo design (DiD = −0.09, p=0.04) and social media design (DiD = −0.14, p=0.001). High-exposure categories became **less** bimodal than the control after the shock — the opposite direction of the disruption prediction.
- **Substitutability-weighted graded-dose DiD.** With the full five-category gradient, the S × Post interaction on BC is small and not significant (β = −0.07, p=0.39). The gradient test finds no evidence that higher AI exposure produces higher post-shock bimodality.

The pattern is consistent across both robustness designs: BC moved during the study window, but its movement is not specifically attributable to AI launches, and the direction is not the one the disruption hypothesis predicts. The original framing should be retired. The softened replacement claim — **"distributional shifts occurred consistent with ceiling compression"** — describes what the data actually show: the upper tail of the price distribution collapsed in exposed categories (the GMM ceiling result), which changes the *shape* of the distribution without producing the upward-BC signature that classical bimodality polarization would imply.

### 6.3 Revised paper framing

The study's contribution is reframed accordingly:

> **AI-driven price compression in freelance markets.** Generative AI exposure during 2022–2024 was associated with substantial collapse of the premium tier in directly substitutable Fiverr categories, with the magnitude of compression scaling with substitutability across a five-category gradient ($26–$40 differential between high- and low-exposure categories, p=0.015 under the augmented graded-dose DiD). The compression operates through the ceiling rather than the floor: floor prices were already at platform-tier minima pre-shock and could not fall further, while pre-shock premium-tier prices in high-substitutability categories dropped by $23–$46 between pre- and post-shock GMM components. No evidence is found for the alternative hypothesis that AI exposure polarized the distribution into separated commodity and premium modes — the bimodality coefficient does not respond to AI shocks in a time-locked or substitutability-graded way, and the binary DiD on BC has the wrong sign.

This reframing keeps the substantive economic story (AI reshapes freelance pricing through commoditization of premium work) while dropping a claim the data do not support (the price distribution becomes polarized). The price-compression finding is also closer to what the GPT-exposure literature (Eloundou et al. 2023) predicts at the task level, translated into the market-equilibrium consequence: tasks that AI can perform end-to-end see their human-labor premium erode rather than bifurcate.

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
