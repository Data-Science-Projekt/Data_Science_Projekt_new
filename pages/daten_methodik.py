import streamlit as st
import pandas as pd

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Data & Methodology – StockInsight", page_icon="🔬", layout="wide")

# ── Shared CSS (same design system as homepage) ───────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --accent-blue:  #2563eb;
    --accent-green: #16a34a;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── page hero ── */
.page-hero {
    background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(37,99,235,0.02) 60%, rgba(124,58,237,0.05) 100%);
    border: 1px solid rgba(37,99,235,0.2);
    border-radius: 16px;
    padding: 40px 56px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.page-hero::before {
    content: "";
    position: absolute;
    top: -50px; right: -50px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(37,99,235,0.1) 0%, transparent 70%);
    pointer-events: none;
}
.page-badge {
    display: inline-block;
    background: rgba(37,99,235,0.1);
    border: 1px solid rgba(37,99,235,0.3);
    color: #2563eb;
    font-size: 0.82rem;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 12px;
}
.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin: 0 0 6px 0;
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.15;
}
.page-subtitle {
    font-size: 1.2rem;
    font-weight: 300;
    margin: 0;
    max-width: 580px;
    line-height: 1.6;
    opacity: 0.7;
}

/* ── section banners ── */
.section-banner {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 22px;
    border-radius: 10px;
    margin-bottom: 20px;
    margin-top: 10px;
}
.section-banner-blue   { background: linear-gradient(90deg, rgba(37,99,235,0.08),  rgba(37,99,235,0.01));  border-left: 3px solid #2563eb; }
.section-banner-green  { background: linear-gradient(90deg, rgba(22,163,74,0.08),  rgba(22,163,74,0.01));  border-left: 3px solid #16a34a; }
.section-banner-purple { background: linear-gradient(90deg, rgba(124,58,237,0.08), rgba(124,58,237,0.01)); border-left: 3px solid #7c3aed; }
.section-banner-orange { background: linear-gradient(90deg, rgba(217,119,6,0.08),  rgba(217,119,6,0.01));  border-left: 3px solid #d97706; }
.section-icon  { font-size: 1.5rem; line-height: 1; }
.section-title { font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700; margin: 0; }

/* ── info box ── */
.info-box {
    background: rgba(37,99,235,0.04);
    border: 1px solid rgba(37,99,235,0.15);
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 16px;
    line-height: 1.75;
    font-size: 1.08rem;
}
.info-box .hl-blue   { color: #2563eb; font-weight: 600; }
.info-box .hl-green  { color: #16a34a; font-weight: 600; }
.info-box .hl-purple { color: #7c3aed; font-weight: 600; }

/* ── source pill row ── */
.source-strip {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 16px;
    margin-bottom: 8px;
}
.source-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(37,99,235,0.08);
    border: 1px solid rgba(37,99,235,0.2);
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 0.95rem;
    font-weight: 600;
    color: #2563eb;
    letter-spacing: 0.3px;
}

/* ── step card ── */
.step-card {
    background: rgba(0,0,0,0.02);
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 12px;
    display: flex;
    gap: 16px;
    align-items: flex-start;
    transition: border-color 0.2s, transform 0.2s;
}
.step-card:hover {
    border-color: #2563eb;
    transform: translateX(3px);
}
.step-number {
    font-family: 'Syne', sans-serif;
    font-size: 1.4rem;
    font-weight: 800;
    color: #2563eb;
    opacity: 0.35;
    min-width: 32px;
    line-height: 1.3;
}
.step-content {}
.step-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    margin: 0 0 3px 0;
}
.step-desc {
    font-size: 0.98rem;
    line-height: 1.55;
    margin: 0;
    opacity: 0.7;
}

/* ── method card ── */
.method-card {
    background: rgba(0,0,0,0.02);
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 14px;
    transition: border-color 0.2s, transform 0.2s;
}
.method-card:hover {
    border-color: #7c3aed;
    transform: translateY(-2px);
}
.method-title { font-family: 'Syne', sans-serif; font-size: 1.05rem; font-weight: 700; margin: 0 0 4px 0; }
.method-tags  { font-size: 0.95rem; opacity: 0.65; margin: 0; line-height: 1.5; }

/* ── tech table ── */
.tech-row {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 14px 20px;
    border-radius: 8px;
    margin-bottom: 8px;
    background: rgba(0,0,0,0.02);
    border: 1px solid rgba(0,0,0,0.06);
    transition: border-color 0.15s;
}
.tech-row:hover { border-color: rgba(37,99,235,0.3); }
.tech-name  { font-family: 'Syne', sans-serif; font-size: 1.02rem; font-weight: 700; min-width: 160px; }
.tech-desc  { font-size: 0.98rem; opacity: 0.65; }
</style>
""", unsafe_allow_html=True)


# ── Page Hero ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-hero">
    <div class="page-badge">Methodology</div>
    <h1 class="page-title">Data & Methodology</h1>
    <p class="page-subtitle">
        Data sources, preparation pipeline, and applied analytical methods
        powering the StockInsight analysis.
    </p>
</div>
""", unsafe_allow_html=True)


# ── Data Sources ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-blue">
    <p class="section-title">Data Sources</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    Our analysis is based on historical stock price data obtained through publicly available financial APIs.
    Each data point includes <span class="hl-blue">Open, High, Low, Close, and Volume</span> — covering
    the last <span class="hl-blue">100 trading days</span> (Alpha Vantage compact) plus extended monthly history.
</div>

<div class="source-strip">
    <span class="source-pill">Alpha Vantage — Stock Data</span>
    <span class="source-pill">FRED — S&P 500 &amp; Consumer Sentiment</span>
</div>
""", unsafe_allow_html=True)

col_src1, col_src2 = st.columns(2)
with col_src1:
    st.markdown("""
    <div class="method-card">
        <p class="method-title">Price Data</p>
        <p class="method-tags">Daily OHLCV · 100 trading days compact · extended monthly history</p>
    </div>
    """, unsafe_allow_html=True)

with col_src2:
    st.markdown("""
    <div class="method-card">
        <p class="method-title">Stocks Analyzed</p>
        <p class="method-tags">AAPL · MSFT · NVDA · JPM · GS · BAC</p>
    </div>
    """, unsafe_allow_html=True)


# ── Data Preparation ──────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-green">
    <p class="section-title">Data Preparation</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="step-card">
    <div class="step-number">01</div>
    <div class="step-content">
        <p class="step-title">Cleaning</p>
        <p class="step-desc">Removal of missing values, outlier detection and correction to ensure data integrity.</p>
    </div>
</div>
<div class="step-card">
    <div class="step-number">02</div>
    <div class="step-content">
        <p class="step-title">Log-Return Calculation</p>
        <p class="step-desc">Transformation of raw prices into logarithmic returns for statistical comparability and stationarity.</p>
    </div>
</div>
<div class="step-card">
    <div class="step-number">03</div>
    <div class="step-content">
        <p class="step-title">Normalization & Standardization</p>
        <p class="step-desc">Z-score standardization and min-max scaling applied where required for cross-stock comparability.</p>
    </div>
</div>
<div class="step-card">
    <div class="step-number">04</div>
    <div class="step-content">
        <p class="step-title">Feature Engineering</p>
        <p class="step-desc">Computation of technical indicators (RSI, MACD, Bollinger Bands) and sentiment features from news data.</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Methods ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-purple">
    <p class="section-title">Methods</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="method-card">
        <p class="method-title">Statistical Analysis</p>
        <p class="method-tags">Descriptive statistics · Distribution analysis · Hypothesis testing · Normality tests</p>
    </div>
    <div class="method-card">
        <p class="method-title">Time Series Analysis</p>
        <p class="method-tags">ARIMA · GARCH models · Stationarity tests · Regime detection</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="method-card">
        <p class="method-title">Machine Learning</p>
        <p class="method-tags">Clustering · Classification · Dimensionality reduction · Feature importance</p>
    </div>
    <div class="method-card">
        <p class="method-title">Visualization</p>
        <p class="method-tags">Matplotlib · Seaborn · Plotly · Interactive charts & dashboards</p>
    </div>
    """, unsafe_allow_html=True)


# ── Technologies ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-orange">
    <p class="section-title">Technologies Used</p>
</div>
""", unsafe_allow_html=True)

techs = [
    ("Python",              "Core programming language"),
    ("Pandas / NumPy",      "Data processing & numerical computing"),
    ("Scikit-learn",        "Machine learning algorithms"),
    ("Matplotlib / Plotly", "Static & interactive visualization"),
    ("Streamlit",           "Web framework & deployment"),
]

for name, desc in techs:
    st.markdown(f"""
    <div class="tech-row">
        <span class="tech-name">{name}</span>
        <span class="tech-desc">{desc}</span>
    </div>
    """, unsafe_allow_html=True)