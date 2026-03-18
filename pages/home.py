import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="StockInsight", page_icon="📈", layout="wide")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* ── global ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0d1117;
    color: #e6edf3;
}

/* ── hero banner ── */
.hero-banner {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 40%, #0d1117 100%);
    border: 1px solid #30363d;
    border-radius: 16px;
    padding: 48px 56px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: "";
    position: absolute;
    top: -60px; right: -60px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(56,139,253,0.15) 0%, transparent 70%);
    pointer-events: none;
}
.hero-banner::after {
    content: "";
    position: absolute;
    bottom: -80px; left: -40px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(63,185,80,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 3.2rem;
    font-weight: 800;
    letter-spacing: -1px;
    margin: 0 0 4px 0;
    background: linear-gradient(90deg, #58a6ff, #79c0ff, #3fb950);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
}
.hero-subtitle {
    color: #8b949e;
    font-size: 1.05rem;
    font-weight: 300;
    margin: 0;
    max-width: 640px;
    line-height: 1.6;
}
.hero-badge {
    display: inline-block;
    background: rgba(56,139,253,0.15);
    border: 1px solid rgba(56,139,253,0.4);
    color: #79c0ff;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 14px;
}

/* ── section header banner ── */
.section-banner {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 22px;
    border-radius: 10px;
    margin-bottom: 20px;
    margin-top: 10px;
}
.section-banner-blue  { background: linear-gradient(90deg, rgba(56,139,253,0.18), rgba(56,139,253,0.04)); border-left: 3px solid #388bfd; }
.section-banner-green { background: linear-gradient(90deg, rgba(63,185,80,0.18),  rgba(63,185,80,0.04));  border-left: 3px solid #3fb950; }
.section-icon { font-size: 1.5rem; line-height: 1; }
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #e6edf3;
    margin: 0;
}

/* ── summary box ── */
.summary-box {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 24px;
    line-height: 1.7;
    color: #c9d1d9;
    font-size: 0.97rem;
}
.summary-box .highlight {
    color: #79c0ff;
    font-weight: 500;
}

/* ── insight card ── */
.insight-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 22px 22px 20px;
    margin-bottom: 16px;
    transition: border-color 0.2s, transform 0.2s;
    height: 100%;
}
.insight-card:hover {
    border-color: #388bfd;
    transform: translateY(-2px);
}
.card-icon-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}
.card-icon {
    font-size: 1.4rem;
    width: 40px; height: 40px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 8px;
    flex-shrink: 0;
}
.icon-blue   { background: rgba(56,139,253,0.15); }
.icon-green  { background: rgba(63,185,80,0.15);  }
.icon-orange { background: rgba(210,153,34,0.15); }
.icon-purple { background: rgba(163,113,247,0.15);}
.icon-teal   { background: rgba(56,211,203,0.15); }
.icon-red    { background: rgba(248,81,73,0.15);  }
.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: #e6edf3;
    margin: 0;
}
.card-body {
    color: #8b949e;
    font-size: 0.88rem;
    line-height: 1.65;
    margin: 0;
}

/* ── divider ── */
hr { border-color: #21262d !important; margin: 28px 0 !important; }

/* ── ticker strip ── */
.ticker-strip {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 18px;
}
.ticker-pill {
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 0.8rem;
    font-weight: 500;
    color: #58a6ff;
    letter-spacing: 0.5px;
}
</style>
""", unsafe_allow_html=True)


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <div class="hero-badge">📊 Data Science · Finance</div>
    <h1 class="hero-title">StockInsight</h1>
    <p class="hero-subtitle">
        A systematic data science framework for stock market analysis —
        from return distributions and volatility to market regimes and portfolio risk.
    </p>
    <div class="ticker-strip">
        <span class="ticker-pill">AAPL</span>
        <span class="ticker-pill">MSFT</span>
        <span class="ticker-pill">NVDA</span>
        <span class="ticker-pill">JPM</span>
        <span class="ticker-pill">GS</span>
        <span class="ticker-pill">BAC</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Project Summary ────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-blue">
    <span class="section-icon">📋</span>
    <p class="section-title">Project Summary</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="summary-box">
    This project applies modern data science methods to investigate key research questions about stock market behavior.
    Using live data from <span class="highlight">Alpha Vantage</span>, <span class="highlight">NewsAPI</span>, and <span class="highlight">FRED</span>,
    we analyze <span class="highlight">six tech and financial stocks</span>
    (Apple, Microsoft, NVIDIA, J.P. Morgan, Goldman Sachs, Bank of America)
    across multiple dimensions: return distributions, trading ranges, market structure,
    regime detection, technical indicators, and risk management.
</div>
""", unsafe_allow_html=True)


# ── Key Findings ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-green">
    <span class="section-icon">🔍</span>
    <p class="section-title">Key Findings</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-blue">📉</div>
            <p class="card-title">Return Analysis</p>
        </div>
        <p class="card-body">
            Daily log-returns deviate significantly from a normal distribution,
            exhibiting fat tails (leptokurtosis) and negative skewness —
            extreme events occur more frequently than standard models predict.
        </p>
    </div>

    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-green">🐂</div>
            <p class="card-title">Market Phases</p>
        </div>
        <p class="card-body">
            Bull and bear markets can be systematically identified.
            Bull markets last significantly longer on average, but bear markets
            exhibit stronger and faster price movements.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-orange">⚡</div>
            <p class="card-title">Volatility &amp; Trading Ranges</p>
        </div>
        <p class="card-body">
            Tech stocks show higher average daily trading ranges than financial stocks.
            News sentiment magnitude is a stronger predictor of volatility spikes
            than sentiment direction alone.
        </p>
    </div>

    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-purple">📊</div>
            <p class="card-title">Technical Analysis</p>
        </div>
        <p class="card-body">
            Technical indicators (moving averages, RSI, MACD) provide useful signals
            in trending markets but frequently generate false signals in sideways phases.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-teal">🔗</div>
            <p class="card-title">Market Structure</p>
        </div>
        <p class="card-body">
            Correlations between stocks are dynamic, not static. During crises,
            correlations increase sharply, making diversification more difficult
            precisely when it is needed most.
        </p>
    </div>

    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-red">🛡️</div>
            <p class="card-title">Risk Management</p>
        </div>
        <p class="card-body">
            With as few as 15–20 stocks, unsystematic risk can be largely eliminated
            through diversification. However, systematic market risk remains
            and must be managed separately.
        </p>
    </div>
    """, unsafe_allow_html=True)