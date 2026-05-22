# AI-Driven Price Compression in Freelance Markets: Evidence from Fiverr, 2021–2024

**OQG x AISA Spring 2026**

---

## Abstract

We study whether the arrival of generative AI tools in 2022–2023 caused measurable shifts in price distributions on Fiverr, the world's largest online freelance marketplace. Using a graded quasi-experimental design — a five-category panel (2021–2024) spanning substitutability scores from S=0.10 (data entry, minimal AI threat) to S=0.90 (logo design, directly substitutable) — we find evidence of price compression that scales with AI exposure. Our headline identification, a substitutability-weighted difference-in-differences, estimates a differential post-shock price decline of S×Post = −$40.2 (SE $9.9, p=0.015) under the augmented specification, implying a $32 gap in post-2022 price change between the highest- and lowest-exposure categories. Compression operates through the ceiling: premium-tier prices (identified via a two-component Gaussian Mixture Model) fell $23–$46 in high-exposure categories while floor prices held near platform minimums. We also test the alternative hypothesis that AI exposure caused price distributions to polarize into separate commodity and premium modes (i.e., become bimodal). This hypothesis is not supported: the bimodality coefficient (BC) shows no substitutability gradient (S×Post = −0.071, p=0.39), and binary difference-in-differences estimates on BC have the wrong sign. Results survive placebo interruption tests and a score-sensitivity analysis in which 97% of perturbations preserve the direction and marginal significance of the compression finding.

---

## 1. Introduction

The period from July 2022 to May 2024 witnessed an unprecedented acceleration in the deployment of generative AI tools capable of producing professional-quality creative and textual outputs: Midjourney's open beta (July 2022), Stable Diffusion's public release (August 2022), ChatGPT's launch (November 2022), GPT-4 (March 2023), and GPT-4o's extension to free-tier users (May 2024). Unlike prior waves of automation, these tools directly substitute for the end product delivered by a large class of online freelancers — logo designers, social media graphic designers, and creative writers — rather than merely accelerating the workers' own production.

A growing empirical literature has begun to characterize AI's exposure at the task level. Eloundou et al. (2023) map LLM capability onto O*NET task descriptions and find that high-wage, high-skill occupations have greater GPT exposure, with writing, coding, and design tasks among the most exposed. What the task-level literature does not directly answer is the *market equilibrium consequence* of that exposure: if AI tools can now produce a deliverable that buyers previously paid $80 for, what happens to the distribution of prices in the market for that deliverable?

This paper asks that question using Fiverr, a gig-economy platform that provides unusually clean price visibility — sellers post fixed-price tiers and buyers see them before committing. We build a panel of monthly price observations for five Fiverr service categories spanning four years (2021–2024) and three levels of AI substitutability, extracted from Wayback Machine archived snapshots. The resulting dataset enables us to study price distribution dynamics before, during, and after the major AI shocks of 2022–2023.

We test two hypotheses:

1. **Price compression hypothesis.** AI exposure causes price distributions to compress — specifically, it erodes the premium tier while the floor, already bounded by platform minimums, cannot fall further. This implies a ceiling collapse rather than a symmetric squeeze.

2. **Bimodality hypothesis.** AI exposure causes price distributions to polarize into distinct commodity and premium modes, as buyers bifurcate between AI-aided cheap work and premium human-labeled craft. This is the intuitive "barbell" prediction common in early commentary on AI disruption.

We find support for the first hypothesis and against the second. The contribution of this paper is to connect the task-level exposure literature to a market-level outcome — the shape of the price distribution — and to show that the mechanism is ceiling collapse, not bifurcation.

---

## 2. Data

### 2.1 Data Collection

All price data are extracted from Wayback Machine archived HTML snapshots of Fiverr category listing pages. For each of the five service categories, we used the CDX API to identify available monthly snapshots and extracted gig-level prices, titles, seller information, and star ratings from the archived HTML.

Two distinct HTML price formats are handled by the extractor: a pre-May 2023 format (prices in `<a class="price"><span>` tags) and a post-May 2023 format (prices nested inside `<span class="text-bold">From <span>` elements). The dual-path extractor was validated against spot-sampled snapshots from both periods. Detailed notes on extraction issues, fixes, and residual gaps are in `docs/data_quality.md`.

### 2.2 Panel Construction

The final panel contains **1,670 gig-month observations** across five categories and approximately 48 calendar months (January 2021 – December 2024). Of these, 56 rows (3.4%) have null prices due to snapshot quality failures and are excluded from all monthly aggregations. The analysis-ready sample is 1,614 rows with valid prices.

The panel is at the individual gig level; all statistical models operate on monthly category-level aggregates (median price, bimodality coefficient), constructed by grouping gig-level rows to (category, calendar-month) cells. Months with zero valid prices for a category are excluded from that category's time series.

See **Figure 1** (coverage heatmap) for the full coverage structure. Notable gaps:
- Logo design: no observations before May 2021 (Wayback crawl availability)
- Multiple categories: zero-price months in mid-2023 (unrecoverable degraded snapshots following the May 2023 markup change)
- Logo design: January 2024 (partially-loaded snapshot)

### 2.3 Substitutability Scores and Study Design

Rather than a binary treated/control split, we use a **graded-dose design** with a continuous AI substitutability score S ∈ [0.10, 0.90] assigned to each category *a priori* (before analysis). This converts the identification from a binary DiD into a dose-response test: if AI disruption is the cause, effect sizes should scale with S.

**Table 1** provides the panel summary with substitutability scores. The scoring rationale is as follows:

| Category | S | Rationale |
|---|---|---|
| Creative logo design | 0.90 | Image-gen AI (Midjourney, Stable Diffusion) produces end-to-end substitute deliverables; clients no longer need a human designer for a basic logo |
| Social media design | 0.85 | Same image-gen AI threat; slightly lower because social media designs are more template-reliant and adapt better to human–AI hybrid workflows |
| Creative writing | 0.80 | LLMs (ChatGPT, GPT-4) produce directly substitutable creative text; slightly lower than image-gen categories because buyers may still prefer perceptibly human voice |
| Transcription | 0.40 | Speech-to-text (Whisper, released September 2022) automates the core task but humans are still needed for quality review, timestamps, speaker labeling, and domain-specific terminology — partial substitution |
| Data entry | 0.10 | No major AI product during the study window directly substitutes for manual data entry at scale; automation existed pre-2022 and is not an AI-era shock |

Scores are researcher-assigned and subject to sensitivity analysis (see §4.6). The specific numerical values are less important than the ordering and the spread; the identification requires only that higher-S categories are genuinely more AI-exposed than lower-S ones.

**Design validity check:** Having two graphics subcategories (logo design and social media design) at similar exposure levels allows a within-arm consistency check. If both move similarly after image-gen AI launches, that strengthens the causal interpretation against idiosyncratic category effects.

### 2.4 AI Shock Dates

We define shocks by the public availability dates of the major generative AI tools:

| Date | Event | Categories treated |
|---|---|---|
| 2022-07-12 | Midjourney open beta | Logo design, social media design |
| 2022-08-22 | Stable Diffusion public release | Logo design, social media design |
| 2022-09-21 | OpenAI Whisper open-source release | Transcription (control-medium) |
| 2022-11-30 | ChatGPT public launch | Creative writing |
| 2023-02-01 | ChatGPT Plus subscription tier | Creative writing |
| 2023-03-14 | GPT-4 release | Creative writing |
| 2023-03-15 | Midjourney V5 | Logo design, social media design |
| 2024-05-13 | GPT-4o extended to free users | Creative writing |

Data entry (S=0.10) has no assigned shock date. It serves as a pure trend baseline.

---

## 3. Methods

### 3.1 Within-Category Interrupted Time Series (ITS)

For each category, we fit a segmented regression model to monthly category-level aggregates. The design allows multiple shocks per category:

$$Y_t = \beta_0 + \beta_1 t + \sum_{k=1}^{K} \left[\beta_{2k} D_{k,t} + \beta_{3k} (D_{k,t} \cdot t)\right] + \varepsilon_t$$

where $D_{k,t} = \mathbf{1}[t \geq \text{shock}_k]$ is the indicator for being post-shock $k$, $\beta_{2k}$ is the immediate level shift at shock $k$, and $\beta_{3k}$ is the change in monthly slope following shock $k$. Standard errors use Newey-West heteroskedasticity-and-autocorrelation-consistent (HAC) correction with lag length $L = \lfloor 4 (T/100)^{2/9} \rfloor$, which evaluates to $L = 3$ for our series lengths ($T \approx 31$–46).

ITS is fit per category separately; it identifies within-category trend breaks rather than cross-category differentials. It is best interpreted alongside the cross-category DiD in §3.2.

### 3.2 Substitutability-Weighted Graded-Dose DiD (Main Identification)

The primary identification strategy stacks all five categories into a single panel and estimates whether the post-shock change in outcomes scales with S:

**Spec A (Two-Way Fixed Effects):**
$$Y_{ct} = \gamma_c + \delta_t + \beta (S_c \times \text{Post}_t) + \varepsilon_{ct}$$

where $\gamma_c$ is a category fixed effect (absorbs the S main effect, which is time-invariant), $\delta_t$ is a month fixed effect (absorbs the Post main effect), and $S_c \times \text{Post}_t$ is the dose-response interaction. $\beta$ is the graded DiD coefficient.

**Spec B (Trend Interaction):**
$$Y_{ct} = \gamma_c + \alpha t + \beta_1 (S_c \times \text{Post}_t) + \beta_2 (S_c \times t) + \varepsilon_{ct}$$

Spec B drops month fixed effects (so $S \times t$ is identified) and adds a differential linear trend per exposure level. This tests whether higher-S categories were already trending differently before the cutoff.

The post cutoff is July 2022 (the first image-gen shock month), applied uniformly across all categories so that the month fixed effects in Spec A remain identified. Standard errors are cluster-robust by category. With five clusters, this is below the rule-of-thumb threshold (~10 clusters) for reliable asymptotic inference; these SEs should be treated as indicative rather than precise. This is a named limitation (§6).

**Translation to dollar magnitudes:** The coefficient $\beta$ is the differential change per unit of S. The implied gap between the highest- (logo design, S=0.90) and lowest-substitutability (data entry, S=0.10) categories is $(S_\text{max} - S_\text{min}) \times \hat\beta = 0.80 \times \hat\beta$.

### 3.3 Gaussian Mixture Model (GMM) Distributional Analysis

To directly characterize the shape change in price distributions, we fit a two-component Gaussian Mixture Model (k=2) on log-prices separately for the pre-shock and post-shock periods for each category. The lower-mean component is labeled the **floor** (commodity tier) and the upper-mean component the **ceiling** (premium tier).

This allows us to test whether compression operates through floor decline, ceiling decline, or both. Pre/post split is at each category's primary shock date (logo design and social media: 2022-07-12; creative writing: 2022-11-30; transcription: 2022-09-21; data entry: 2022-07-12 as reference).

### 3.4 Bimodality Testing

As a secondary test of the polarization hypothesis, we compute Sarle's Bimodality Coefficient (BC) and Hartigan's dip statistic on quarterly price aggregates (~20–30 observations per cell), which are more reliable than monthly moments. A BC > 0.555 indicates bimodal tendency; the dip test (H₀: unimodal) supplements it with a calibrated p-value.

Because Fiverr's tier-pricing structure (Basic/Standard/Premium packages) creates platform-wide bimodality in every category — including the data-entry control — we focus on the *treatment-minus-control BC differential* rather than absolute BC levels.

### 3.5 Robustness Checks

Three robustness specifications are run:

1. **Placebo ITS:** All ITS models are re-run with shock dates shifted six months earlier. If the real shock dates are informative, real significance rates should exceed placebo rates.

2. **Binary 2×2 DiD:** For each treatment category, we fit `Y ~ treated + post + treated×post + t` using the category and data-entry control as the only two groups. This is lower-powered than the graded-dose spec but avoids the assumption of a linear S dose-response.

3. **Score sensitivity:** The graded-dose DiD (Spec A) is re-run 42 times, varying each category's S score by ±0.05, ±0.10, and ±0.20 (one at a time and all simultaneously). This tests how much the headline finding depends on the specific numerical score assignments.

---

## 4. Results

### 4.1 Descriptive Patterns

**Figure 2** (main compression figure) shows monthly median prices by category from 2021 to 2024. Treatment categories (solid lines) exhibit clear downward trends following the AI shock events of 2022–2023. Logo design, which begins the period with a median price near $25, declines to roughly $15 by 2024. Social media design and creative writing follow similar trajectories, though with somewhat more volatility. Control categories (dashed lines) show flatter trends — data entry, always priced near its platform floor, remains near $5–$20 throughout; transcription is similarly stable.

The price index panel (Panel B of **Figure 2**), which normalizes each category to its 2021 average = 100, makes the divergence cleaner. All three treatment categories end 2024 roughly 30–50% below their 2021 baselines, while both control categories hold closer to 100. This visual pattern motivates the formal identification.

### 4.2 Price Compression: Main DiD Results

**Table 2** reports the graded-dose DiD results. Under Spec A (TWFE), the S×Post coefficient on price_median is **−$32.6 (SE $13.0, p=0.066)**, significant at the 10% level. Spec B (which adds a differential linear trend) sharpens this to **−$40.2 (SE $9.9, p=0.015)**, significant at 5%.

Translating to dollar magnitudes: the implied gap between logo design (S=0.90) and data entry (S=0.10) in their post-July-2022 price change is $0.80 × $32.6 = **$26.1** under Spec A and **$32.2** under Spec B. In other words, by the end of the study period, the most AI-exposed categories had price levels roughly $26–$32 lower *relative to the least-exposed category* compared to the pre-July-2022 relationship.

The S×t coefficient in Spec B is small and not significant (β₂ = +$0.33/month, p=0.46), providing no evidence that high-S and low-S categories were already on diverging price trends before the shock cutoff. This supports a post-2022 disruption effect rather than a pre-existing differential trend.

### 4.3 GMM Distributional Evidence: Ceiling Collapse

**Table 4** and **Figure 3** (floor/ceiling trajectories) decompose the price distribution shift using the GMM analysis. The findings are consistent across all three high-exposure categories: **ceiling collapse dominates**.

- **Creative logo design:** ceiling $107 → $60 (−$46.3); floor $17.9 → $16.5 (−$1.4)
- **Social media design:** ceiling $76 → $36 (−$39.6); floor $17.0 → $13.5 (−$3.6)
- **Creative writing:** ceiling $81 → $58 (−$23.1); floor $13.0 → $11.4 (−$1.6)
- **Data entry (control, low):** ceiling $36 → $17 (−$18.3); floor $8.8 → $5.0 (−$3.8)
- **Transcription (control, medium):** ceiling $21 → $23 (+$1.6); floor stable at $5.0

The pattern is economically interpretable: clients who previously paid $80–$107 for a professional logo or creative graphic can now produce an acceptable substitute using Midjourney for a fraction of the cost. The human freelancers serving that premium tier have no choice but to match the new competition or exit. The floor, already at or near Fiverr's $5 minimum gig price, cannot be compressed further.

The data-entry control shows a non-trivial ceiling decline (−$18.3) that is not attributable to AI shocks (data entry has no shock in our design). This signals platform-wide pricing changes — a common downward trend — that the graded-dose design is meant to partial out. The ceiling drop in high-exposure categories ($23–$46) substantially exceeds the data-entry control decline, consistent with an AI-specific effect layered on top of the platform-wide trend.

**The transcription finding reveals a structural precondition.** Transcription's ceiling did not collapse despite having a genuine AI shock (Whisper). The explanation: transcription's pre-shock ceiling was only $21 — roughly 4× the floor — and there was no meaningful "premium human" tier priced at $50–$100 to collapse. Ceiling compression requires both AI exposure *and* a pre-existing premium tier that the AI can undercut. The high-exposure trio satisfies both conditions; transcription satisfies only the first.

### 4.4 ITS Results

**Table 3** reports selected ITS coefficients on price_median. The pattern across categories is consistent with price compression following the primary shocks:

- **Logo design (Midjourney beta, 2022-07-12):** β₃ (slope change) = −$19.2/month (p<0.001), indicating a sustained downward price trend beginning at the shock. The level shift β₂ is not significant (−$50.9, p=0.23), consistent with price adjustments occurring gradually rather than as an immediate jump.

- **Logo design (Midjourney V5, 2023-03-15):** β₂ = +$2.4 (p=0.085), a small upward level adjustment, and β₃ = +$0.62/month (p<0.001). This suggests a modest floor-finding period around Midjourney V5 — a slight stabilization in the rate of decline.

- **Social media design (Midjourney beta, 2022-07-12):** β₃ = −$27.4/month (p<0.001), the steepest post-shock slope change in the panel.

- **Social media design (Stable Diffusion, 2022-08-22):** β₂ = −$65.0 (p<0.001). This large level shift partially reflects the multi-shock ITS accounting: with both July and August shocks stacked, the August coefficients absorb the accumulated price gap between what the July trend would have predicted and where prices actually landed. The net post-shock trajectory is compression.

- **Creative writing (ChatGPT launch, 2022-11-30):** β₂ = −$19.2 (p=0.084), a marginally significant level drop at the first major text-LLM shock. β₃ = −$16.0/month (p=0.085), also marginal.

- **Creative writing (GPT-4o, 2024-05-13):** β₂ = −$3.4 (p=0.037), a smaller but significant level drop at the most recent shock.

**Figure 4** (ITS coefficients plot) displays the full set of β₂ and β₃ estimates by category and shock. The overall pattern is negative coefficients dominating the price_median outcome in high-exposure categories, with the exception of partial offset terms in the multi-shock specifications.

### 4.5 Bimodality: A Non-Result

We tested the hypothesis that AI exposure caused price distributions to polarize — the intuitive "barbell" prediction in which a mass of cheap AI-aided gigs forms at the floor while a surviving premium human tier holds at the ceiling. This hypothesis is not supported.

Three independent analyses reject the polarization interpretation:

**1. Graded-dose DiD on BC (Table 2):** The S×Post coefficient on the bimodality coefficient is **−0.071 (SE 0.074, p=0.387)** under Spec A — not significant and in the *wrong direction* for the disruption hypothesis. Under Spec B, the estimate is +0.022 (p=0.835). There is no evidence that higher-substitutability categories became more bimodal after the shocks.

**2. Binary DiD on BC:** When we fit a traditional 2×2 DiD comparing each treatment category to the data-entry control, the estimated BC change is negative and in some cases significant — treatment categories became **less** bimodal than the control post-shock:
- Logo design vs. data entry: DiD = −0.093 (SE 0.044, p=0.036) — significant at 5%
- Social media vs. data entry: DiD = −0.136 (SE 0.038, p=0.001) — significant at 1%
- Creative writing vs. data entry: DiD = −0.020 (SE 0.049, p=0.679) — not significant

In two of three treatment categories, the distribution became measurably *less* polarized relative to the control, not more. This is the opposite of the bimodality hypothesis prediction.

**3. Placebo ITS on BC:** When shock dates are shifted six months earlier, significance rates on ITS BC coefficients are nearly indistinguishable from those using real shock dates. Real shock dates do not produce anomalously high BC significance rates, indicating that ITS detects generic mid-panel fluctuations rather than bimodality changes time-locked to AI launches.

**We retire the bimodality hypothesis.** The ceiling-collapse pattern from the GMM analysis describes what actually happened: the upper tail of the price distribution collapsed in exposed categories, *narrowing* the price band rather than *polarizing* it. A collapsed ceiling does not produce bimodality — it produces a more compressed, less spread-out distribution. The negative BC direction in the binary DiD is consistent with this: ceiling collapse brings the upper mode down toward the floor, reducing the inter-mode separation that bimodality measures.

The revised interpretation: **AI exposure produced ceiling compression, not polarization.** The commodity/premium bifurcation prediction assumed the premium tier would survive as a separate "human-labeled" mode. Instead, the premium tier collapsed because buyers did not persistently pay a premium for human craft in the face of equivalent AI output at lower cost.

### 4.6 Robustness

**Score sensitivity:** The score-sensitivity analysis (**Figure 5**) varies each category's substitutability score by ±0.05, ±0.10, and ±0.20, one at a time and all simultaneously (42 model runs total). **35 of 36 perturbation runs (97%)** maintain the direction and marginal significance (p<0.10) of the compression finding. The single run that drops below p=0.10 is a large perturbation of the transcription score, which most alters the dose-response gradient's shape. The compression finding is highly stable to plausible reassignment of substitutability scores.

**Placebo ITS (price):** For the price_median outcome, placebo shock dates (shifted −6 months) produce fewer and smaller significant coefficients than real shock dates, particularly for the β₃ slope change terms. Logo design's β₃ at the real Midjourney beta (−$19.2/month, p<0.001) has no parallel at the −6 month placebo (which falls in January 2022, with no market event). This provides evidence that the ITS timing is information-bearing for the price outcome.

**Binary 2×2 DiD (price):** The binary DiD for logo design vs. data entry finds a price DiD of **−$41.3 (SE $20.0, p=0.043)**. Social media vs. data entry (−$9.8, p=0.21) and creative writing vs. data entry (−$17.4, p=0.11) are not significant at conventional levels individually, but the lower power of the 2×2 design (which uses only two categories and loses the dose-response gradient) is expected to produce wider confidence intervals than the five-category graded-dose spec.

---

## 5. Discussion

### 5.1 Economic Interpretation

The mechanism behind the results is straightforward: AI tools lowered the cost of producing outputs in high-substitutability categories, intensifying supply-side competition at the quality level that previously commanded premium prices. Clients who would have paid $80–$107 for a professional logo now have a credible outside option — Midjourney or similar — for $20 or less. Human freelancers who built their business serving those buyers face a hard choice: match the new price floor or exit the commodity segment.

What the data show is that the premium tier collapsed rather than survived. There is no evidence of a "premium human-labeled" mode persisting at the old ceiling. This is consistent with the view that in these categories, buyers are not willing to pay a large multiple for work explicitly labeled as human. The "human signal" premium — if it exists on Fiverr — is not large enough to be detected in the cross-category price distribution.

### 5.2 The Structural Precondition Finding

The transcription result adds an important nuance to the graded-dose framework. The monotonic prediction (high-S effect > medium-S effect > low-S effect) does not hold when we look at ceiling deltas. Transcription (medium S=0.40) shows essentially no ceiling decline despite having a genuine AI shock (Whisper). Data entry (low S=0.10) shows a larger ceiling decline than transcription despite having no assigned shock.

The explanation is structural: ceiling collapse requires both AI exposure *and* a pre-existing premium tier to collapse. Transcription's pre-shock ceiling was $21 — there was no $80 premium tier for Whisper to undercut. Data entry shows a ceiling decline that tracks platform-wide trends rather than an AI-specific disruption.

This finding refines the dose-response prediction: **AI exposure × pre-existing premium tier → ceiling compression**. Categories with high AI exposure and high pre-shock ceilings (logo design, social media design, creative writing) satisfy both conditions. Categories that lack either component show the predicted effect less clearly or not at all.

For future applications of this framework, this suggests that the appropriate measure of "disruption risk" is not just AI substitutability, but the product of substitutability and the existing premium-tier magnitude. A high-S, low-ceiling category is less disrupted than a high-S, high-ceiling one.

### 5.3 Relation to Eloundou et al. (2023) and the GPT-Exposure Literature

Eloundou et al. (2023) identify which tasks and occupations have high GPT exposure based on LLM capability matching. Our three treatment categories (logo design, social media design, creative writing) correspond to occupations Eloundou et al. classify as high-exposure. This study provides the market-level outcome that their task-level analysis predicts: if LLMs can perform these tasks at scale, the market for human-provided versions should see price compression.

The convergence between the task-level and market-level findings is encouraging for the validity of both. It also suggests a research agenda: for which high-GPT-exposure occupations do we see market-level price compression, and for which do we see quantity adjustments (displacement without price change) or quality upgrading (sellers pivot to higher-value work that AI cannot replicate)?

---

## 6. Limitations

**Small panel and weak SEs.** With five categories, cluster-robust standard errors are asymptotically unreliable — the standard rule of thumb requires at least 10 clusters. The p-values in Table 2 should be interpreted as indicative. Replication with a larger panel (more categories) would substantially strengthen the inferences.

**Wayback Machine coverage is opportunistic.** The archive crawls Fiverr at irregular intervals; some months have multiple snapshots, others have none. The panel is constructed from roughly one snapshot per category per month, but coverage is uneven (see Figure 1). The extracted sample (~8–12 gigs per category-month) is unlikely to be representative of the full category listing. Systematic variation in which gigs are crawled could bias price medians.

**Substitutability scores are researcher-assigned.** The scores are a priori theoretical constructs, not measured from data. The sensitivity analysis shows the finding is robust to perturbations, but a Harvard or journal reviewer will ask whether the scores can be independently validated (e.g., from task survey data, API capability benchmarks, or user-behavior data from Fiverr). This is a meaningful limitation.

**Platform policy confounders.** Fiverr has changed its search ranking algorithms, packaging structures (Basic/Standard/Premium tiers), and buyer incentives over the study period. These changes could produce platform-wide price changes unrelated to AI. The graded-dose design partially addresses this — any platform-wide change would affect all categories equally and be absorbed by the differential — but category-specific platform policy changes could not be excluded.

**GMM k=2 assumption.** The floor/ceiling decomposition assumes a two-component mixture, which may not accurately describe the empirical price distribution if there are more than two meaningful price tiers. A k=3 or k=4 model was not tested.

**`ai_assisted` and `human_signal` supply-side flags unused.** The panel contains boolean flags for gigs explicitly advertising AI assistance or human-only work. These flags could be used to study whether explicitly AI-labeled gigs cluster at the price floor, or whether human-signal sellers occupy a surviving premium niche. This analysis is left for future work.

---

## Figures

- **Figure 1:** Coverage heatmap (`figures/final/coverage_heatmap.png`)
- **Figure 2:** Main compression figure — absolute prices and price index (`figures/final/main_compression.png`)
- **Figure 3:** GMM floor/ceiling trajectories (`figures/final/floor_ceiling_trajectories.png`)
- **Figure 4:** ITS coefficient forest plot (`figures/final/its_coefficients.png`)
- **Figure 5:** Score sensitivity forest plot (`figures/final/sensitivity_forest.png`)

## Tables

- **Table 1:** Panel summary (`tables/table1_panel_summary.md`)
- **Table 2:** Weighted DiD results (`tables/table2_weighted_did.md`)
- **Table 3:** ITS results, selected shocks (`tables/table3_its_results.md`)
- **Table 4:** GMM floor/ceiling pre/post (`tables/table4_gmm_floor_ceiling.md`)

---

## References

Eloundou, T., Manning, S., Mishkin, P., & Rock, D. (2023). GPTs are GPTs: An early look at the labor market impact potential of large language models. *arXiv preprint* arXiv:2303.10130.

*[Additional references to be added: labor market platform studies, gig economy pricing literature, bimodality methodology references (Hartigan & Hartigan 1985, Sarle 1990).]*

---

## Appendix

### A.1 Scoring System Justification

The five substitutability scores represent *a priori* theoretical assessments of how directly generative AI tools introduced during the study window can substitute for the end deliverable of each category's typical gig. The key distinction is between *end-to-end substitution* (high S) and *workflow acceleration* (medium S):

- **End-to-end substitution (high S):** A buyer who previously hired a freelancer to produce a logo, social media graphic, or short creative piece can now prompt Midjourney, Stable Diffusion, or ChatGPT and receive a deliverable they consider equivalent at zero marginal labor cost. The human freelancer is no longer necessary for a large share of the buyer intent.

- **Workflow acceleration (medium S):** Whisper automates the transcription of audio, but buyers frequently require additional services that speech-to-text alone does not provide: precise timestamps, speaker labels, formatting for legal or medical contexts, correction of domain-specific terminology. A freelance transcriptionist's value proposition shifts from "I will type what was said" to "I will produce a final, usable transcript" — a service for which pure speech-to-text is an input, not a replacement.

- **No direct AI substitute (low S):** Data entry during the study window (2021–2024) was not meaningfully automated by generative AI. General-purpose tools like ChatGPT can assist with formatting or lookup tasks but do not replace a human who physically transfers data from one medium to another. Traditional scripting automation pre-dates the AI-era shocks and is not represented in these scores.

The scores do not represent precision measurements. They operationalize an ordinal judgment: logo design (0.90) is more directly substitutable than transcription (0.40), which is more substitutable than data entry (0.10). The score-sensitivity analysis (§4.6) confirms that the compression finding survives meaningful variation in these assignments.

### A.2 Bimodality Measurement

The raw monthly bimodality coefficient approach (Sarle's BC with the 0.555 threshold) was the initial analysis strategy but was abandoned after three problems emerged:

1. **Structural bimodality predates AI.** The data-entry control had more months above BC=0.555 than the social media design treatment category, indicating that Fiverr's own tier-pricing (Basic/Standard/Premium packages at $5, $25, $100) creates platform-wide distributional clustering independent of AI disruption.

2. **Monthly cells are too small.** With ~8 gigs per (category, month), sample kurtosis and skewness are highly unstable. BC oscillates around the 0.555 threshold for all categories throughout the panel.

3. **Numerical instability.** Tightly-clustered price months (e.g., many $5 gigs) produce precision-loss warnings in moment calculations; these cells' BC values are unreliable.

The revised approach uses: (a) quarterly aggregation for cell-size stability, (b) the Hartigan dip test (properly calibrated for sample size) rather than the BC threshold, and (c) the treatment-minus-control BC differential (differencing out platform-wide structural bimodality). All three approaches independently fail to support the polarization hypothesis, and the binary DiD on BC has the wrong sign. These convergent non-results provide confidence that the bimodality retirement is well-founded.
