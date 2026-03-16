"""
metrics.py - Calculates competitive intelligence metrics from citation data.

Core metrics:
  - Citation Frequency: raw count of mentions per brand
  - Share of Voice: brand citations / total citations (%)
  - Citation Quality Score: weighted by position (1st mention = 3x, top 3 = 2x, rest = 1x)
  - Platform Coverage: how many AI platforms mention the brand (0-100%)
  - Sentiment Score: (positive - negative) / total mentions (-1 to +1)
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.database import get_all_citations, get_connection


def get_citations_dataframe():
    """Load all citations into a pandas DataFrame."""
    citations = get_all_citations()
    if not citations:
        print("No citations found in database. Run the pipeline first.")
        return pd.DataFrame()
    return pd.DataFrame(citations)


def citation_frequency(df):
    """Count total mentions per brand."""
    if df.empty:
        return pd.DataFrame()
    return (
        df.groupby("brand_mentioned")
        .size()
        .reset_index(name="citation_count")
        .sort_values("citation_count", ascending=False)
    )


def share_of_voice(df):
    """Calculate each brand's share of total citations as a percentage."""
    if df.empty:
        return pd.DataFrame()
    freq = citation_frequency(df)
    total = freq["citation_count"].sum()
    freq["share_of_voice"] = (freq["citation_count"] / total * 100).round(2)
    return freq


def citation_quality_score(df):
    """
    Weighted citation score based on position in the response.
    Position 1 (first mentioned) = 3 points
    Position 2-3 = 2 points
    Position 4+ = 1 point
    """
    if df.empty:
        return pd.DataFrame()

    def position_weight(pos):
        if pos == 1:
            return 3
        elif pos <= 3:
            return 2
        else:
            return 1

    df_copy = df.copy()
    df_copy["quality_points"] = df_copy["position"].apply(
        lambda p: position_weight(p) if pd.notna(p) else 1
    )

    quality = (
        df_copy.groupby("brand_mentioned")
        .agg(
            total_citations=("quality_points", "count"),
            quality_score=("quality_points", "sum"),
        )
        .reset_index()
        .sort_values("quality_score", ascending=False)
    )

    # Normalize to 0-100 scale
    max_score = quality["quality_score"].max()
    if max_score > 0:
        quality["quality_normalized"] = (quality["quality_score"] / max_score * 100).round(1)
    else:
        quality["quality_normalized"] = 0

    return quality


def platform_coverage(df):
    """
    How many unique AI platforms mention each brand.
    Score: number of platforms / total platforms (as percentage).
    """
    if df.empty:
        return pd.DataFrame()

    total_platforms = df["platform"].nunique()

    coverage = (
        df.groupby("brand_mentioned")["platform"]
        .nunique()
        .reset_index(name="platforms_present")
    )
    coverage["total_platforms"] = total_platforms
    coverage["coverage_pct"] = (coverage["platforms_present"] / total_platforms * 100).round(1)

    return coverage.sort_values("coverage_pct", ascending=False)


def sentiment_score(df):
    """
    Calculate sentiment score per brand.
    Formula: (positive - negative) / total mentions
    Range: -1.0 (all negative) to +1.0 (all positive)
    """
    if df.empty:
        return pd.DataFrame()

    sentiment_counts = (
        df.groupby(["brand_mentioned", "sentiment"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    # Ensure all sentiment columns exist
    for col in ["positive", "neutral", "negative"]:
        if col not in sentiment_counts.columns:
            sentiment_counts[col] = 0

    sentiment_counts["total"] = (
        sentiment_counts["positive"] + sentiment_counts["neutral"] + sentiment_counts["negative"]
    )
    sentiment_counts["sentiment_score"] = (
        (sentiment_counts["positive"] - sentiment_counts["negative"]) / sentiment_counts["total"]
    ).round(3)

    return sentiment_counts.sort_values("sentiment_score", ascending=False)


def brand_summary(df):
    """
    Combine all metrics into a single summary DataFrame.
    This is what the dashboard primarily uses.
    """
    if df.empty:
        return pd.DataFrame()

    sov = share_of_voice(df)
    quality = citation_quality_score(df)
    coverage = platform_coverage(df)
    sentiment = sentiment_score(df)

    # Merge everything on brand name
    summary = sov.merge(
        quality[["brand_mentioned", "quality_score", "quality_normalized"]],
        on="brand_mentioned", how="left"
    ).merge(
        coverage[["brand_mentioned", "platforms_present", "coverage_pct"]],
        on="brand_mentioned", how="left"
    ).merge(
        sentiment[["brand_mentioned", "positive", "neutral", "negative", "sentiment_score"]],
        on="brand_mentioned", how="left"
    )

    return summary.sort_values("share_of_voice", ascending=False)


def category_breakdown(df):
    """Show which brands dominate which prompt categories."""
    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby(["category", "brand_mentioned"])
        .size()
        .reset_index(name="mentions")
        .sort_values(["category", "mentions"], ascending=[True, False])
    )


def source_analysis(df):
    """Analyze which source URLs/domains are most commonly cited."""
    if df.empty:
        return pd.DataFrame()

    sources = df[df["source_url"].notna()].copy()
    if sources.empty:
        return pd.DataFrame()

    # Extract domain from URL
    sources["domain"] = sources["source_url"].str.extract(r"https?://(?:www\.)?([^/]+)")

    return (
        sources.groupby("domain")
        .size()
        .reset_index(name="citation_count")
        .sort_values("citation_count", ascending=False)
    )


# ----- Run directly to test -----
if __name__ == "__main__":
    print("=" * 60)
    print("METRICS CALCULATOR - TEST")
    print("=" * 60)
    print()

    df = get_citations_dataframe()
    if df.empty:
        print("No data! Run `python src/pipeline.py` first.")
        sys.exit(1)

    print(f"Total citations in database: {len(df)}")
    print(f"Unique brands: {df['brand_mentioned'].nunique()}")
    print(f"Platforms: {df['platform'].unique().tolist()}")
    print()

    print("--- Share of Voice ---")
    sov = share_of_voice(df)
    for _, row in sov.iterrows():
        bar = "█" * int(row["share_of_voice"] / 2)
        print(f"  {row['brand_mentioned']:15s} {row['share_of_voice']:5.1f}% {bar}")

    print()
    print("--- Citation Quality Score ---")
    quality = citation_quality_score(df)
    for _, row in quality.iterrows():
        print(f"  {row['brand_mentioned']:15s} Score: {row['quality_score']:4.0f} ({row['quality_normalized']:.0f}/100)")

    print()
    print("--- Sentiment Score ---")
    sent = sentiment_score(df)
    for _, row in sent.iterrows():
        emoji = "🟢" if row["sentiment_score"] > 0.2 else ("🔴" if row["sentiment_score"] < -0.2 else "🟡")
        print(f"  {emoji} {row['brand_mentioned']:15s} {row['sentiment_score']:+.3f} (pos:{row['positive']:.0f} neu:{row['neutral']:.0f} neg:{row['negative']:.0f})")

    print()
    print("--- Full Brand Summary ---")
    summary = brand_summary(df)
    print(summary.to_string(index=False))
