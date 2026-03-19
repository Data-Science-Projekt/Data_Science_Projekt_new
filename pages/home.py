import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="StockInsight", page_icon="📈", layout="wide")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* ── accent colors ── */
:root {
    --accent-blue:  #2563eb;
    --accent-green: #16a34a;
}

/* ── global ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── hero banner ── */
.hero-banner {
    background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(37,99,235,0.02) 50%, rgba(22,163,74,0.05) 100%);
    border: 1px solid rgba(37,99,235,0.2);
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
    background: radial-gradient(circle, rgba(37,99,235,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.hero-banner::after {
    content: "";
    position: absolute;
    bottom: -80px; left: -40px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(22,163,74,0.08) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 3.2rem;
    font-weight: 800;
    letter-spacing: -1px;
    margin: 0 0 4px 0;
    background: linear-gradient(90deg, var(--accent-blue), #0ea5e9, var(--accent-green));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
}
.hero-subtitle {
    font-size: 1.2rem;
    font-weight: 300;
    margin: 0;
    max-width: 640px;
    line-height: 1.6;
    opacity: 0.7;
}
.hero-badge {
    display: inline-block;
    background: rgba(37,99,235,0.1);
    border: 1px solid rgba(37,99,235,0.3);
    color: var(--accent-blue);
    font-size: 0.82rem;
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
.section-banner-blue  {
    background: linear-gradient(90deg, rgba(37,99,235,0.08), rgba(37,99,235,0.01));
    border-left: 3px solid #2563eb;
}
.section-banner-green {
    background: linear-gradient(90deg, rgba(22,163,74,0.08), rgba(22,163,74,0.01));
    border-left: 3px solid #16a34a;
}
.section-icon { font-size: 1.5rem; line-height: 1; }
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    margin: 0;
}

/* ── summary box ── */
.summary-box {
    background: rgba(37,99,235,0.04);
    border: 1px solid rgba(37,99,235,0.15);
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 24px;
    line-height: 1.7;
    font-size: 1.08rem;
}
.summary-box .highlight {
    color: #2563eb;
    font-weight: 600;
}

/* ── insight card ── */
.insight-card {
    background: rgba(0,0,0,0.02);
    border: 1px solid rgba(0,0,0,0.1);
    border-radius: 12px;
    padding: 22px 22px 20px;
    margin-bottom: 16px;
    transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
    height: 210px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
}
.insight-card:hover {
    border-color: #2563eb;
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(37,99,235,0.1);
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
.icon-blue   { background: rgba(37,99,235,0.12);  }
.icon-green  { background: rgba(22,163,74,0.12);   }
.icon-orange { background: rgba(217,119,6,0.12);   }
.icon-purple { background: rgba(124,58,237,0.12);  }
.icon-teal   { background: rgba(13,148,136,0.12);  }
.icon-red    { background: rgba(220,38,38,0.12);   }
.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.08rem;
    font-weight: 700;
    margin: 0;
}
.card-body {
    font-size: 1rem;
    line-height: 1.65;
    margin: 0;
    opacity: 0.75;
}
/* ── ticker strip ── */
.ticker-strip {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 18px;
}
.ticker-pill {
    background: rgba(37,99,235,0.1);
    border: 1px solid rgba(37,99,235,0.25);
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 0.92rem;
    font-weight: 600;
    color: #2563eb;
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
    This project investigates <span class="highlight">eight research questions</span> about stock market
    behavior using real financial data and modern data science methods. We analyze
    <span class="highlight">six U.S. stocks</span> across two sectors — Technology
    (Apple, Microsoft, NVIDIA) and Financial (J.P. Morgan, Goldman Sachs, Bank of America) —
    using data from <span class="highlight">Alpha Vantage</span> (daily stock prices) and
    <span class="highlight">FRED</span> (S&P 500, VIX, Consumer Sentiment).
    <br><br>
    The analyses span return distributions, intraday volatility, volume anomaly detection,
    bull/bear market phase classification, VIX-based stress testing, Value-at-Risk modeling,
    iPhone sales event studies, and sentiment-stock correlation analysis. Each research question
    is addressed on its own interactive page with adjustable parameters, statistical tests, and
    a clear interpretation of results.
    <br><br>
    The project is built as a <span class="highlight">Streamlit web application</span>, deployed on
    Streamlit Community Cloud, using Python, Pandas, SciPy, and Plotly.
</div>
""", unsafe_allow_html=True)


# ── Research Questions ─────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-green">
    <span class="section-icon">🔍</span>
    <p class="section-title">Research Questions</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-blue">📉</div>
            <p class="card-title">RQ1 — Return Analysis</p>
        </div>
        <p class="card-body">
            Are the daily returns of Apple and NVIDIA normally distributed, or do they
            deviate significantly from the Gaussian assumption?
        </p>
    </div>

    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-orange">⚡</div>
            <p class="card-title">RQ2 — Volatility</p>
        </div>
        <p class="card-body">
            How do the intraday trading ranges of tech stocks compare to those of
            financial stocks over time?
        </p>
    </div>

    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-purple">📊</div>
            <p class="card-title">RQ3 — Technical Analysis</p>
        </div>
        <p class="card-body">
            Do volume spike patterns differ systematically between the technology
            and financial sectors?
        </p>
    </div>

    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-green">🐂</div>
            <p class="card-title">RQ4 — Market Phases</p>
        </div>
        <p class="card-body">
            Can bull and bear market phases be systematically identified, and how do
            individual stocks behave across these regimes?
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-teal">🔗</div>
            <p class="card-title">RQ5 — Market Structure</p>
        </div>
        <p class="card-body">
            How do Apple and NVIDIA react to periods of elevated market stress
            as measured by the VIX index?
        </p>
    </div>

    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-red">🛡️</div>
            <p class="card-title">RQ6 — Risk Management</p>
        </div>
        <p class="card-body">
            What are the Value-at-Risk and Expected Shortfall levels for Apple and
            NVIDIA, and how do their risk profiles compare?
        </p>
    </div>

    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-blue">📱</div>
            <p class="card-title">RQ7 — Company Fundamentals</p>
        </div>
        <p class="card-body">
            Does the quarterly iPhone sales volume statistically correlate with
            Apple's stock price returns in the month following earnings?
        </p>
    </div>

    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-orange">🧠</div>
            <p class="card-title">RQ8 — Sentiment Correlation</p>
        </div>
        <p class="card-body">
            How does the Consumer Sentiment Index correlate with the monthly
            returns of tech and financial stocks?
        </p>
    </div>
    """, unsafe_allow_html=True)