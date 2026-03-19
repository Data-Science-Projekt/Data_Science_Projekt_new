import streamlit as st
import pandas as pd

# ── Custom CSS (same design system as other pages) ───────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root { --accent-blue: #2563eb; --accent-green: #16a34a; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.page-hero {
    background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(37,99,235,0.02) 60%, rgba(124,58,237,0.05) 100%);
    border: 1px solid rgba(37,99,235,0.2); border-radius: 16px;
    padding: 40px 56px; margin-bottom: 32px;
    position: relative; overflow: hidden;
}
.page-hero::before {
    content: ""; position: absolute; top: -50px; right: -50px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(37,99,235,0.1) 0%, transparent 70%);
    pointer-events: none;
}
.page-badge {
    display: inline-block; background: rgba(37,99,235,0.1);
    border: 1px solid rgba(37,99,235,0.3); color: #2563eb;
    font-size: 0.82rem; font-weight: 500; letter-spacing: 1.5px;
    text-transform: uppercase; padding: 4px 12px;
    border-radius: 20px; margin-bottom: 12px;
}
.page-title {
    font-family: 'Syne', sans-serif; font-size: 2.4rem; font-weight: 800;
    letter-spacing: -0.5px; margin: 0 0 6px 0;
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1.15;
}
.page-subtitle {
    font-size: 1.2rem; font-weight: 300; margin: 0;
    max-width: 580px; line-height: 1.6; opacity: 0.7;
}

.section-banner {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 22px; border-radius: 10px;
    margin-bottom: 20px; margin-top: 10px;
}
.section-banner-blue   { background: linear-gradient(90deg, rgba(37,99,235,0.08), rgba(37,99,235,0.01)); border-left: 3px solid #2563eb; }
.section-banner-green  { background: linear-gradient(90deg, rgba(22,163,74,0.08), rgba(22,163,74,0.01)); border-left: 3px solid #16a34a; }
.section-banner-purple { background: linear-gradient(90deg, rgba(124,58,237,0.08), rgba(124,58,237,0.01)); border-left: 3px solid #7c3aed; }
.section-banner-orange { background: linear-gradient(90deg, rgba(217,119,6,0.08), rgba(217,119,6,0.01)); border-left: 3px solid #d97706; }
.section-icon  { font-size: 1.5rem; line-height: 1; }
.section-title { font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700; margin: 0; }

.info-box {
    background: rgba(37,99,235,0.04); border: 1px solid rgba(37,99,235,0.15);
    border-radius: 12px; padding: 24px 28px; margin-bottom: 16px;
    line-height: 1.75; font-size: 1.08rem;
}
.info-box .hl { color: #2563eb; font-weight: 600; }

.method-card {
    background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.08);
    border-radius: 12px; padding: 20px 22px; margin-bottom: 14px;
    transition: border-color 0.2s, transform 0.2s;
}
.method-card:hover { border-color: #7c3aed; transform: translateY(-2px); }
.method-title { font-family: 'Syne', sans-serif; font-size: 1.05rem; font-weight: 700; margin: 0 0 4px 0; }
.method-tags  { font-size: 0.95rem; opacity: 0.65; margin: 0; line-height: 1.5; }

.source-strip { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 16px; margin-bottom: 8px; }
.source-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(37,99,235,0.08); border: 1px solid rgba(37,99,235,0.2);
    border-radius: 8px; padding: 7px 16px; font-size: 0.95rem;
    font-weight: 600; color: #2563eb; letter-spacing: 0.3px;
}

.rq-card {
    background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.08);
    border-radius: 12px; padding: 18px 20px; margin-bottom: 12px;
    display: flex; gap: 16px; align-items: flex-start;
    transition: border-color 0.2s, transform 0.2s;
}
.rq-card:hover { border-color: #2563eb; transform: translateX(3px); }
.rq-number {
    font-family: 'Syne', sans-serif; font-size: 1.1rem; font-weight: 800;
    color: #2563eb; opacity: 1; min-width: 44px; line-height: 1.2;
    background: rgba(37,99,235,0.1); border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    padding: 4px 8px; flex-shrink: 0;
}
.rq-title { font-family: 'Syne', sans-serif; font-size: 1.02rem; font-weight: 700; margin: 0 0 3px 0; }
.rq-desc { font-size: 0.95rem; line-height: 1.5; margin: 0; opacity: 0.7; }

.tech-row {
    display: flex; align-items: center; gap: 16px;
    padding: 14px 20px; border-radius: 8px; margin-bottom: 8px;
    background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.06);
    transition: border-color 0.15s;
}
.tech-row:hover { border-color: rgba(37,99,235,0.3); }
.tech-name { font-family: 'Syne', sans-serif; font-size: 1.02rem; font-weight: 700; min-width: 160px; }
.tech-desc { font-size: 0.98rem; opacity: 0.65; }
</style>
""", unsafe_allow_html=True)


# ── Page Hero ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-hero">
    <div class="page-badge">About</div>
    <h1 class="page-title">About the Project</h1>
    <p class="page-subtitle">
        Goals, motivation, methodology, and data sources behind the
        StockInsight analysis framework.
    </p>
</div>
""", unsafe_allow_html=True)


# ── GOALS ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-blue">
    <span class="section-icon">🎯</span>
    <p class="section-title">Goals</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    The goal of this project is to systematically investigate <span class="hl">eight research questions</span>
    about stock market behavior using modern data science methods. We analyze
    <span class="hl">six major U.S. stocks</span> across two sectors: Technology (Apple, Microsoft, NVIDIA)
    and Financial (J.P. Morgan, Goldman Sachs, Bank of America), to understand how these assets
    behave under different market conditions.
    <br><br>
    Each research question is addressed on its own dedicated page with interactive charts,
    statistical analysis, and a clear interpretation of the results.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="rq-card">
    <div class="rq-number">RQ1</div>
    <div>
        <p class="rq-title">Return Analysis</p>
        <p class="rq-desc">To what extent do the daily log-returns of Apple and NVIDIA deviate from a normal distribution?</p>
    </div>
</div>
<div class="rq-card">
    <div class="rq-number">RQ2</div>
    <div>
        <p class="rq-title">Volatility</p>
        <p class="rq-desc">What are the differences in the daily trading range between selected tech stocks and selected financial stocks?</p>
    </div>
</div>
<div class="rq-card">
    <div class="rq-number">RQ3</div>
    <div>
        <p class="rq-title">Technical Analysis</p>
        <p class="rq-desc">How do trading volume patterns (frequency of volume spikes) differ between tech and financial stocks?</p>
    </div>
</div>
<div class="rq-card">
    <div class="rq-number">RQ4</div>
    <div>
        <p class="rq-title">Market Phases</p>
        <p class="rq-desc">How does the correlation between tech and financial stocks change during stable market periods compared to crisis periods?</p>
    </div>
</div>
<div class="rq-card">
    <div class="rq-number">RQ5</div>
    <div>
        <p class="rq-title">Market Structure</p>
        <p class="rq-desc">How do stock prices react during periods of extreme market volatility (when the VIX index exceeds a threshold)?</p>
    </div>
</div>
<div class="rq-card">
    <div class="rq-number">RQ6</div>
    <div>
        <p class="rq-title">Risk Management</p>
        <p class="rq-desc">What is the maximum expected loss (Value-at-Risk) for Apple compared to NVIDIA over a 1-day horizon?</p>
    </div>
</div>
<div class="rq-card">
    <div class="rq-number">RQ7</div>
    <div>
        <p class="rq-title">Company Fundamentals</p>
        <p class="rq-desc">How does the quarterly sales volume of iPhone units correlate with Apple's stock price returns after earnings?</p>
    </div>
</div>
<div class="rq-card">
    <div class="rq-number">RQ8</div>
    <div>
        <p class="rq-title">Sentiment Correlation</p>
        <p class="rq-desc">How does the Consumer Sentiment Index correlate with tech and financial stock returns?</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ── MOTIVATION ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-green">
    <span class="section-icon">💡</span>
    <p class="section-title">Motivation</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    Financial markets are complex systems where many assumptions from classical theory
    such as normally distributed returns, constant correlations, or efficient pricing of
    fundamental data break down in practice. This project was motivated by the desire to:
    <br><br>
    <strong>1. Bridge theory and practice</strong> — apply academic concepts (VaR, OLS regression,
    Pearson correlation, Z-score anomaly detection) to real market data and examine where models
    hold up and where they fail.
    <br><br>
    <strong>2. Build an end-to-end data pipeline</strong> — from API data ingestion
    (Alpha Vantage, FRED) through automated data processing to interactive visualization
    on a deployed web application.
    <br><br>
    <strong>3. Create an accessible tool</strong> — make quantitative financial analysis
    available through an <span class="hl">interactive Streamlit web application</span> with
    adjustable parameters, rather than static PDF reports.
    <br><br>
    <strong>4. Compare sectors systematically</strong> — by analyzing three tech and three
    financial stocks in parallel, we can identify structural differences in how these
    sectors behave under different market conditions.
</div>
""", unsafe_allow_html=True)


# ── METHODOLOGY ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-purple">
    <span class="section-icon">⚙️</span>
    <p class="section-title">Methodology</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="method-card">
        <p class="method-title">Statistical Analysis</p>
        <p class="method-tags">Pearson & Spearman correlation · OLS linear regression ·
        Kurtosis & skewness · Distribution fitting · p-value significance testing</p>
    </div>
    <div class="method-card">
        <p class="method-title">Risk Modeling</p>
        <p class="method-tags">Value-at-Risk (Historical Simulation) · Expected Shortfall (CVaR) ·
        Confidence level analysis · Tail risk assessment</p>
    </div>
    <div class="method-card">
        <p class="method-title">Volume Analysis</p>
        <p class="method-tags">Z-score anomaly detection · 20-day rolling average ·
        Volume spike frequency · Sector aggregation</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="method-card">
        <p class="method-title">Market Phase Detection</p>
        <p class="method-tags">Rolling 20-day window · Bull/bear threshold classification ·
        Phase distribution analysis · VIX-based regime detection</p>
    </div>
    <div class="method-card">
        <p class="method-title">Fundamental Analysis</p>
        <p class="method-tags">Earnings event study · 30-day post-earnings returns ·
        iPhone sales vs. stock price regression · Quarterly seasonality</p>
    </div>
    <div class="method-card">
        <p class="method-title">Visualization & Deployment</p>
        <p class="method-tags">Interactive Plotly charts · Streamlit multipage app ·
        PDF/PNG export · Streamlit Community Cloud deployment</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    <strong>Technology Stack:</strong>
</div>
""", unsafe_allow_html=True)

techs = [
    ("Python 3.13",         "Core programming language for all analysis and data processing"),
    ("Pandas / NumPy",      "Data manipulation, time series processing, numerical computing"),
    ("SciPy",               "Statistical tests (Pearson, Spearman, linregress, kurtosis, skew)"),
    ("Plotly",              "Interactive charts: histograms, scatter plots, heatmaps, bar charts"),
    ("Streamlit",           "Web application framework, multipage navigation, interactive widgets"),
    ("Alpha Vantage API",   "Daily stock price data (OHLCV) for all six stocks"),
    ("FRED API",            "S&P 500 index, VIX volatility index, Consumer Sentiment Index"),
]

for name, desc in techs:
    st.markdown(f"""
    <div class="tech-row">
        <span class="tech-name">{name}</span>
        <span class="tech-desc">{desc}</span>
    </div>
    """, unsafe_allow_html=True)


# ── DATASET DESCRIPTION ─────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-orange">
    <span class="section-icon">📊</span>
    <p class="section-title">Dataset Description</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    The analysis is based on <span class="hl">real market data</span> from publicly available
    financial APIs. Stock prices are fetched via Alpha Vantage (daily OHLCV data), while
    macroeconomic indicators come from the Federal Reserve Economic Data (FRED) API.
    iPhone sales data is maintained manually based on Apple earnings reports and third-party
    estimates (Statista, IDC).
</div>
""", unsafe_allow_html=True)

st.markdown("**Stocks Analyzed:**")

st.table(pd.DataFrame({
    "Stock": ["Apple (AAPL)", "Microsoft (MSFT)", "NVIDIA (NVDA)", "J.P. Morgan (JPM)", "Goldman Sachs (GS)", "Bank of America (BAC)"],
    "Sector": ["Technology", "Technology", "Technology", "Financial", "Financial", "Financial"],
    "Why Included": [
        "Largest company by market cap, benchmark for the tech sector",
        "Enterprise & cloud leader, diversified revenue streams",
        "AI/GPU leader, highest volatility among the six stocks",
        "Largest U.S. bank, financial sector bellwether",
        "Investment banking leader, sensitive to market conditions",
        "Consumer banking giant, interest rate sensitive",
    ],
}))

st.markdown("**Data Sources:**")

st.table(pd.DataFrame({
    "Source": ["Alpha Vantage", "FRED", "FRED", "FRED", "Apple IR / Statista"],
    "Dataset": [
        "Daily stock prices (OHLCV)",
        "S&P 500 Index",
        "CBOE Volatility Index (VIX)",
        "Consumer Sentiment Index (Univ. of Michigan)",
        "Quarterly iPhone unit sales & revenue",
    ],
    "Used In": [
        "All analysis pages (returns, volatility, risk, phases, volume)",
        "Return Analysis (benchmark comparison)",
        "Market Structure (panic threshold detection)",
        "Sentiment Correlation (macro-to-stock relationship)",
        "Company Fundamentals (earnings event study)",
    ],
}))

st.markdown("""
<div class="info-box">
    <strong>Data fields per stock (OHLCV):</strong>
    <br>Open: opening price of the trading day
    <br>High: highest price during the day
    <br>Low: lowest price during the day
    <br>Close: closing price (used for return calculations)
    <br>Volume: number of shares traded (used for volume spike analysis)
    <br><br>
    <strong>Derived features:</strong>
    <br>Log-returns: ln(Close_t / Close_t-1)
    <br>Daily trading range: (High - Low) / Close x 100%
    <br>Volume Z-score: (Volume - 20d avg) / 20d std
    <br>30-day post-earnings return (Company Fundamentals)
    <br>Monthly returns (Sentiment Correlation)
</div>
""", unsafe_allow_html=True)

st.caption("StockInsight — Data Science Project, Europa-Universitat Flensburg")