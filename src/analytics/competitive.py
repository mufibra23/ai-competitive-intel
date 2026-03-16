"""
competitive.py - Competitive analysis functions for head-to-head comparison,
gap analysis, and trend detection.

Used by the dashboard for the "Head-to-Head" and "Source Intelligence" tabs.
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.database import get_all_citations


def get_citations_dataframe():
    """Load all citations into a pandas DataFrame."""
    citations = get_all_citations()
    if not citations:
        return pd.DataFrame()
    return pd.DataFrame(citations)


def head_to_head(df, brand_a, brand_b):
    """
    Compare two brands across all metrics.
    Returns a dict with comparison data for each dimension.
    """
    if df.empty:
        return {}

    results = {}

    for brand in [brand_a, brand_b]:
        brand_df = df[df["brand_mentioned"] == brand]
        total = len(brand_df)
        results[brand] = {
            "total_citations": total,
            "avg_position": brand_df["position"].mean() if total > 0 else None,
            "positive_pct": (len(brand_df[brand_df["sentiment"] == "positive"]) / total * 100) if total > 0 else 0,
            "negative_pct": (len(brand_df[brand_df["sentiment"] == "negative"]) / total * 100) if total > 0 else 0,
            "platforms": brand_df["platform"].nunique() if total > 0 else 0,
            "categories": brand_df["category"].unique().tolist() if total > 0 else [],
        }

    # Which prompts mention one but not the other
    prompts_a = set(df[df["brand_mentioned"] == brand_a]["prompt_text"].unique())
    prompts_b = set(df[df["brand_mentioned"] == brand_b]["prompt_text"].unique())

    results["only_a"] = list(prompts_a - prompts_b)  # brand_a appears but not brand_b
    results["only_b"] = list(prompts_b - prompts_a)  # brand_b appears but not brand_a
    results["both"] = list(prompts_a & prompts_b)     # both appear

    return results


def gap_analysis(df, target_brand):
    """
    Find prompts where the target brand does NOT appear but competitors do.
    These represent opportunities for the target brand.
    """
    if df.empty:
        return pd.DataFrame()

    all_prompts = df["prompt_text"].unique()
    brand_prompts = set(df[df["brand_mentioned"] == target_brand]["prompt_text"].unique())

    gaps = []
    for prompt in all_prompts:
        if prompt not in brand_prompts:
            # Which brands DO appear for this prompt?
            prompt_brands = df[df["prompt_text"] == prompt]["brand_mentioned"].unique().tolist()
            category = df[df["prompt_text"] == prompt]["category"].iloc[0]
            gaps.append({
                "prompt_text": prompt,
                "category": category,
                "competitors_present": prompt_brands,
                "competitor_count": len(prompt_brands),
            })

    return pd.DataFrame(gaps).sort_values("competitor_count", ascending=False) if gaps else pd.DataFrame()


def category_heatmap_data(df):
    """
    Create a matrix of brands x prompt categories showing mention counts.
    Perfect for rendering as a heatmap in the dashboard.
    """
    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby(["brand_mentioned", "category"])
        .size()
        .unstack(fill_value=0)
    )


def source_domain_analysis(df):
    """
    Analyze which source domains AI platforms cite most in this niche.
    Tells clients: "You need to get featured on these sites."
    """
    if df.empty:
        return pd.DataFrame()

    sources = df[df["source_url"].notna()].copy()
    if sources.empty:
        return pd.DataFrame()

    sources["domain"] = sources["source_url"].str.extract(r"https?://(?:www\.)?([^/]+)")

    domain_stats = (
        sources.groupby("domain")
        .agg(
            citation_count=("domain", "size"),
            brands_cited=("brand_mentioned", lambda x: list(x.unique())),
            platforms=("platform", lambda x: list(x.unique())),
        )
        .reset_index()
        .sort_values("citation_count", ascending=False)
    )

    return domain_stats


def trend_over_time(df):
    """
    Track citation counts over time (by collection date).
    Works with both real data (actual dates) and sample data (simulated dates).
    """
    if df.empty or "collected_at" not in df.columns:
        return pd.DataFrame()

    df_copy = df.copy()
    df_copy["date"] = pd.to_datetime(df_copy["collected_at"]).dt.date

    return (
        df_copy.groupby(["date", "brand_mentioned"])
        .size()
        .reset_index(name="citations")
        .sort_values("date")
    )


# ----- Run directly to test -----
if __name__ == "__main__":
    print("=" * 60)
    print("COMPETITIVE ANALYSIS - TEST")
    print("=" * 60)
    print()

    df = get_citations_dataframe()
    if df.empty:
        print("No data! Run `python src/pipeline.py` first.")
        sys.exit(1)

    brands = df["brand_mentioned"].unique().tolist()
    print(f"Brands in dataset: {brands}")
    print()

    # Head-to-head: HubSpot vs Attio
    if "HubSpot" in brands and "Attio" in brands:
        print("--- Head-to-Head: HubSpot vs Attio ---")
        h2h = head_to_head(df, "HubSpot", "Attio")
        for brand in ["HubSpot", "Attio"]:
            stats = h2h[brand]
            print(f"  {brand}:")
            print(f"    Citations: {stats['total_citations']}")
            print(f"    Avg Position: {stats['avg_position']:.1f}" if stats['avg_position'] else "    Avg Position: N/A")
            print(f"    Positive: {stats['positive_pct']:.0f}%")
            print(f"    Platforms: {stats['platforms']}")

        print(f"\n  Prompts where only HubSpot appears: {len(h2h['only_a'])}")
        print(f"  Prompts where only Attio appears: {len(h2h['only_b'])}")
        print(f"  Prompts where both appear: {len(h2h['both'])}")

    # Gap analysis for Attio
    if "Attio" in brands:
        print()
        print("--- Gap Analysis: Attio ---")
        print("(Prompts where Attio is MISSING but competitors appear)")
        gaps = gap_analysis(df, "Attio")
        if not gaps.empty:
            for _, row in gaps.head(5).iterrows():
                print(f"  [{row['category']}] {row['prompt_text'][:60]}...")
                print(f"    Competitors: {', '.join(row['competitors_present'][:3])}")
        else:
            print("  No gaps found - Attio appears everywhere!")

    # Category heatmap
    print()
    print("--- Category Heatmap ---")
    heatmap = category_heatmap_data(df)
    if not heatmap.empty:
        print(heatmap.to_string())

    # Source domains
    print()
    print("--- Top Source Domains ---")
    sources = source_domain_analysis(df)
    if not sources.empty:
        for _, row in sources.head(5).iterrows():
            print(f"  {row['domain']:30s} cited {row['citation_count']}x")
