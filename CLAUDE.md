# OQG x AISA Fiverr Research

Price distribution analysis in AI-disrupted freelance markets.

## Project Context

**Organization:** OQG x AISA Spring 2026  
**Goal:** Analyze how AI tools have shifted price distributions on Fiverr across service categories.

## Directory Structure

```
data/
  snapshots/   # Raw HTML snapshots (gitignored — too large)
  output/      # Generated CSVs (gitignored)
  processed/   # Cleaned, intermediate data (versioned)
scripts/       # Data collection and analysis scripts
notebooks/     # Exploratory analysis
```

## Key Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run scraper
python scripts/scrape.py

# Run analysis
python scripts/analyze.py
```

## Data Notes

- Raw HTML snapshots go in `data/snapshots/` (gitignored)
- Final CSVs go in `data/output/` (gitignored)
- Processed/cleaned data in `data/processed/` is versioned

## Environment Variables

Copy `.env.example` to `.env` and fill in values. Never commit `.env`.
