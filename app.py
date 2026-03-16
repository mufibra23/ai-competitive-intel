"""
app.py - Streamlit Dashboard for AI Competitive Intelligence Monitor.
Visualizes CRM brand citations across AI search platforms.

Run with: streamlit run app.py
"""

import sys
import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.analytics.metrics import (
    get_citations_dataframe, share_of_voice, citation_quality_score,
    platform_coverage, sentiment_score, brand_summary, category_breakdown,
    source_analysis
)
from src.analytics.competitive import (
    head_to_head, gap_analysis, category_heatmap_data, source_domain_analysis
)
from src.analytics.ai_insights import generate_insights
from startup import ensure_data_exists
ensure_data_exists()


# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="AI Competitive Intelligence Monitor",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CUSTOM CSS =====
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
    
    .stApp {
        font-family: 'DM Sans', sans-serif;
    }
    
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    
    .sub-header {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.85;
    }
    
    .insight-box {
        background: #f8fafc;
        border-left: 4px solid #667eea;
        padding: 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    
    .data-notice {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        font-size: 0.85rem;
        color: #92400e;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ===== LOAD DATA =====
@st.cache_data(ttl=300)
def load_data():
    return get_citations_dataframe()


df = load_data()

if df.empty:
    st.error("No citation data found. Run `python src/pipeline.py` first to populate the database.")
    st.stop()


# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("## 🔍 AI CompIntel Monitor")
    st.markdown("**CRM for SMBs**")
    st.markdown("---")
    
    # Brand filter
    all_brands = sorted(df["brand_mentioned"].unique().tolist())
    selected_brands = st.multiselect(
        "Filter Brands",
        options=all_brands,
        default=all_brands,
        help="Select which brands to include in the analysis"
    )
    
    # Platform filter
    all_platforms = sorted(df["platform"].unique().tolist())
    selected_platforms = st.multiselect(
        "Filter Platforms",
        options=all_platforms,
        default=all_platforms,
    )
    
    # Category filter
    all_categories = sorted(df["category"].unique().tolist())
    selected_categories = st.multiselect(
        "Filter Categories",
        options=all_categories,
        default=all_categories,
    )
    
    st.markdown("---")
    st.markdown("##### Data Info")
    st.caption(f"Total citations: {len(df)}")
    st.caption(f"Brands tracked: {df['brand_mentioned'].nunique()}")
    st.caption(f"Platforms: {df['platform'].nunique()}")
    
    # Data notice
    if any("sample" in p for p in df["platform"].unique()):
        st.markdown("---")
        st.warning("⚠️ Dashboard uses sample/demo data for demonstration purposes.")


# Apply filters
filtered_df = df[
    (df["brand_mentioned"].isin(selected_brands)) &
    (df["platform"].isin(selected_platforms)) &
    (df["category"].isin(selected_categories))
]

if filtered_df.empty:
    st.warning("No data matches your filters. Try adjusting the sidebar selections.")
    st.stop()


# ===== HEADER =====
st.markdown('<p class="main-header">🔍 AI Competitive Intelligence Monitor</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">How AI search engines recommend CRM brands — powered by Perplexity & Gemini citation analysis</p>', unsafe_allow_html=True)


# ===== TOP METRICS ROW =====
summary = brand_summary(filtered_df)
top_brand = summary.iloc[0] if not summary.empty else None

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Citations",
        value=f"{len(filtered_df):,}",
    )

with col2:
    st.metric(
        label="Brands Tracked",
        value=len(selected_brands),
    )

with col3:
    if top_brand is not None:
        st.metric(
            label="Market Leader",
            value=top_brand["brand_mentioned"],
            delta=f"{top_brand['share_of_voice']:.1f}% SoV",
        )

with col4:
    avg_sentiment = filtered_df.groupby("brand_mentioned").apply(
        lambda x: (len(x[x["sentiment"] == "positive"]) - len(x[x["sentiment"] == "negative"])) / len(x)
    ).mean()
    st.metric(
        label="Avg Sentiment",
        value=f"{avg_sentiment:+.2f}",
        delta="Positive" if avg_sentiment > 0 else "Negative",
    )

st.markdown("---")


# ===== TABS =====
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Niche Overview",
    "🏷️ Brand Deep Dive",
    "⚔️ Head-to-Head",
    "🌐 Source Intelligence",
    "🤖 AI Insights"
])


# ===== TAB 1: NICHE OVERVIEW =====
with tab1:
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.subheader("Share of Voice")
        sov = share_of_voice(filtered_df)
        
        fig_sov = px.bar(
            sov,
            x="share_of_voice",
            y="brand_mentioned",
            orientation="h",
            text="share_of_voice",
            color="share_of_voice",
            color_continuous_scale=["#c084fc", "#7c3aed", "#4c1d95"],
        )
        fig_sov.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_sov.update_layout(
            yaxis=dict(categoryorder="total ascending"),
            showlegend=False,
            coloraxis_showscale=False,
            height=400,
            margin=dict(l=0, r=40, t=10, b=0),
            xaxis_title="Share of Voice (%)",
            yaxis_title="",
        )
        st.plotly_chart(fig_sov, use_container_width=True)
    
    with col_right:
        st.subheader("Citation Quality")
        quality = citation_quality_score(filtered_df)
        
        fig_quality = px.bar(
            quality,
            x="quality_normalized",
            y="brand_mentioned",
            orientation="h",
            text="quality_normalized",
            color="quality_normalized",
            color_continuous_scale=["#86efac", "#22c55e", "#166534"],
        )
        fig_quality.update_traces(texttemplate="%{text:.0f}/100", textposition="outside")
        fig_quality.update_layout(
            yaxis=dict(categoryorder="total ascending"),
            showlegend=False,
            coloraxis_showscale=False,
            height=400,
            margin=dict(l=0, r=40, t=10, b=0),
            xaxis_title="Quality Score (0-100)",
            yaxis_title="",
        )
        st.plotly_chart(fig_quality, use_container_width=True)
    
    # Category heatmap
    st.subheader("Brand × Category Heatmap")
    st.caption("Which brands dominate which types of buyer questions")
    
    heatmap_data = category_heatmap_data(filtered_df)
    if not heatmap_data.empty:
        fig_heat = px.imshow(
            heatmap_data.values,
            labels=dict(x="Prompt Category", y="Brand", color="Mentions"),
            x=heatmap_data.columns.tolist(),
            y=heatmap_data.index.tolist(),
            color_continuous_scale="Purples",
            text_auto=True,
        )
        fig_heat.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_heat, use_container_width=True)
    
    # Sentiment breakdown
    st.subheader("Sentiment Analysis")
    sent = sentiment_score(filtered_df)
    if not sent.empty:
        fig_sent = go.Figure()
        for sentiment_type, color in [("positive", "#22c55e"), ("neutral", "#94a3b8"), ("negative", "#ef4444")]:
            if sentiment_type in sent.columns:
                fig_sent.add_trace(go.Bar(
                    name=sentiment_type.capitalize(),
                    x=sent["brand_mentioned"],
                    y=sent[sentiment_type],
                    marker_color=color,
                ))
        fig_sent.update_layout(
            barmode="stack",
            height=350,
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis_title="",
            yaxis_title="Number of Citations",
        )
        st.plotly_chart(fig_sent, use_container_width=True)


# ===== TAB 2: BRAND DEEP DIVE =====
with tab2:
    selected_brand = st.selectbox("Select a brand to analyze", options=all_brands)
    
    brand_df = filtered_df[filtered_df["brand_mentioned"] == selected_brand]
    
    if brand_df.empty:
        st.info(f"No citations found for {selected_brand} with current filters.")
    else:
        # Brand metrics row
        bcol1, bcol2, bcol3, bcol4 = st.columns(4)
        
        total = len(brand_df)
        pos_pct = len(brand_df[brand_df["sentiment"] == "positive"]) / total * 100
        avg_pos = brand_df["position"].mean()
        platforms = brand_df["platform"].nunique()
        
        bcol1.metric("Total Citations", total)
        bcol2.metric("Positive Sentiment", f"{pos_pct:.0f}%")
        bcol3.metric("Avg Position", f"{avg_pos:.1f}")
        bcol4.metric("Platform Coverage", f"{platforms}/{df['platform'].nunique()}")
        
        # Citations by platform
        col_l, col_r = st.columns(2)
        
        with col_l:
            st.subheader("Citations by Platform")
            plat_counts = brand_df["platform"].value_counts().reset_index()
            plat_counts.columns = ["platform", "count"]
            fig_plat = px.pie(
                plat_counts, values="count", names="platform",
                color_discrete_sequence=["#7c3aed", "#c084fc", "#e9d5ff"]
            )
            fig_plat.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_plat, use_container_width=True)
        
        with col_r:
            st.subheader("Citations by Category")
            cat_counts = brand_df["category"].value_counts().reset_index()
            cat_counts.columns = ["category", "count"]
            fig_cat = px.bar(
                cat_counts, x="count", y="category", orientation="h",
                color_discrete_sequence=["#7c3aed"]
            )
            fig_cat.update_layout(
                height=300, margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(categoryorder="total ascending"),
                xaxis_title="Citations", yaxis_title="",
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        
        # Sample context snippets
        st.subheader("How AI Platforms Describe This Brand")
        snippets = brand_df[brand_df["context_snippet"].notna()].head(5)
        for _, row in snippets.iterrows():
            sentiment_emoji = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}.get(row["sentiment"], "⚪")
            st.markdown(f'{sentiment_emoji} *"{row["context_snippet"]}"*')
            st.caption(f"— {row['platform']} | {row['category']}")


# ===== TAB 3: HEAD-TO-HEAD =====
with tab3:
    col_a, col_b = st.columns(2)
    with col_a:
        brand_a = st.selectbox("Brand A", options=all_brands, index=0)
    with col_b:
        remaining = [b for b in all_brands if b != brand_a]
        brand_b = st.selectbox("Brand B", options=remaining, index=min(2, len(remaining)-1))
    
    h2h = head_to_head(filtered_df, brand_a, brand_b)
    
    if h2h:
        # Comparison metrics
        mcol1, mcol2 = st.columns(2)
        
        for col, brand in [(mcol1, brand_a), (mcol2, brand_b)]:
            stats = h2h[brand]
            with col:
                st.markdown(f"### {brand}")
                st.metric("Citations", stats["total_citations"])
                st.metric("Positive %", f"{stats['positive_pct']:.0f}%")
                if stats["avg_position"]:
                    st.metric("Avg Position", f"{stats['avg_position']:.1f}")
                st.metric("Platforms", stats["platforms"])
        
        # Radar chart comparison
        st.subheader("Multi-Dimensional Comparison")
        
        stats_a = h2h[brand_a]
        stats_b = h2h[brand_b]
        
        categories_radar = ["Citations", "Positive %", "Platform Coverage", "Prompt Coverage"]
        
        max_citations = max(stats_a["total_citations"], stats_b["total_citations"], 1)
        max_prompts = max(len(h2h["only_a"]) + len(h2h["both"]), len(h2h["only_b"]) + len(h2h["both"]), 1)
        total_platforms = df["platform"].nunique()
        
        values_a = [
            stats_a["total_citations"] / max_citations * 100,
            stats_a["positive_pct"],
            stats_a["platforms"] / total_platforms * 100,
            (len(h2h["only_a"]) + len(h2h["both"])) / max_prompts * 100,
        ]
        values_b = [
            stats_b["total_citations"] / max_citations * 100,
            stats_b["positive_pct"],
            stats_b["platforms"] / total_platforms * 100,
            (len(h2h["only_b"]) + len(h2h["both"])) / max_prompts * 100,
        ]
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values_a + [values_a[0]],
            theta=categories_radar + [categories_radar[0]],
            fill="toself", name=brand_a,
            line_color="#7c3aed", fillcolor="rgba(124,58,237,0.2)"
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=values_b + [values_b[0]],
            theta=categories_radar + [categories_radar[0]],
            fill="toself", name=brand_b,
            line_color="#f97316", fillcolor="rgba(249,115,22,0.2)"
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            height=400,
            margin=dict(l=40, r=40, t=40, b=40),
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        
        # Prompt overlap
        st.subheader("Prompt Coverage Overlap")
        ocol1, ocol2, ocol3 = st.columns(3)
        ocol1.metric(f"Only {brand_a}", len(h2h["only_a"]))
        ocol2.metric("Both", len(h2h["both"]))
        ocol3.metric(f"Only {brand_b}", len(h2h["only_b"]))


# ===== TAB 4: SOURCE INTELLIGENCE =====
with tab4:
    st.subheader("Most Cited Source Domains")
    st.caption("Which websites do AI platforms cite most when recommending CRMs — tells you where to get featured")
    
    sources = source_domain_analysis(filtered_df)
    if not sources.empty:
        # Treemap
        sources_top = sources.head(10)
        fig_tree = px.treemap(
            sources_top,
            path=["domain"],
            values="citation_count",
            color="citation_count",
            color_continuous_scale="Purples",
        )
        fig_tree.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_tree, use_container_width=True)
        
        # Table
        st.subheader("Source Details")
        for _, row in sources.head(10).iterrows():
            with st.expander(f"🌐 {row['domain']} — cited {row['citation_count']}x"):
                st.write(f"**Brands cited from this source:** {', '.join(row['brands_cited'])}")
                st.write(f"**Platforms:** {', '.join(row['platforms'])}")
    else:
        st.info("No source URL data available in current dataset.")


# ===== TAB 5: AI INSIGHTS =====
with tab5:
    st.subheader("AI-Generated Strategic Analysis")
    st.caption("Powered by Gemini 3.1 Pro — analyzes your citation data and generates actionable insights")
    
    if st.button("🔄 Refresh Insights", help="Generate fresh analysis (uses 1 Gemini API call)"):
        with st.spinner("Generating strategic insights..."):
            insights = generate_insights(force_refresh=True)
        st.markdown(insights)
    else:
        insights = generate_insights(force_refresh=False)
        st.markdown(insights)
    
    st.markdown("---")
    st.caption("Insights are cached for 6 hours. Click 'Refresh' to generate a new analysis.")


# ===== FOOTER =====
st.markdown("---")
st.markdown(
    """<div style='text-align: center; color: #9ca3af; font-size: 0.8rem;'>
    AI Competitive Intelligence Monitor — Built by Ibra | 
    Data sources: Perplexity (via Firecrawl) & Gemini API |
    <a href='https://github.com/' style='color: #7c3aed;'>GitHub</a>
    </div>""",
    unsafe_allow_html=True
)
