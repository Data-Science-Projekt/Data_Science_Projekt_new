import streamlit as st

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root { --accent-blue: #2563eb; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.page-hero {
    background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(37,99,235,0.02) 60%, rgba(22,163,74,0.05) 100%);
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
    background: linear-gradient(90deg, #2563eb, #16a34a);
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

.result-card {
    background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.08);
    border-radius: 12px; padding: 18px 20px; margin-bottom: 12px;
    display: flex; gap: 16px; align-items: flex-start;
    transition: border-color 0.2s, transform 0.2s;
}
.result-card:hover { border-color: #2563eb; transform: translateX(3px); }
.result-number {
    font-family: 'Syne', sans-serif; font-size: 1.1rem; font-weight: 800;
    color: #2563eb; opacity: 0.4; min-width: 36px; line-height: 1.3;
}
.result-title { font-family: 'Syne', sans-serif; font-size: 1.02rem; font-weight: 700; margin: 0 0 3px 0; }
.result-desc { font-size: 0.95rem; line-height: 1.55; margin: 0; opacity: 0.7; }

.insight-card {
    background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.1);
    border-radius: 12px; padding: 22px 22px 20px; margin-bottom: 16px;
    transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
}
.insight-card:hover {
    border-color: #2563eb; transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(37,99,235,0.1);
}
.card-icon-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.card-icon {
    font-size: 1.4rem; width: 40px; height: 40px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 8px; flex-shrink: 0;
}
.icon-blue   { background: rgba(37,99,235,0.12); }
.icon-green  { background: rgba(22,163,74,0.12); }
.icon-orange { background: rgba(217,119,6,0.12); }
.icon-purple { background: rgba(124,58,237,0.12); }
.icon-red    { background: rgba(220,38,38,0.12); }
.card-title { font-family: 'Syne', sans-serif; font-size: 1.08rem; font-weight: 700; margin: 0; }
.card-body  { font-size: 1rem; line-height: 1.65; margin: 0; opacity: 0.75; }
</style>
""", unsafe_allow_html=True)


# ── Page Hero ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-hero">
    <div class="page-badge">Conclusion</div>
    <h1 class="page-title">Summary & Conclusion</h1>
    <p class="page-subtitle">
        A synthesis of all findings across eight research questions —
        what we learned, why it matters, and where the limits lie.
    </p>
</div>
""", unsafe_allow_html=True)


# ── SUMMARY OF RESULTS ──────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-blue">
    <span class="section-icon">📋</span>
    <p class="section-title">Summary of Results</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    This project investigated <span class="hl">eight research questions</span> about the behavior of
    six U.S. stocks (Apple, Microsoft, NVIDIA, J.P. Morgan, Goldman Sachs, Bank of America)
    using real market data from Alpha Vantage and FRED. Below is a summary of each finding.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="result-card">
    <div class="result-number">RQ1</div>
    <div>
        <p class="result-title">Return Analysis</p>
        <p class="result-desc">Both Apple and NVIDIA deviate significantly from a normal distribution. Their daily log-returns exhibit fat tails (leptokurtosis), meaning extreme price movements — both positive and negative — occur far more frequently than standard Gaussian models predict. This has direct implications for risk modeling.</p>
    </div>
</div>
<div class="result-card">
    <div class="result-number">RQ2</div>
    <div>
        <p class="result-title">Volatility & Trading Ranges</p>
        <p class="result-desc">Tech stocks show consistently higher daily trading ranges than financial stocks. NVIDIA leads in intraday volatility, while financial stocks exhibit tighter ranges under normal conditions. However, during stress events like rate decisions, financial stock volatility can spike sharply.</p>
    </div>
</div>
<div class="result-card">
    <div class="result-number">RQ3</div>
    <div>
        <p class="result-title">Technical Analysis (Volume Patterns)</p>
        <p class="result-desc">Volume spike patterns differ measurably between sectors. Tech stocks experience more frequent and more intense volume anomalies, driven by earnings surprises, AI-related news, and analyst activity. Financial stocks show fewer but more clustered spikes around macro events.</p>
    </div>
</div>
<div class="result-card">
    <div class="result-number">RQ4</div>
    <div>
        <p class="result-title">Market Phases</p>
        <p class="result-desc">Bull and bear phases can be systematically identified using a rolling 20-day window approach. Technology stocks react more dynamically to changing conditions and transition between phases more frequently, while financial stocks exhibit steadier, more gradual trend behavior.</p>
    </div>
</div>
<div class="result-card">
    <div class="result-number">RQ5</div>
    <div>
        <p class="result-title">Market Structure (VIX Stress Testing)</p>
        <p class="result-desc">Both Apple and NVIDIA show weaker performance during periods of elevated VIX. NVIDIA reacts more strongly to market stress with larger performance declines, while Apple remains comparatively more stable. The effect intensifies as the VIX threshold increases.</p>
    </div>
</div>
<div class="result-card">
    <div class="result-number">RQ6</div>
    <div>
        <p class="result-title">Risk Management</p>
        <p class="result-desc">NVIDIA carries significantly higher risk than Apple across all metrics. Its Value-at-Risk and Expected Shortfall are substantially larger, reflecting higher daily volatility. Critically, the Expected Shortfall consistently exceeds the VaR for both stocks, confirming that tail risks are underestimated by VaR-only approaches.</p>
    </div>
</div>
<div class="result-card">
    <div class="result-number">RQ7</div>
    <div>
        <p class="result-title">Company Fundamentals</p>
        <p class="result-desc">No statistically significant correlation was found between quarterly iPhone unit sales and Apple's 30-day post-earnings stock return. This is consistent with the Efficient Market Hypothesis — markets price in expected sales before earnings, so only surprises relative to consensus drive the post-announcement reaction.</p>
    </div>
</div>
<div class="result-card">
    <div class="result-number">RQ8</div>
    <div>
        <p class="result-title">Sentiment Correlation</p>
        <p class="result-desc">No statistically significant linear correlation was found between the Consumer Sentiment Index and monthly stock returns over the observed period. Consumer confidence alone is not a reliable predictor of short-term stock returns for either the tech or financial sector.</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ── SIGNIFICANCE ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-green">
    <span class="section-icon">💡</span>
    <p class="section-title">Significance of the Findings</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    Taken together, the eight research questions paint a consistent picture:
    <span class="hl">financial markets are more complex than simple models suggest</span>.
    Several key themes emerge across the analyses:
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-red">📉</div>
            <p class="card-title">Normal Distribution Is Insufficient</p>
        </div>
        <p class="card-body">
            RQ1 and RQ6 both demonstrate that assuming normally distributed returns leads
            to a systematic underestimation of risk. Fat tails are not an exception — they
            are a persistent feature of equity markets. Risk models must account for this
            to avoid dangerous blind spots.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-blue">⚖️</div>
            <p class="card-title">Tech vs. Financial: Structural Differences</p>
        </div>
        <p class="card-body">
            Across RQ2, RQ3, RQ4, and RQ5, a consistent pattern emerges: tech stocks are
            more volatile, more reactive to news, and more sensitive to market stress than
            financial stocks. These are not random fluctuations — they reflect fundamental
            differences in business models, investor base, and information flow.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-green">🔬</div>
            <p class="card-title">Negative Results Are Valid Results</p>
        </div>
        <p class="card-body">
            RQ7 and RQ8 found no statistically significant correlations. This is not a failure —
            it is an important scientific finding. It demonstrates that intuitive assumptions
            ("more iPhones sold = higher stock price") do not hold up under statistical testing,
            and that markets are more efficient at pricing in information than commonly believed.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-purple">🎯</div>
            <p class="card-title">Markets Price In Expectations</p>
        </div>
        <p class="card-body">
            The findings from RQ7 (iPhone sales) and RQ8 (consumer sentiment) both point to
            the same conclusion: stock prices react to surprises, not to absolute numbers.
            The market has already incorporated publicly available information — what matters
            is the deviation from consensus expectations.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-orange">🧩</div>
            <p class="card-title">Multi-Dimensional Analysis Is Essential</p>
        </div>
        <p class="card-body">
            No single metric — returns, volume, sentiment, or fundamentals — fully explains
            stock behavior. The value of this project lies in combining multiple perspectives:
            statistical analysis, risk modeling, market regime detection, and fundamental data.
            Each dimension reveals something the others miss.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-blue">📊</div>
            <p class="card-title">Interactive Analysis Over Static Reports</p>
        </div>
        <p class="card-body">
            By deploying the analysis as an interactive web application rather than a static
            PDF, users can adjust parameters (confidence levels, thresholds, stock selection)
            and see how results change in real time. This makes the analysis more transparent,
            reproducible, and accessible to non-technical audiences.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ── LIMITATIONS ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-orange">
    <span class="section-icon">⚠️</span>
    <p class="section-title">Limitations</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    <strong>Data window:</strong> The analysis is based on approximately 100 trading days of daily
    stock data (Alpha Vantage compact) and a limited number of monthly observations for sentiment
    analysis. Longer time series would increase statistical power and allow for more robust conclusions.
    <br><br>
    <strong>Sample size:</strong> Six stocks across two sectors provide a meaningful comparison,
    but do not represent the full breadth of the market. Results may not generalize to small-cap
    stocks, international markets, or other asset classes.
    <br><br>
    <strong>iPhone unit estimates:</strong> Apple has not officially reported iPhone unit sales
    since Q4 2018. The figures used in RQ7 are third-party estimates (Statista, IDC), which
    introduces measurement uncertainty.
    <br><br>
    <strong>No causal claims:</strong> All analyses are correlational. Correlation does not imply
    causation — observed relationships may be driven by unmodeled confounding factors such as
    monetary policy, geopolitical events, or broader economic cycles.
    <br><br>
    <strong>No transaction costs:</strong> The analysis does not account for trading costs,
    bid-ask spreads, or market impact — factors that would affect the practical implementation
    of any strategy derived from these findings.
</div>
""", unsafe_allow_html=True)


# ── FINAL STATEMENT ──────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-purple">
    <span class="section-icon">🏁</span>
    <p class="section-title">Final Statement</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    This project demonstrates that <span class="hl">data science methods can provide meaningful
    insights into stock market behavior</span> — but also that financial markets resist simple
    explanations. The most important takeaway is not any single finding, but the recognition
    that robust analysis requires multiple perspectives, honest reporting of negative results,
    and a clear understanding of methodological limitations.
    <br><br>
    The interactive nature of this application allows users to explore the data themselves,
    adjust parameters, and form their own conclusions — embodying the principle that
    <span class="hl">good data science is not about giving answers, but about enabling
    better questions</span>.
</div>
""", unsafe_allow_html=True)

st.caption("StockInsight — Data Science Project, Christian-Albrechts-Universität zu Kiel")
