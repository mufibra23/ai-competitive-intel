# 🔍 AI Competitive Intelligence Monitor

**Monitor how AI search engines recommend brands in any niche.**

An automated pipeline that queries AI platforms (Perplexity, Gemini), extracts brand citations, and visualizes competitive positioning on an interactive dashboard. Built for the CRM niche as a demonstration — adaptable to any product category.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_3.1_Pro-AI_Insights-4285F4?logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## The Problem

Brands are increasingly invisible in AI-generated answers — and most don't know it. When someone asks ChatGPT, Gemini, or Perplexity "What's the best CRM for small businesses?", only a few brands get recommended. Manual monitoring across multiple AI platforms is impractical and doesn't scale.

Companies like Otterly ($29-189/mo), Athena ($95/mo), and ZipTie ($69-159/mo) charge significant monthly fees for AI citation tracking. This project demonstrates how to build the analytics engine behind those services.

## The Solution

An automated pipeline that:
1. **Queries AI platforms** with real buyer-style prompts ("What's the best CRM?", "Compare HubSpot vs Attio")
2. **Extracts brand citations** — which brands get mentioned, in what position, with what sentiment
3. **Calculates competitive metrics** — Share of Voice, Citation Quality Score, Sentiment Analysis
4. **Visualizes everything** on an interactive Streamlit dashboard with 5 analytical views
5. **Generates strategic insights** using Gemini 3.1 Pro to turn numbers into actionable recommendations

## Dashboard Screenshots

### Niche Overview — Share of Voice & Citation Quality
The main view showing which brands dominate AI recommendations and their quality scores.

### Head-to-Head Comparison — Radar Chart
Compare any two brands across multiple dimensions: citations, sentiment, platform coverage, and prompt coverage.

### Source Intelligence — Treemap
Discover which websites AI platforms cite most when recommending CRMs — tells clients exactly where they need to get featured.

### Brand × Category Heatmap
See which brands dominate which types of buyer questions (comparisons, pricing, features, use cases).

> *Replace these descriptions with actual screenshots after deployment*

## Architecture

```
config/prompts.json ──→ SQLite Database
                              │
                    Pipeline (pipeline.py)
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   Firecrawl            Gemini API         Sample Data
 (Perplexity)        (gemini-3.1-pro)     Generator
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    Citation Extractor
                  (brands, sentiment,
                   position, sources)
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              metrics.py          competitive.py
           (Share of Voice,      (Head-to-Head,
            Quality Score,        Gap Analysis,
            Sentiment)            Source Intel)
                    │                   │
                    └─────────┬─────────┘
                              ▼
                      ai_insights.py
                    (Gemini strategic
                       narrative)
                              │
                              ▼
                     Streamlit Dashboard
                    (5 interactive tabs)
```

## Key Metrics

| Metric | What It Measures | Why It Matters |
|--------|-----------------|----------------|
| **Share of Voice** | % of total citations per brand | The #1 metric — shows who dominates AI recommendations |
| **Citation Quality Score** | Position-weighted mentions (1st = 3x, top 3 = 2x) | Not all mentions are equal — being first matters |
| **Sentiment Score** | Positive vs negative context (-1.0 to +1.0) | Brands can be mentioned but criticized |
| **Platform Coverage** | % of AI platforms that mention the brand | Visibility gaps across platforms |
| **Gap Analysis** | Prompts where a brand is missing but competitors appear | Direct opportunities for improvement |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Web Scraping | Firecrawl API |
| AI Platform | Google Gemini 3.1 Pro |
| Database | SQLite |
| Data Analysis | pandas |
| Visualization | Plotly |
| Dashboard | Streamlit |
| Deployment | Streamlit Community Cloud |

## Quick Start

### 1. Clone and install
```bash
git clone https://github.com/YOUR_USERNAME/ai-competitive-intel.git
cd ai-competitive-intel
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2. Set up API keys
```bash
cp .env.example .env
# Edit .env with your keys:
# FIRECRAWL_API_KEY=fc-your_key_here
# GEMINI_API_KEY=your_gemini_key_here
```

### 3. Initialize the database and run pipeline
```bash
python src/database.py          # Create tables + load prompts
python src/pipeline.py          # Generate sample data (no API credits needed)
```

### 4. Launch the dashboard
```bash
streamlit run app.py
```

Open http://localhost:8501 and explore the 5 dashboard tabs.

### 5. (Optional) Run with real API data
```bash
python src/pipeline.py --live --max 5   # Uses 5 Firecrawl credits + Gemini API
```

## Project Structure

```
ai-competitive-intel/
├── app.py                          # Streamlit dashboard (5 tabs)
├── requirements.txt
├── .env.example                    # Template for API keys
├── .gitignore
├── config/
│   ├── brands.json                 # 7 CRM brands to track
│   └── prompts.json                # 20 buyer-style prompts
├── src/
│   ├── __init__.py
│   ├── database.py                 # SQLite setup + helper functions
│   ├── pipeline.py                 # Orchestrates: collect → parse → store
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── firecrawl_collector.py  # Scrapes Perplexity via Firecrawl
│   │   ├── gemini_collector.py     # Queries Gemini 3.1 Pro API
│   │   └── sample_data_generator.py # Realistic demo data generator
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── citation_extractor.py   # Extracts brands, sentiment, sources
│   └── analytics/
│       ├── __init__.py
│       ├── metrics.py              # Share of Voice, Quality, Sentiment
│       ├── competitive.py          # Head-to-Head, Gap Analysis
│       └── ai_insights.py          # Gemini-powered strategic analysis
└── data/
    └── competitive_intel.db        # SQLite database (auto-generated)
```

## Demo Niche: CRM for Small & Mid-Size Business

| Brand | Role in Analysis |
|-------|-----------------|
| HubSpot | Market leader — dominates AI citations |
| Salesforce | Enterprise giant — strong sentiment, less SMB visibility |
| Attio | Rising challenger — the David vs Goliath story |
| Pipedrive | Sales pipeline specialist |
| Zoho CRM | Value player — strong in pricing queries |
| Close | Outbound sales niche |
| Freshsales | Budget-friendly option |

## What This Enables as a Service

| Service | Price Range |
|---------|------------|
| AI Brand Visibility Audit (one-time report) | $1,000–2,000 |
| AI Competitive Intelligence Report | $1,500–3,000 |
| Monthly AI Citation Monitoring (retainer) | $500–1,500/mo |
| GEO Content Strategy (recommendations) | $2,000–3,000 |

## Key Findings from Sample Data

- **HubSpot** dominates with ~23% Share of Voice and the highest Citation Quality Score
- **Salesforce** shows the highest sentiment (+0.80) despite fewer total citations — quality over quantity
- **Attio** is missing from general recommendation queries but strong in comparisons — a gap that targeted content could fill
- **reddit.com** is the most-cited source domain across AI platforms — brands need Reddit presence
- AI platforms favor structured comparison content and pricing transparency

## Note on Data

This dashboard uses **sample/demo data** for demonstration purposes. The sample data generator creates realistic citation patterns based on actual market observations from Perplexity and Gemini API queries. For production monitoring, the pipeline supports live API calls with `--live` mode.

## Future Improvements

- Add more AI platforms (ChatGPT, Claude, Google AI Overviews)
- Real-time monitoring with scheduled pipeline runs
- Alert system for citation drops or competitor changes
- Historical trend tracking across weeks/months
- White-label client dashboard version

## Built By

**Ibra** — AI Marketing Analytics | [LinkedIn](https://linkedin.com/) | [Portfolio](https://github.com/)

Part of a 10-project AI Marketing Analytics portfolio. See also:
- [Project 1: AI Marketing Intelligence Agent](https://github.com/) — AI-powered GA4 analytics dashboard


