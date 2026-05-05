"""Add ai_assisted and human_signal boolean keyword flags to full_panel.csv."""

import re
import pandas as pd

INPUT = "data/output/full_panel.csv"
OUTPUT = "data/output/full_panel.csv"

AI_KEYWORDS = [
    r"\bai\b",
    r"artificial intelligence",
    r"chatgpt",
    r"\bgpt\b",
    r"gpt-?4",
    r"openai",
    r"midjourney",
    r"stable diffusion",
    r"dall-?e",
    r"text-to-image",
    r"\bgenerative\b",
    r"ai[- ]generated",
    r"\bgenerated\b",
    r"\bautomated\b",
    r"\bllm\b",
    r"machine learning",
    r"\bprompt\b",
    r"\bclaude\b",
    r"\bgemini\b",
]

HUMAN_KEYWORDS = [
    r"\bhuman\b",
    r"no[- ]ai",
    r"not ai",
    r"without ai",
    r"ai[- ]free",
    r"no artificial",
    r"handcrafted",
    r"hand[- ]drawn",
    r"handwritten",
    r"100\s*%\s*human",
    r"real human",
    r"real person",
    r"guaranteed human",
    r"human[- ]written",
    r"human only",
    r"written by",
    r"\bmanually\b",
    r"\bauthentic\b",
]

AI_PAT = re.compile("|".join(AI_KEYWORDS), re.IGNORECASE)
HUMAN_PAT = re.compile("|".join(HUMAN_KEYWORDS), re.IGNORECASE)


def flag_title(series: pd.Series, pattern: re.Pattern) -> pd.Series:
    return series.fillna("").str.contains(pattern, regex=True)


def freq_table(df: pd.DataFrame, flag: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {flag}  —  frequency by category × year")
    print(f"{'='*60}")
    df["year"] = df["date"].str[:4]
    tbl = (
        df.groupby(["category", "year"])[flag]
        .agg(n_true="sum", n_total="count")
        .assign(pct=lambda x: (x["n_true"] / x["n_total"] * 100).round(1))
    )
    print(tbl.to_string())


def main():
    df = pd.read_csv(INPUT)

    df["ai_assisted"] = flag_title(df["title"], AI_PAT)
    df["human_signal"] = flag_title(df["title"], HUMAN_PAT)

    freq_table(df, "ai_assisted")
    freq_table(df, "human_signal")

    # Totals and spot-checks
    n = len(df)
    for flag in ("ai_assisted", "human_signal"):
        cnt = df[flag].sum()
        print(f"\nTOTAL {flag}: {cnt}/{n} ({cnt/n*100:.2f}%)")
    print("\n--- all ai_assisted titles ---")
    print(df.loc[df["ai_assisted"], ["date", "category", "title"]].drop_duplicates("title").to_string(index=False))
    print("\n--- all human_signal titles ---")
    print(df.loc[df["human_signal"], ["date", "category", "title"]].drop_duplicates("title").to_string(index=False))

    df.drop(columns=["year"], inplace=True)
    df.to_csv(OUTPUT, index=False)
    print(f"\nSaved {OUTPUT}  ({len(df)} rows, columns: {df.columns.tolist()})")


if __name__ == "__main__":
    main()
