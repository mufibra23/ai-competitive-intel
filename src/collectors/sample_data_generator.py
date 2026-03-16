"""
sample_data_generator.py - Generates realistic sample citation data for development and demos.
Based on real-world CRM market patterns so the dashboard looks credible.

Use this instead of burning Firecrawl credits during development.
All sample data is clearly labeled as simulated.
"""

import os
import json
import random
from datetime import datetime, timedelta


# Load brands from config
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "brands.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    BRANDS_CONFIG = json.load(f)

BRAND_NAMES = [b["name"] for b in BRANDS_CONFIG["brands"]]

# Realistic citation patterns based on actual AI search behavior
# HubSpot and Salesforce dominate, Attio appears in startup contexts, etc.
BRAND_WEIGHTS = {
    "HubSpot": 0.30,       # Market leader, appears in most responses
    "Salesforce": 0.22,     # Enterprise giant, strong but less SMB-focused
    "Zoho CRM": 0.15,       # Strong value play, popular internationally
    "Pipedrive": 0.12,      # Sales-focused, appears in pipeline questions
    "Attio": 0.08,          # Rising challenger, appears in startup/modern contexts
    "Freshsales": 0.07,     # Budget-friendly, appears in pricing questions
    "Close": 0.06,          # Niche for outbound sales teams
}

# Which brands appear for which prompt categories
CATEGORY_BRAND_AFFINITY = {
    "general_recommendation": ["HubSpot", "Salesforce", "Zoho CRM", "Pipedrive", "Freshsales"],
    "comparison": ["HubSpot", "Salesforce", "Pipedrive", "Attio", "Zoho CRM", "Close"],
    "use_case_specific": ["HubSpot", "Pipedrive", "Attio", "Close", "Zoho CRM"],
    "pricing_value": ["HubSpot", "Zoho CRM", "Freshsales", "Pipedrive", "Attio"],
    "feature_specific": ["HubSpot", "Salesforce", "Pipedrive", "Attio", "Zoho CRM", "Close"],
}

# Realistic source URLs that AI platforms commonly cite
SAMPLE_SOURCES = [
    "https://www.g2.com/categories/crm",
    "https://www.capterra.com/customer-relationship-management-software/",
    "https://www.pcmag.com/picks/the-best-crm-software",
    "https://www.forbes.com/advisor/business/software/best-crm-small-business/",
    "https://www.techradar.com/best/best-crm-software",
    "https://blog.hubspot.com/sales/best-crm",
    "https://www.reddit.com/r/smallbusiness/comments/best_crm/",
    "https://www.reddit.com/r/SaaS/comments/crm_recommendations/",
    "https://zapier.com/blog/best-crm/",
    "https://www.trustradius.com/crm",
    "https://www.getapp.com/customer-management-software/crm/",
    None,  # Some citations don't have source URLs
    None,
]

# Sentiment keywords for context snippets
POSITIVE_CONTEXTS = [
    "{brand} is widely regarded as the best option for {context}",
    "{brand} stands out with its {feature} capabilities",
    "Many small businesses prefer {brand} for its {feature}",
    "{brand} offers excellent {feature} that makes it a top choice",
    "For {context}, {brand} is the most recommended solution",
    "{brand} leads the market with its {feature} features",
]

NEUTRAL_CONTEXTS = [
    "{brand} is a popular choice for {context}",
    "{brand} provides {feature} functionality",
    "You might also consider {brand} for {context}",
    "{brand} offers {feature} as part of its platform",
    "Another option worth exploring is {brand}",
]

NEGATIVE_CONTEXTS = [
    "{brand} can be expensive for small teams, especially as you scale",
    "While {brand} is powerful, the learning curve can be steep",
    "Some users find {brand} overwhelming for basic CRM needs",
    "{brand} may be overkill if you only need simple contact management",
]

FEATURES = [
    "sales pipeline management", "email automation", "contact management",
    "reporting and analytics", "lead scoring", "workflow automation",
    "integration ecosystem", "free tier", "mobile app", "AI-powered insights",
    "customizable dashboards", "team collaboration", "deal tracking",
]

CONTEXTS = [
    "small businesses", "startups", "sales teams", "marketing agencies",
    "freelancers", "B2B companies", "remote teams", "growing businesses",
    "solopreneurs", "small teams under 20 people",
]


def generate_sample_response(prompt_text, category, platform="sample"):
    """Generate a realistic-looking AI response for a given prompt."""
    # Pick 3-6 brands to mention, weighted by category affinity
    available_brands = CATEGORY_BRAND_AFFINITY.get(category, BRAND_NAMES)
    num_brands = random.randint(3, min(6, len(available_brands)))
    
    # Weight selection toward market leaders
    weights = [BRAND_WEIGHTS.get(b, 0.05) for b in available_brands]
    total = sum(weights)
    weights = [w / total for w in weights]
    
    mentioned_brands = []
    remaining = list(available_brands)
    remaining_weights = list(weights)
    
    for _ in range(num_brands):
        if not remaining:
            break
        total = sum(remaining_weights)
        if total == 0:
            break
        normalized = [w / total for w in remaining_weights]
        chosen = random.choices(remaining, weights=normalized, k=1)[0]
        mentioned_brands.append(chosen)
        idx = remaining.index(chosen)
        remaining.pop(idx)
        remaining_weights.pop(idx)
    
    # Build a fake response text
    lines = [f"# {prompt_text}\n"]
    lines.append(f"Here are the top CRM recommendations for your needs:\n")
    
    for i, brand in enumerate(mentioned_brands):
        feature = random.choice(FEATURES)
        context = random.choice(CONTEXTS)
        
        if i == 0:
            template = random.choice(POSITIVE_CONTEXTS)
        elif i < 3:
            template = random.choice(POSITIVE_CONTEXTS + NEUTRAL_CONTEXTS)
        else:
            template = random.choice(NEUTRAL_CONTEXTS + NEGATIVE_CONTEXTS)
        
        snippet = template.format(brand=brand, feature=feature, context=context)
        lines.append(f"{i+1}. **{brand}** - {snippet}\n")
    
    lines.append(f"\n[SAMPLE DATA - Generated for demo purposes]")
    
    return {
        "text": "\n".join(lines),
        "brands_mentioned": mentioned_brands,
        "metadata": {
            "source": f"sample_data_{platform}",
            "generated_at": datetime.now().isoformat()
        }
    }


def generate_citation_data(prompt_id, prompt_text, category, platform="perplexity"):
    """Generate realistic citation records for a single prompt."""
    response = generate_sample_response(prompt_text, category, platform)
    citations = []
    
    for position, brand in enumerate(response["brands_mentioned"], start=1):
        # Determine sentiment based on position
        if position <= 2:
            sentiment = "positive"
        elif position <= 4:
            sentiment = random.choice(["positive", "neutral"])
        else:
            sentiment = random.choice(["neutral", "negative"])
        
        feature = random.choice(FEATURES)
        context = random.choice(CONTEXTS)
        
        # Pick context template based on sentiment
        if sentiment == "positive":
            template = random.choice(POSITIVE_CONTEXTS)
        elif sentiment == "negative":
            template = random.choice(NEGATIVE_CONTEXTS)
        else:
            template = random.choice(NEUTRAL_CONTEXTS)
        
        snippet = template.format(brand=brand, feature=feature, context=context)
        
        citations.append({
            "brand_mentioned": brand,
            "position": position,
            "source_url": random.choice(SAMPLE_SOURCES),
            "sentiment": sentiment,
            "context_snippet": snippet,
        })
    
    return {
        "prompt_id": prompt_id,
        "prompt_text": prompt_text,
        "category": category,
        "platform": f"sample_{platform}",
        "raw_response": response["text"],
        "citations": citations,
    }


def generate_full_dataset(prompts, platforms=None, num_runs=3):
    """
    Generate a complete sample dataset across multiple platforms and simulated runs.
    
    Args:
        prompts: List of dicts with 'id', 'prompt_text', 'category'
        platforms: List of platform names to simulate (default: perplexity + gemini)
        num_runs: Number of collection runs to simulate (for trend data)
    
    Returns:
        List of result dicts ready to be stored in the database
    """
    if platforms is None:
        platforms = ["perplexity", "gemini"]
    
    all_results = []
    
    print(f"\n--- Sample Data Generator ---")
    print(f"Generating data for {len(prompts)} prompts x {len(platforms)} platforms x {num_runs} runs")
    print()
    
    for run in range(num_runs):
        run_date = datetime.now() - timedelta(days=(num_runs - 1 - run) * 3)
        
        for platform in platforms:
            for prompt in prompts:
                result = generate_citation_data(
                    prompt["id"],
                    prompt["prompt_text"],
                    prompt["category"],
                    platform
                )
                result["run_date"] = run_date.isoformat()
                all_results.append(result)
        
        print(f"  Run {run+1}/{num_runs} ({run_date.strftime('%Y-%m-%d')}): {len(prompts) * len(platforms)} responses generated")
    
    total_citations = sum(len(r["citations"]) for r in all_results)
    print(f"\nTotal: {len(all_results)} responses, {total_citations} citations generated")
    
    return all_results


# ----- Run directly to test -----
if __name__ == "__main__":
    print("=" * 60)
    print("SAMPLE DATA GENERATOR - TEST")
    print("=" * 60)
    print()
    
    # Load prompts from config
    prompts_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "prompts.json")
    with open(prompts_path, "r", encoding="utf-8") as f:
        prompts_config = json.load(f)
    
    prompts = [{"id": p["id"], "prompt_text": p["text"], "category": p["category"]} for p in prompts_config["prompts"]]
    
    # Generate for just 3 prompts as a test
    test_prompts = prompts[:3]
    results = generate_full_dataset(test_prompts, num_runs=2)
    
    # Show a sample
    print()
    print("--- Sample result ---")
    sample = results[0]
    print(f"Prompt: {sample['prompt_text']}")
    print(f"Platform: {sample['platform']}")
    print(f"Citations found: {len(sample['citations'])}")
    for c in sample["citations"]:
        print(f"  #{c['position']} {c['brand_mentioned']} ({c['sentiment']}) - {c['context_snippet'][:60]}...")
