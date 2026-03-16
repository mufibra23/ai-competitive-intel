"""
gemini_collector.py - Queries Google Gemini API to get AI-generated responses about CRM brands.
Uses the same prompts as Firecrawl but gets Gemini's perspective directly via API.

Uses the new google-genai package (the old google-generativeai is deprecated).
Model: gemini-3.1-pro-preview (latest as of March 2026).
Free tier: 15 requests/min via AI Studio. Plenty for our use case.
"""

import os
import time
from dotenv import load_dotenv
from google import genai

# Load API key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = "gemini-3.1-pro-preview"


def get_gemini_client():
    """Initialize the Gemini client."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file")
    return genai.Client(api_key=GEMINI_API_KEY)


def query_gemini(prompt_text, delay=2):
    """
    Send a prompt to Gemini and return the response.

    Args:
        prompt_text: The buyer-style question to ask
        delay: Seconds to wait between requests (respect rate limits)

    Returns:
        dict with 'text' (response) and 'metadata', or None on failure
    """
    client = get_gemini_client()

    # Add context to get more detailed, citation-rich responses
    system_context = (
        "You are a helpful software advisor. When recommending tools, "
        "always mention specific product names, explain their key strengths "
        "and weaknesses, mention pricing tiers, and cite specific features. "
        "Compare multiple options when relevant."
    )

    full_prompt = f"{system_context}\n\nUser question: {prompt_text}"

    try:
        print(f"  Querying Gemini: {prompt_text[:60]}...")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt
        )

        # Respect rate limits
        time.sleep(delay)

        if response and response.text:
            return {
                "text": response.text,
                "metadata": {
                    "model": MODEL_NAME,
                    "source": "gemini_api"
                }
            }
        else:
            print(f"  Warning: Empty response for: {prompt_text[:40]}")
            return None

    except Exception as e:
        print(f"  Error querying Gemini: {e}")
        return None


def query_batch(prompts, max_prompts=None):
    """
    Query Gemini with multiple prompts. No credit limit since Gemini free tier is generous.

    Args:
        prompts: List of dicts with 'id', 'prompt_text', 'category'
        max_prompts: Max number to query (None = all prompts)

    Returns:
        List of dicts with prompt info + Gemini response
    """
    results = []
    prompts_to_query = prompts[:max_prompts] if max_prompts else prompts

    print(f"\n--- Gemini Collector ---")
    print(f"Querying {len(prompts_to_query)} prompts via Gemini API ({MODEL_NAME})")
    print()

    for i, prompt in enumerate(prompts_to_query):
        print(f"[{i+1}/{len(prompts_to_query)}]", end="")

        response = query_gemini(prompt["prompt_text"])

        results.append({
            "prompt_id": prompt["id"],
            "prompt_text": prompt["prompt_text"],
            "category": prompt["category"],
            "platform": "gemini",
            "response": response
        })

    success = sum(1 for r in results if r["response"] is not None)
    failed = len(results) - success
    print(f"\nDone: {success} successful, {failed} failed")

    return results


# ----- Run this file directly to test with 1 prompt -----
if __name__ == "__main__":
    print("=" * 60)
    print(f"GEMINI COLLECTOR - TEST RUN ({MODEL_NAME})")
    print("This uses the free Gemini API (no credits consumed).")
    print("=" * 60)
    print()

    test_prompt = "What is the best CRM for small businesses in 2026?"
    print(f"Test prompt: {test_prompt}")
    print()

    result = query_gemini(test_prompt)

    if result:
        text = result["text"]
        print(f"SUCCESS! Got {len(text)} characters of response.")
        print()
        print("--- First 800 characters of response ---")
        print(text[:800])
        if len(text) > 800:
            print(f"\n... ({len(text) - 800} more characters)")
    else:
        print("FAILED - No response received.")
        print("Check your GEMINI_API_KEY in .env")
