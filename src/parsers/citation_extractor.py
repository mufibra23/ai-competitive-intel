"""
citation_extractor.py - Parses raw AI responses to extract brand citations.
Finds brand mentions, their position in the response, sentiment, source URLs, and context.

This is the core intelligence of the project - turning messy AI text into structured data.
"""

import os
import re
import json


# Load brands from config
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "brands.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    BRANDS_CONFIG = json.load(f)

# Build lookup: all aliases map to canonical brand name
BRAND_ALIASES = {}
for brand in BRANDS_CONFIG["brands"]:
    canonical = brand["name"]
    BRAND_ALIASES[canonical.lower()] = canonical
    for alias in brand.get("aliases", []):
        BRAND_ALIASES[alias.lower()] = canonical

# Sentiment keywords
POSITIVE_KEYWORDS = [
    "best", "top", "excellent", "outstanding", "leading", "recommended",
    "popular", "powerful", "strong", "great", "favorite", "preferred",
    "ideal", "perfect", "impressive", "robust", "intuitive", "seamless",
    "highly rated", "top-rated", "standout", "winner", "gold standard",
]

NEGATIVE_KEYWORDS = [
    "expensive", "costly", "complex", "steep learning curve", "overwhelming",
    "limited", "lacks", "missing", "weak", "difficult", "confusing",
    "overkill", "pricey", "clunky", "outdated", "frustrating", "slow",
    "overpriced", "bloated", "restrictive",
]


def extract_citations(response_text, platform="unknown"):
    """
    Extract brand citations from a raw AI response.
    
    Args:
        response_text: Raw text/markdown from an AI platform
        platform: Which platform generated this response
    
    Returns:
        List of citation dicts with: brand_mentioned, position, source_url, sentiment, context_snippet
    """
    if not response_text:
        return []
    
    text_lower = response_text.lower()
    citations = []
    seen_brands = set()
    position_counter = 0
    
    # Split into sentences for context extraction
    sentences = re.split(r'[.!?\n]+', response_text)
    
    # Find each brand mention
    for alias, canonical_name in BRAND_ALIASES.items():
        if canonical_name in seen_brands:
            continue
        
        # Search for the alias in the response (word boundary matching)
        pattern = re.compile(r'\b' + re.escape(alias) + r'\b', re.IGNORECASE)
        match = pattern.search(response_text)
        
        if match:
            seen_brands.add(canonical_name)
            position_counter += 1
            
            # Find the sentence containing the brand mention for context
            context = _find_context(sentences, canonical_name, alias)
            
            # Determine sentiment from the surrounding context
            sentiment = _analyze_sentiment(context)
            
            # Extract any URLs near the mention
            source_url = _find_nearby_url(response_text, match.start())
            
            citations.append({
                "brand_mentioned": canonical_name,
                "position": position_counter,
                "source_url": source_url,
                "sentiment": sentiment,
                "context_snippet": context[:200] if context else None,
            })
    
    return citations


def _find_context(sentences, brand_name, alias):
    """Find the sentence(s) that contain a brand mention."""
    for sentence in sentences:
        if brand_name.lower() in sentence.lower() or alias.lower() in sentence.lower():
            cleaned = sentence.strip()
            # Remove markdown formatting for clean context
            cleaned = re.sub(r'[*#\[\]`]', '', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            if len(cleaned) > 20:  # Skip tiny fragments
                return cleaned
    return None


def _analyze_sentiment(context):
    """Simple keyword-based sentiment analysis on the context around a brand mention."""
    if not context:
        return "neutral"
    
    context_lower = context.lower()
    
    positive_score = sum(1 for kw in POSITIVE_KEYWORDS if kw in context_lower)
    negative_score = sum(1 for kw in NEGATIVE_KEYWORDS if kw in context_lower)
    
    if positive_score > negative_score:
        return "positive"
    elif negative_score > positive_score:
        return "negative"
    else:
        return "neutral"


def _find_nearby_url(text, mention_position, window=500):
    """Find the closest URL near a brand mention."""
    # Look in a window around the mention
    start = max(0, mention_position - window)
    end = min(len(text), mention_position + window)
    nearby_text = text[start:end]
    
    # Find URLs
    url_pattern = re.compile(r'https?://[^\s\)>\]]+')
    urls = url_pattern.findall(nearby_text)
    
    return urls[0] if urls else None


# ----- Run directly to test with real data -----
if __name__ == "__main__":
    print("=" * 60)
    print("CITATION EXTRACTOR - TEST")
    print("=" * 60)
    print()
    
    # Test with a sample Perplexity-style response
    sample_perplexity = """
    # What is the best CRM for small businesses in 2026?
    
    There is no single "best" CRM for every small business in 2026; the right choice depends 
    on budget, team size, and how much you value marketing features vs. simple sales pipelines.
    
    ## Quick picks by scenario
    - Very small / solo, lowest cost, simple setup: **Bigin by Zoho** or **Less Annoying CRM**.
    - Free starter with marketing tools: **HubSpot CRM** (strong free tier, but upgrades can get expensive).
    - Best for sales pipeline management: **Pipedrive** is the most intuitive option.
    - Modern and fast-growing: **Attio** is the recommended choice for startups that want a fresh approach.
    - Enterprise-ready: **Salesforce** remains the most powerful but has a steep learning curve.
    - Budget-friendly all-in-one: **Freshsales** by Freshworks offers great value.
    - Best for outbound sales: **Close** is popular with inside sales teams.
    
    Sources: https://www.g2.com/categories/crm https://www.forbes.com/advisor/crm/
    """
    
    # Test with Gemini-style response
    sample_gemini = """
    Welcome to 2026! The CRM landscape for small businesses has evolved significantly.
    
    Here is a comparison of the top CRMs for small businesses:
    
    1. HubSpot CRM (Best for All-in-One Sales & Marketing)
    HubSpot remains the gold standard for small businesses that want a unified platform.
    The free tier is excellent, but paid plans can be costly as you grow.
    
    2. Zoho CRM (Best Value for Money)
    Zoho CRM offers outstanding value with comprehensive features at lower price points.
    
    3. Pipedrive (Best for Pure Sales Teams)
    Pipedrive is the most intuitive sales CRM with a powerful visual pipeline.
    
    4. Attio (Best for Modern Startups)
    Attio is a rising star, highly recommended for teams that want a clean, flexible CRM.
    """
    
    print("--- Testing with Perplexity-style response ---")
    citations_p = extract_citations(sample_perplexity, platform="perplexity")
    print(f"Found {len(citations_p)} brand citations:")
    for c in citations_p:
        print(f"  #{c['position']} {c['brand_mentioned']:15s} | {c['sentiment']:8s} | {c['context_snippet'][:70] if c['context_snippet'] else 'N/A'}...")
    
    print()
    print("--- Testing with Gemini-style response ---")
    citations_g = extract_citations(sample_gemini, platform="gemini")
    print(f"Found {len(citations_g)} brand citations:")
    for c in citations_g:
        print(f"  #{c['position']} {c['brand_mentioned']:15s} | {c['sentiment']:8s} | {c['context_snippet'][:70] if c['context_snippet'] else 'N/A'}...")
