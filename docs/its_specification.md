# Interrupted Time Series (ITS) Specification

## OQG x AISA — Fiverr Price Distribution Study

---

## 1. Model Form

We estimate segmented regression interrupted time series models on monthly category-level data (2021-01 through 2024-12).

**Outcome variables (estimated separately):**
- `price_median` — within-month, within-category median gig price (level)
- `BC` — Sarle's bimodality coefficient computed on the within-month price distribution

**Time variable:**
- `t` — month index, integer, anchored at the panel start (`t = 0` for 2021-01)

**Treatment indicators (per category):**
For each shock date `Tk` defined for that category:
- `Dk` — step indicator: `1` for months on or after `Tk`, else `0`
- `(t − Tk) · Dk` — slope-change term: months elapsed since the shock, zero before

The model is fit per category (one regression per category × outcome). The control category (`data/data-entry`) has no shock terms — it provides counterfactual validation via the DiD robustness check (§4), not via the within-category ITS.

**Estimator:** Ordinary least squares with Newey-West heteroskedasticity- and autocorrelation-consistent (HAC) standard errors. Lag length follows the Newey-West (1994) automatic bandwidth selection rule, `L = floor(4 · (T/100)^(2/9))`, where `T` is the number of monthly observations available for the category.

---

## 2. Shock Dates per Category

Shocks are drawn from `data/ai_events.json` and mapped to categories per the AI-disruption vector each category is exposed to.

| Category | Shock dates | Source event |
|---|---|---|
| `graphics-design/creative-logo-design` | 2022-07-12, 2022-08-22, 2023-03-15 | Midjourney open beta; Stable Diffusion public release; Midjourney V5 |
| `graphics-design/social-media-design` | 2022-07-12, 2022-08-22, 2023-03-15 | Same image-generation shocks (shared exposure to image-gen AI) |
| `content-writing/creative-writing` | 2022-11-30, 2023-02-01, 2023-03-14, 2024-05-13 | ChatGPT public launch; ChatGPT Plus; GPT-4; GPT-4o free to all |
| `data/data-entry` | — | Control category, no shock |

For monthly aggregation, each shock date is binned to its calendar month: `Tk` enters the regression as the month index of the first month strictly affected by the event (e.g., a 2022-07-12 event sets `Dk = 1` for 2022-07 and onward).

---

## 3. Functional Form

For a category with `K` shocks at month indices `T1, …, TK`:

```
Yt = β0 + β1·t + Σ[k=1..K] ( β2k·Dk + β3k·(t − Tk)·Dk ) + εt
```

Where:
- `β0` — pre-shock intercept (baseline level at `t = 0`)
- `β1` — pre-shock secular trend (per-month change before any shock)
- `β2k` — immediate **level change** at shock `k`
- `β3k` — change in **slope** after shock `k` (additive to the prior slope)
- `εt` — residual; HAC-corrected via Newey-West

**Interpretation rules:**
- A negative, significant `β2k` indicates an immediate price drop coinciding with shock `k`.
- A negative, significant `β3k` indicates the post-shock trend is more downward (or less upward) than the pre-shock trend.
- For the BC outcome, a positive `β2k` or `β3k` indicates the distribution becoming **more bimodal** after the shock — the substantive prediction of the disruption hypothesis (top-tier sellers retain pricing power, low-tier prices collapse).

For categories with multiple shocks, post-shock segments stack: the cumulative slope after shock `k` is `β1 + Σ[j≤k] β3j`, and the cumulative level shift at month `t ≥ Tk` is the sum of `β2j` for all `j ≤ k` plus the accumulated slope adjustments.

---

## 4. Robustness Checks

### 4.1 Difference-in-Differences using Substitutability Index

A DiD specification using `data/data-entry` as the control category complements the within-category ITS by partialling out platform-wide trends (Fiverr-side pricing changes, search-ranking shifts, macro effects).

```
Yct = α0 + α1·Postt + α2·Treatedc·Postt + γc + δt + εct
```

Where `Treatedc` is weighted by the **AI substitutability index** for category `c` — a continuous score (0–1) reflecting how directly generative AI can replace that service. The substitutability index will be derived from the keyword-flag work and external task-exposure scores (e.g., Eloundou et al. 2023 GPT exposure, where applicable). This converts the binary treated/control split into a graded dose-response test: categories with higher substitutability should show larger `α2` if the causal story holds.

### 4.2 Placebo Tests with 6-Month Offset Event Dates

Re-estimate the ITS models in §1–3, replacing each true shock date `Tk` with `Tk − 6 months`. Under the null hypothesis that nothing AI-specific drove the observed effects, the placebo regressions should produce coefficients statistically indistinguishable from zero. A significant placebo coefficient would indicate a pre-existing trend break unrelated to the actual AI launch and would weaken the causal interpretation of the main results.

A symmetric `Tk + 6 months` placebo is reported as a secondary check (it tests whether the effect is truly time-locked to the shock or merely a post-hoc trend that any downstream date would pick up).

---

## 5. Implementation Notes

- Monthly aggregation collapses the panel to one row per `(category, year-month)`. Cells with fewer than 5 observations are flagged but retained; sensitivity to a `min_n ≥ 10` filter is reported.
- Standard errors via `statsmodels` `OLS.fit().get_robustcov_results(cov_type='HAC', maxlags=L)`.
- All outcome variables are reported in their natural units (USD for `price_median`, unitless for `BC`); no log transform unless residual diagnostics indicate it is necessary.
