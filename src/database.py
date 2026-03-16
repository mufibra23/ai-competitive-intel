"""
database.py - SQLite database setup and helper functions for AI Competitive Intelligence Monitor.
Creates and manages 4 tables:
  - prompts: stores the buyer-style prompts from config
  - responses: raw AI platform responses
  - citations: extracted brand mentions (the gold - core of the project)
  - runs: logs each pipeline execution for trend tracking
"""

import sqlite3
import json
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "competitive_intel.db")


def get_connection():
    """Get a connection to the SQLite database. Creates the data/ folder if needed."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # So we can access columns by name
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent read performance
    return conn


def create_tables():
    """Create all 4 tables if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1: prompts - the buyer-style questions we send to AI platforms
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_text TEXT NOT NULL,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 2: responses - raw responses from each AI platform
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            raw_response TEXT,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prompt_id) REFERENCES prompts(id)
        )
    """)

    # Table 3: citations - extracted brand mentions from responses (THE GOLD)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS citations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            response_id INTEGER NOT NULL,
            brand_mentioned TEXT NOT NULL,
            position INTEGER,
            source_url TEXT,
            sentiment TEXT DEFAULT 'neutral',
            context_snippet TEXT,
            FOREIGN KEY (response_id) REFERENCES responses(id)
        )
    """)

    # Table 4: runs - logs each pipeline execution for tracking over time
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            platform TEXT,
            prompts_sent INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    print("All 4 tables created successfully.")


def load_prompts_from_config():
    """Load prompts from config/prompts.json into the prompts table (skips duplicates)."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "prompts.json")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    conn = get_connection()
    cursor = conn.cursor()

    loaded = 0
    skipped = 0
    for prompt in config["prompts"]:
        # Check if prompt already exists (avoid duplicates on re-run)
        cursor.execute("SELECT id FROM prompts WHERE prompt_text = ?", (prompt["text"],))
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO prompts (prompt_text, category) VALUES (?, ?)",
                (prompt["text"], prompt["category"])
            )
            loaded += 1
        else:
            skipped += 1

    conn.commit()
    conn.close()
    print(f"Prompts loaded: {loaded} new, {skipped} already existed.")


def insert_run(platform, prompts_sent, success_count, error_count):
    """Log a pipeline run."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO runs (platform, prompts_sent, success_count, error_count) VALUES (?, ?, ?, ?)",
        (platform, prompts_sent, success_count, error_count)
    )
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id


def insert_response(prompt_id, platform, raw_response):
    """Store a raw response from an AI platform."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO responses (prompt_id, platform, raw_response) VALUES (?, ?, ?)",
        (prompt_id, platform, raw_response)
    )
    response_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return response_id


def insert_citation(response_id, brand_mentioned, position=None, source_url=None, sentiment="neutral", context_snippet=None):
    """Store an extracted brand citation."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO citations (response_id, brand_mentioned, position, source_url, sentiment, context_snippet) VALUES (?, ?, ?, ?, ?, ?)",
        (response_id, brand_mentioned, position, source_url, sentiment, context_snippet)
    )
    citation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return citation_id


def get_all_prompts():
    """Fetch all prompts from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, prompt_text, category FROM prompts")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_citations():
    """Fetch all citations with their associated prompt and response info."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            c.id,
            c.brand_mentioned,
            c.position,
            c.source_url,
            c.sentiment,
            c.context_snippet,
            r.platform,
            r.collected_at,
            p.prompt_text,
            p.category
        FROM citations c
        JOIN responses r ON c.response_id = r.id
        JOIN prompts p ON r.prompt_id = p.id
        ORDER BY r.collected_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_runs():
    """Fetch all pipeline runs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM runs ORDER BY run_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ----- Run this file directly to set up the database -----
if __name__ == "__main__":
    print("Setting up database...")
    create_tables()
    print()
    print("Loading prompts from config...")
    load_prompts_from_config()
    print()
    print(f"Database location: {os.path.abspath(DB_PATH)}")
    print()

    # Quick verification
    prompts = get_all_prompts()
    print(f"Verification: {len(prompts)} prompts in database.")
    for p in prompts[:3]:
        print(f"  - [{p['category']}] {p['prompt_text']}")
    if len(prompts) > 3:
        print(f"  ... and {len(prompts) - 3} more.")
