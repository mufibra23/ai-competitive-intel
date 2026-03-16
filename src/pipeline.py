"""
pipeline.py - Orchestrates the full data collection pipeline.
Flow: Load prompts -> Collect from AI platforms -> Parse citations -> Store in SQLite

Usage:
    python src/pipeline.py                    # Run with sample data (no API credits)
    python src/pipeline.py --live             # Run with real APIs (uses credits)
    python src/pipeline.py --live --max 5     # Run live but limit to 5 prompts
"""

import sys
import os
import argparse
from datetime import datetime

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.database import (
    get_all_prompts, insert_response, insert_citation, insert_run, create_tables, load_prompts_from_config
)
from src.parsers.citation_extractor import extract_citations
from src.collectors.sample_data_generator import generate_full_dataset


def run_sample_pipeline(num_runs=3):
    """Run the pipeline using generated sample data (no API credits used)."""
    print("=" * 60)
    print("PIPELINE - SAMPLE DATA MODE")
    print("No API credits will be used.")
    print("=" * 60)
    print()
    
    # Ensure database and prompts exist
    create_tables()
    load_prompts_from_config()
    
    # Load prompts from database
    prompts = get_all_prompts()
    print(f"Loaded {len(prompts)} prompts from database.\n")
    
    # Generate sample data
    results = generate_full_dataset(prompts, platforms=["perplexity", "gemini"], num_runs=num_runs)
    
    # Store in database
    print(f"\nStoring results in database...")
    total_citations = 0
    
    for platform in ["sample_perplexity", "sample_gemini"]:
        platform_results = [r for r in results if r["platform"] == platform]
        if not platform_results:
            continue
        
        success = sum(1 for r in platform_results if r.get("citations"))
        error = len(platform_results) - success
        run_id = insert_run(platform, len(platform_results), success, error)
        
        for result in platform_results:
            # Store raw response
            response_id = insert_response(
                result["prompt_id"],
                result["platform"],
                result["raw_response"]
            )
            
            # Store citations
            for citation in result.get("citations", []):
                insert_citation(
                    response_id=response_id,
                    brand_mentioned=citation["brand_mentioned"],
                    position=citation.get("position"),
                    source_url=citation.get("source_url"),
                    sentiment=citation.get("sentiment", "neutral"),
                    context_snippet=citation.get("context_snippet"),
                )
                total_citations += 1
    
    print(f"Done! Stored {len(results)} responses and {total_citations} citations.")
    print()
    return total_citations


def run_live_pipeline(max_prompts=5):
    """Run the pipeline with real API calls (uses Firecrawl credits + Gemini API)."""
    print("=" * 60)
    print("PIPELINE - LIVE MODE")
    print(f"Will query up to {max_prompts} prompts per platform.")
    print(f"Firecrawl credits used: ~{max_prompts}")
    print("=" * 60)
    print()
    
    # Ensure database and prompts exist
    create_tables()
    load_prompts_from_config()
    
    # Load prompts
    prompts = get_all_prompts()
    prompts_subset = prompts[:max_prompts]
    print(f"Using {len(prompts_subset)} of {len(prompts)} prompts.\n")
    
    total_citations = 0
    
    # --- Firecrawl (Perplexity) ---
    try:
        from src.collectors.firecrawl_collector import scrape_batch
        
        firecrawl_results = scrape_batch(prompts_subset, max_prompts=max_prompts)
        
        success = sum(1 for r in firecrawl_results if r["response"] is not None)
        error = len(firecrawl_results) - success
        run_id = insert_run("perplexity", len(firecrawl_results), success, error)
        
        for result in firecrawl_results:
            if result["response"] is None:
                continue
            
            raw_text = result["response"]["markdown"]
            response_id = insert_response(result["prompt_id"], "perplexity", raw_text)
            
            # Parse citations from the raw response
            citations = extract_citations(raw_text, platform="perplexity")
            for citation in citations:
                insert_citation(
                    response_id=response_id,
                    brand_mentioned=citation["brand_mentioned"],
                    position=citation.get("position"),
                    source_url=citation.get("source_url"),
                    sentiment=citation.get("sentiment", "neutral"),
                    context_snippet=citation.get("context_snippet"),
                )
                total_citations += 1
        
        print(f"Firecrawl: {success} responses, {total_citations} citations extracted\n")
        
    except Exception as e:
        print(f"Firecrawl collection failed: {e}\n")
    
    # --- Gemini API ---
    gemini_citations = 0
    try:
        from src.collectors.gemini_collector import query_batch
        
        gemini_results = query_batch(prompts_subset, max_prompts=max_prompts)
        
        success = sum(1 for r in gemini_results if r["response"] is not None)
        error = len(gemini_results) - success
        run_id = insert_run("gemini", len(gemini_results), success, error)
        
        for result in gemini_results:
            if result["response"] is None:
                continue
            
            raw_text = result["response"]["text"]
            response_id = insert_response(result["prompt_id"], "gemini", raw_text)
            
            citations = extract_citations(raw_text, platform="gemini")
            for citation in citations:
                insert_citation(
                    response_id=response_id,
                    brand_mentioned=citation["brand_mentioned"],
                    position=citation.get("position"),
                    source_url=citation.get("source_url"),
                    sentiment=citation.get("sentiment", "neutral"),
                    context_snippet=citation.get("context_snippet"),
                )
                gemini_citations += 1
                total_citations += 1
        
        print(f"Gemini: {success} responses, {gemini_citations} citations extracted\n")
        
    except Exception as e:
        print(f"Gemini collection failed: {e}\n")
    
    print(f"Pipeline complete! Total citations stored: {total_citations}")
    return total_citations


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Competitive Intelligence Pipeline")
    parser.add_argument("--live", action="store_true", help="Use real APIs instead of sample data")
    parser.add_argument("--max", type=int, default=5, help="Max prompts per platform in live mode (default: 5)")
    parser.add_argument("--runs", type=int, default=3, help="Number of simulated runs in sample mode (default: 3)")
    args = parser.parse_args()
    
    if args.live:
        run_live_pipeline(max_prompts=args.max)
    else:
        run_sample_pipeline(num_runs=args.runs)
