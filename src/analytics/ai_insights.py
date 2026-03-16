"""
ai_insights.py - Generates strategic AI insights by feeding citation metrics into Gemini.
Transforms raw numbers into actionable marketing intelligence.

Caches results to avoid re-calling the API on every dashboard refresh.
"""

import sys
import os
import json
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google import genai

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.analytics.metrics import brand_summary, category_breakdown, get_citations_dataframe

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.1-pro-preview"

# Simple file-based cache
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cache")


def _get_cache_path(cache_key):
    """Get the file path for a cache entry."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{cache_key}.json")


def _read_cache(cache_key, max_age_hours=6):
    """Read from cache if entry exists and is fresh enough."""
    path = _get_cache_path(cache_key)
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        cached = json.load(f)

    cached_time = datetime.fromisoformat(cached["timestamp"])
    if datetime.now() - cached_time > timedelta(hours=max_age_hours):
        return None  # Cache expired

    return cached["content"]


def _write_cache(cache_key, content):
    """Write content to cache."""
    path = _get_cache_path(cache_key)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "content": content
        }, f)


def generate_insights(force_refresh=False):
    """
    Generate AI-powered strategic insights from citation data.
    Results are cached for 6 hours to avoid unnecessary API calls.
    """
    # Check cache first
    cache_key = "strategic_insights"
    if not force_refresh:
        cached = _read_cache(cache_key)
        if cached:
            print("Using cached insights (less than 6 hours old)")
            return cached

    # Load data
    df = get_citations_dataframe()
    if df.empty:
        return "No citation data available. Run the pipeline first."

    summary = brand_summary(df)
    categories = category_breakdown(df)

    # Build the prompt with structured data
    summary_text = summary.to_string(index=False)
    category_text = categories.to_string(index=False)

    prompt = f"""You are a senior AI SEO strategist analyzing how AI search engines recommend CRM brands.

Based on this citation data collected from AI platforms (Perplexity, Gemini):

BRAND SUMMARY:
{summary_text}

CATEGORY BREAKDOWN (which brands appear for which prompt types):
{category_text}

Provide a strategic analysis with exactly these 4 sections:

1. **Market Leaders in AI Visibility** — Which brands dominate AI recommendations and why? What patterns explain their dominance?

2. **Biggest Opportunities** — Which brands are underrepresented? Where are the gaps that a brand could exploit?

3. **Platform Behavior Patterns** — Do different AI platforms favor different brands? What content types get cited most?

4. **Recommended Actions** — For a brand wanting to improve their AI citation rate, what are the top 3 concrete actions they should take?

Keep each section to 3-4 sentences. Be specific, use numbers from the data, and focus on actionable insights."""

    # Call Gemini
    try:
        if not GEMINI_API_KEY:
            return "GEMINI_API_KEY not configured. Add it to .env to enable AI insights."

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        if response and response.text:
            _write_cache(cache_key, response.text)
            return response.text
        else:
            return "Gemini returned an empty response."

    except Exception as e:
        return f"Error generating insights: {e}"


# ----- Run directly to test -----
if __name__ == "__main__":
    print("=" * 60)
    print("AI INSIGHTS GENERATOR - TEST")
    print(f"Using {MODEL_NAME}")
    print("=" * 60)
    print()

    insights = generate_insights(force_refresh=True)
    print(insights)
