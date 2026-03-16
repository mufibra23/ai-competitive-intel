"""
firecrawl_collector.py - Scrapes AI search platforms (Perplexity) using Firecrawl API.
Returns clean markdown responses that we can parse for brand citations.

Free tier: 500 credits (1 credit = 1 page). Be conservative!
"""

import os
import time
from dotenv import load_dotenv
from firecrawl import Firecrawl

# Load API key from .env
load_dotenv()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")


def get_firecrawl_client():
    """Initialize the Firecrawl client."""
    if not FIRECRAWL_API_KEY:
        raise ValueError("FIRECRAWL_API_KEY not found in .env file")
    return Firecrawl(api_key=FIRECRAWL_API_KEY)


def scrape_perplexity(prompt_text, delay=3):
    """
    Send a prompt to Perplexity via Firecrawl and return the markdown response.
    
    Args:
        prompt_text: The buyer-style question to search
        delay: Seconds to wait between requests (be nice to free tier)
    
    Returns:
        dict with 'markdown' (response text) and 'metadata' (page info), or None on failure
    """
    client = get_firecrawl_client()
    
    # Build the Perplexity search URL from the prompt
    query = prompt_text.replace(" ", "+")
    url = f"https://www.perplexity.ai/search?q={query}"
    
    try:
        print(f"  Scraping: {prompt_text[:60]}...")
        result = client.scrape(url, formats=["markdown"])
        
        # Respect rate limits
        time.sleep(delay)
        
        if result and result.markdown:
            return {
                "markdown": result.markdown,
                "metadata": {
                    "title": getattr(result, 'title', ''),
                    "url": url,
                    "source": "perplexity_via_firecrawl"
                }
            }
        else:
            print(f"  Warning: Empty response for: {prompt_text[:40]}")
            return None
            
    except Exception as e:
        print(f"  Error scraping: {e}")
        return None


def scrape_batch(prompts, max_prompts=5):
    """
    Scrape multiple prompts from Perplexity. Limits to max_prompts to conserve credits.
    
    Args:
        prompts: List of dicts with 'id', 'prompt_text', 'category'
        max_prompts: Max number to scrape (default 5 to conserve free credits)
    
    Returns:
        List of dicts with prompt info + scraped response
    """
    results = []
    prompts_to_scrape = prompts[:max_prompts]
    
    print(f"\n--- Firecrawl Collector ---")
    print(f"Scraping {len(prompts_to_scrape)} of {len(prompts)} prompts (conserving credits)")
    print(f"Estimated credits used: {len(prompts_to_scrape)}")
    print()
    
    for i, prompt in enumerate(prompts_to_scrape):
        print(f"[{i+1}/{len(prompts_to_scrape)}]", end="")
        
        response = scrape_perplexity(prompt["prompt_text"])
        
        results.append({
            "prompt_id": prompt["id"],
            "prompt_text": prompt["prompt_text"],
            "category": prompt["category"],
            "platform": "perplexity",
            "response": response
        })
    
    success = sum(1 for r in results if r["response"] is not None)
    failed = len(results) - success
    print(f"\nDone: {success} successful, {failed} failed")
    
    return results


# ----- Run this file directly to test with 1 prompt -----
if __name__ == "__main__":
    print("=" * 60)
    print("FIRECRAWL COLLECTOR - TEST RUN")
    print("This will use 1 Firecrawl credit to test the connection.")
    print("=" * 60)
    print()
    
    test_prompt = "What is the best CRM for small businesses in 2026?"
    print(f"Test prompt: {test_prompt}")
    print()
    
    result = scrape_perplexity(test_prompt)
    
    if result:
        markdown = result["markdown"]
        print(f"SUCCESS! Got {len(markdown)} characters of markdown.")
        print()
        print("--- First 500 characters of response ---")
        print(markdown[:500])
        print()
        print("--- Last 300 characters of response ---")
        print(markdown[-300:])
    else:
        print("FAILED - No response received.")
        print("Check your FIRECRAWL_API_KEY in .env")
