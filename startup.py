"""
startup.py - Auto-initializes database and sample data if not present.
Called by app.py on startup to ensure the dashboard always has data to display.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.database import create_tables, load_prompts_from_config, get_all_citations
from src.pipeline import run_sample_pipeline


def ensure_data_exists():
    """Check if database has data. If not, create tables and run sample pipeline."""
    create_tables()
    load_prompts_from_config()
    
    citations = get_all_citations()
    if not citations:
        print("No data found. Generating sample data...")
        run_sample_pipeline(num_runs=3)
        print("Sample data generated successfully.")
    else:
        print(f"Database has {len(citations)} citations. Ready.")


if __name__ == "__main__":
    ensure_data_exists()
