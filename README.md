# AI-Driven Price Compression in Freelance Markets

Quasi-experimental study of 1,670 Fiverr gig-months (2021–2024) finding that generative AI exposure caused freelance prices to collapse from the top down — not polarize into cheap/premium tiers as commonly assumed — with the effect size scaling by up to $40 per unit of AI-substitutability risk (p=0.015).

## What It Does

- **Builds an original panel dataset** from scratch by scraping Wayback Machine's archived snapshots of Fiverr category pages via the CDX API — no existing dataset for this question existed, so data collection was the first deliverable
- **Handles a live extraction problem**: Fiverr changed its price HTML markup mid-study (May 2023), silently zeroing out every post-change snapshot until a dual-path selector fix was built and validated against spot-sampled pages from both eras
- **Designs a graded quasi-experiment**: five Fiverr categories assigned a priori AI-substitutability scores (S = 0.10 to 0.90, e.g. data entry vs. logo design) instead of a simple treated/control split, turning the test into a dose-response check
- **Runs three independent identification strategies** and checks that they agree:
  - Substitutability-weighted difference-in-differences (cluster-robust SEs)
  - Per-category interrupted time series with HAC-corrected standard errors, anchored to actual AI product launch dates (Midjourney, Stable Diffusion, ChatGPT, GPT-4, Whisper)
  - A two-component Gaussian Mixture Model per category to separate "floor" (commodity) and "ceiling" (premium) price tiers and test which one moves
- **Stress-tests its own headline finding**: placebo shock dates, a binary 2×2 DiD robustness check, and a 42-run sensitivity analysis that perturbs every substitutability score by ±0.05–0.20 (97% of runs preserve the result's direction and significance)
- **Tests and rejects its own secondary hypothesis**: the intuitive prediction that AI would polarize prices into a bimodal cheap/premium split is explicitly tested with Sarle's bimodality coefficient and Hartigan's dip test — and retired, in writing, when three independent checks contradict it
- **Generates a full academic write-up** (`paper/draft.md`) with abstract, methods, results, limitations, and a PDF-ready figure/table pipeline

## Key Result

Premium-tier prices fell **$23–$46** in the three highest-AI-exposure categories (logo design, social media design, creative writing) while floor prices — already near Fiverr's platform minimum — barely moved. The effect did not appear in a medium-exposure control (transcription) that lacked a pre-existing premium tier for AI to undercut, which sharpened the finding into a conditional one: *AI exposure collapses prices only where a premium tier already existed to collapse.*

## Quick Start

```bash
git clone https://github.com/BenjaminTell007/oqg-fiverr-research.git
cd oqg-fiverr-research
pip install -r requirements.txt
playwright install chromium   # only needed if re-scraping
```

The built panel (`data/output/full_panel.csv`) and every downstream table/figure are already checked into the repo, so you can go straight to analysis without re-scraping:

```bash
python scripts/weighted_did.py            # main graded-dose DiD (the headline result)
python scripts/its_analysis.py            # per-category interrupted time series
python scripts/gmm_analysis.py            # floor/ceiling distribution decomposition
python scripts/bimodality_analysis_v2.py  # bimodality coefficient + dip test
python scripts/robustness_checks.py       # placebo tests + binary DiD
python scripts/sensitivity_analysis.py    # substitutability-score perturbation sweep
```

To rebuild the panel from raw Wayback Machine snapshots instead:
```bash
python scripts/full_scrape.py
python scripts/fill_2023_2024.py
```

The full paper is at [`paper/draft.md`](paper/draft.md); the research-design decisions (why these five categories, why 2021–2024, why the bimodality hypothesis was retired) are documented in [`docs/research_rationale.md`](docs/research_rationale.md).

## Tech Stack

| Tool | Why |
|---|---|
| `playwright` + `requests` + `beautifulsoup4` | Wayback Machine snapshots are rendered HTML, not an API — Playwright handles JS-shell pages, BeautifulSoup parses two different DOM structures across the study period |
| `pandas` | Panel construction: gig-level rows rolled up to (category, month) and (category, quarter) aggregates |
| `statsmodels` | OLS with cluster-robust and Newey-West HAC standard errors for the DiD and ITS specifications — needed because 5-category panels violate the usual asymptotic cluster-count assumptions, which the paper's limitations section addresses explicitly |
| `scikit-learn` (`GaussianMixture`) | Unsupervised 2-component fit to separate floor/ceiling price tiers without assuming their locations in advance |
| `scipy` + `diptest` | Sarle's bimodality coefficient and Hartigan's dip test — two independent tests for distributional polarization, used to cross-check each other |
| `matplotlib` | All publication figures (coverage heatmap, compression trends, ITS coefficient plots, sensitivity forest plot) |
| `reportlab` | Programmatic PDF generation for the write-up |

## Challenges Overcome

- **Fiverr's markup changed mid-collection.** A May 2023 HTML change silently broke price extraction on every subsequent snapshot; the fix required a dual-path selector validated against both eras, documented in [`docs/data_quality.md`](docs/data_quality.md).
- **Naive bimodality testing was actively misleading.** The textbook BC-threshold approach flagged the *control* category as bimodal more often than the treatment categories, because Fiverr's own Basic/Standard/Premium tier pricing creates baseline bimodality on the whole platform. The fix was a treatment-minus-control differential that nets out platform-wide structure — a design choice documented and justified in the rationale doc rather than silently applied.
- **Small-cluster inference.** A 5-category panel is below the conventional 10-cluster threshold for reliable cluster-robust SEs. Rather than hide this, the paper reports it as a named limitation and adds a 42-run sensitivity analysis to show the result isn't an artifact of the specific category scores chosen.

## Future Improvements

- Extend the panel past 2024 (technically feasible — see `docs/research_rationale.md` §3 — but reframes the question from "did AI disrupt prices" to "how did the market adapt")
- Validate the researcher-assigned substitutability scores against external data (task-survey instruments or LLM capability benchmarks) instead of a priori judgment
- Use the panel's unused `ai_assisted` / `human_signal` supply-side flags to test whether AI-labeled gigs cluster at the price floor
