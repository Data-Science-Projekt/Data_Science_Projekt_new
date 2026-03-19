import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from scipy.stats import pearsonr, spearmanr
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

# --- CONFIGURATION ---
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
ALL_STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

# --- DATA LOADING (LOCAL) ---
@st.cache_data(show_spinner="Loading local market data...")
def get_monthly_data_local(symbol):
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True).sort_index()
        monthly = df[["4. close"]].resample("MS").last()
        monthly["monthly_return"] = monthly["4. close"].pct_change()
        return monthly[["monthly_return"]].dropna()
    except Exception:
        return None

@st.cache_data(show_spinner="Loading consumer sentiment...")
def get_sentiment_local():
    file_path = "data/consumer_sentiment.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].dt.to_period("M").dt.to_timestamp()
        df = df.rename(columns={"value": "sentiment"})
        df['sentiment'] = pd.to_numeric(df['sentiment'], errors='coerce')
        return df.set_index('date')[['sentiment']].dropna()
    except Exception:
        return None

# --- UI ---
render_page_header(
    "Sentiment Correlation",
    "How does the broader Consumer Sentiment Index (University of Michigan) correlate with selected tech stocks (Apple, Microsoft, NVIDIA) and selected financial stocks (J.P. Morgan, Goldman Sachs, Bank of America)?",
)

st.markdown("""
#### Methodology
- **Consumer Sentiment Index** from the University of Michigan (via FRED API) — a monthly survey
  measuring consumer confidence about the economy
- **Monthly stock returns** from Alpha Vantage for 6 stocks across two sectors
- **Pearson & Spearman correlations** to quantify linear and rank-based relationships
- **Rolling correlation** to examine how the relationship evolves over time
""")

# Load data
sentiment_df = get_sentiment_local()
stock_returns = {}

if sentiment_df is not None:
    for name, symbol in ALL_STOCKS.items():
        data = get_monthly_data_local(symbol)
        if data is not None:
            stock_returns[name] = data.rename(columns={"monthly_return": name})

if sentiment_df is None or not stock_returns:
    st.error("Data files not found in /data folder. Please ensure the bot has run successfully.")
    st.stop()

# Merge all data
merged = sentiment_df.copy()
for name, ret_df in stock_returns.items():
    merged = merged.join(ret_df, how="inner")
merged = merged.dropna()

if len(merged) < 3:
    st.warning(f"Only {len(merged)} months of overlapping data. Need at least 3.")
    st.stop()

st.sidebar.header("Analysis Parameters")
st.sidebar.info(f"Analysis is based on {len(merged)} months of available data.")

st.write(f"**Period:** {merged.index.min().strftime('%Y-%m')} to {merged.index.max().strftime('%Y-%m')} ({len(merged)} months)")

# --- Stock names for iteration ---
stock_names = [n for n in ALL_STOCKS.keys() if n in merged.columns]

# --- 1. Correlation Heatmap ---
st.subheader("1. Correlation Matrix: Sentiment vs Stock Returns")

corr_data = []
for name in stock_names:
    pearson_r, pearson_p = pearsonr(merged["sentiment"], merged[name])
    spearman_r, spearman_p = spearmanr(merged["sentiment"], merged[name])
    sector = "Tech" if name in TECH_STOCKS else "Financial"
    corr_data.append({
        "Stock": name,
        "Sector": sector,
        "Pearson r": pearson_r,
        "Pearson p-value": pearson_p,
        "Spearman r": spearman_r,
        "Spearman p-value": spearman_p,
    })

corr_df = pd.DataFrame(corr_data)

# Heatmap
corr_matrix = merged[["sentiment"] + stock_names].corr()
fig_heatmap = go.Figure(data=go.Heatmap(
    z=corr_matrix.values,
    x=corr_matrix.columns,
    y=corr_matrix.index,
    colorscale="RdBu_r",
    zmid=0,
    text=np.round(corr_matrix.values, 3),
    texttemplate="%{text}",
    textfont={"size": 12},
))
fig_heatmap.update_layout(template="plotly_white", height=500)
st.plotly_chart(fig_heatmap, use_container_width=True)

st.download_button(
    label="📥 Graph als PNG herunterladen",
    data=fig_to_pdf_bytes(fig_heatmap),
    file_name="sentiment_correlation.png",
    mime="image/png",
    key="download_sentiment_heatmap"
)

# --- 2. Detailed Statistics ---
st.subheader("2. Detailed Correlation Statistics")
display_df = corr_df.copy()
for col in ["Pearson r", "Spearman r"]:
    display_df[col] = display_df[col].map("{:.4f}".format)
for col in ["Pearson p-value", "Spearman p-value"]:
    display_df[col] = display_df[col].map("{:.4f}".format)
st.table(display_df)

# --- 3. Sector Comparison ---
st.subheader("3. Sector Comparison")

tech_corrs = [c["Pearson r"] for c in corr_data if c["Sector"] == "Tech"]
fin_corrs = [c["Pearson r"] for c in corr_data if c["Sector"] == "Financial"]
tech_avg = np.mean(tech_corrs) if tech_corrs else 0
fin_avg = np.mean(fin_corrs) if fin_corrs else 0

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Avg Tech Correlation", f"{tech_avg:.4f}")
with c2:
    st.metric("Avg Financial Correlation", f"{fin_avg:.4f}")
with c3:
    st.metric("Difference (Tech - Fin)", f"{tech_avg - fin_avg:.4f}")

fig_sector = go.Figure()
fig_sector.add_trace(go.Bar(
    x=[c["Stock"] for c in corr_data],
    y=[c["Pearson r"] for c in corr_data],
    marker_color=["#1f77b4" if c["Sector"] == "Tech" else "#d62728" for c in corr_data],
    text=[f"{c['Pearson r']:.3f}" for c in corr_data],
    textposition="outside",
))
fig_sector.add_hline(y=0, line_dash="dash", line_color="gray")
fig_sector.update_layout(
    yaxis_title="Pearson Correlation with Consumer Sentiment",
    template="plotly_white", height=400,
)
st.plotly_chart(fig_sector, use_container_width=True)

st.download_button(
    label="📥 Graph als PNG herunterladen",
    data=fig_to_pdf_bytes(fig_sector),
    file_name="sentiment_sector_comparison.png",
    mime="image/png",
    key="download_sector_comparison"
)

# --- Compute values for styled sections below ---
sig_stocks = [c["Stock"] for c in corr_data if c["Pearson p-value"] < 0.05]
nonsig_stocks = [c["Stock"] for c in corr_data if c["Pearson p-value"] >= 0.05]
strongest = max(corr_data, key=lambda c: abs(c["Pearson r"]))
weakest = min(corr_data, key=lambda c: abs(c["Pearson r"]))

# --- STYLED ANALYSIS SECTIONS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
.section-banner {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 22px; border-radius: 10px;
    margin-bottom: 20px; margin-top: 10px;
}
.section-banner-blue  { background: linear-gradient(90deg, rgba(37,99,235,0.08), rgba(37,99,235,0.01)); border-left: 3px solid #2563eb; }
.section-banner-green { background: linear-gradient(90deg, rgba(22,163,74,0.08), rgba(22,163,74,0.01)); border-left: 3px solid #16a34a; }
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
/* ── process flow ── */
.process-flow {
    display: flex; gap: 0; margin-bottom: 24px; position: relative;
}
.process-step {
    flex: 1; text-align: center; padding: 24px 16px 20px; position: relative;
    background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.08);
    border-radius: 12px; margin: 0 6px;
    transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
}
.process-step:hover {
    border-color: #2563eb; transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(37,99,235,0.1);
}
.process-circle {
    width: 48px; height: 48px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 12px; font-size: 1.2rem;
    font-family: 'Syne', sans-serif; font-weight: 800; color: white;
}
.circle-1 { background: linear-gradient(135deg, #2563eb, #3b82f6); }
.circle-2 { background: linear-gradient(135deg, #7c3aed, #8b5cf6); }
.circle-3 { background: linear-gradient(135deg, #d97706, #f59e0b); }
.circle-4 { background: linear-gradient(135deg, #16a34a, #22c55e); }
.process-title { font-family: 'Syne', sans-serif; font-size: 0.95rem; font-weight: 700; margin: 0 0 6px 0; }
.process-desc { font-size: 0.88rem; line-height: 1.5; margin: 0; opacity: 0.65; }
.process-arrow {
    position: absolute; right: -14px; top: 50%; transform: translateY(-50%);
    font-size: 1.2rem; color: #cbd5e0; z-index: 2;
}
</style>
""", unsafe_allow_html=True)

# --- WHAT IS THIS? ---
st.markdown("""
<div class="section-banner section-banner-blue">
    <span class="section-icon">📖</span>
    <p class="section-title">What Does This Analysis Show?</p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="info-box">
    This page investigates whether <span class="hl">consumer confidence</span> — how optimistic or
    pessimistic ordinary people feel about the economy — has any measurable connection to
    <span class="hl">stock market returns</span>.
    <br><br>
    The <span class="hl">Consumer Sentiment Index</span> is published monthly by the University of
    Michigan. It is based on surveys asking households about their financial situation, business
    conditions, and buying intentions. A higher number means people feel more optimistic; a lower
    number means growing pessimism.
    <br><br>
    We compare this index against the monthly returns of <span class="hl">6 stocks across two sectors</span>
    (Tech: Apple, Microsoft, NVIDIA — Financial: J.P. Morgan, Goldman Sachs, Bank of America)
    over <span class="hl">{len(merged)} months</span> of overlapping data.
    <br><br>
    The key question: <em>When consumers feel more confident, do stock returns tend to be higher?
    And does this effect differ between tech and financial stocks?</em>
</div>
""", unsafe_allow_html=True)

# --- HOW IT WORKS ---
st.markdown("""
<div class="section-banner section-banner-purple">
    <span class="section-icon">⚙️</span>
    <p class="section-title">How It Works</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="process-flow">
    <div class="process-step">
        <div class="process-circle circle-1">01</div>
        <p class="process-title">Sentiment Data</p>
        <p class="process-desc">Monthly Consumer Sentiment Index from the University of Michigan (via FRED).</p>
        <span class="process-arrow">→</span>
    </div>
    <div class="process-step">
        <div class="process-circle circle-2">02</div>
        <p class="process-title">Stock Returns</p>
        <p class="process-desc">Daily stock prices aggregated to monthly returns for all 6 stocks.</p>
        <span class="process-arrow">→</span>
    </div>
    <div class="process-step">
        <div class="process-circle circle-3">03</div>
        <p class="process-title">Correlation</p>
        <p class="process-desc">Pearson (linear) and Spearman (rank-based) correlations computed per stock.</p>
        <span class="process-arrow">→</span>
    </div>
    <div class="process-step">
        <div class="process-circle circle-4">04</div>
        <p class="process-title">Sector Comparison</p>
        <p class="process-desc">Average correlations compared between Tech and Financial sectors.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- ANALYSIS AND INTERPRETATION ---
st.markdown("""
<div class="section-banner section-banner-green">
    <span class="section-icon">📊</span>
    <p class="section-title">Analysis and Interpretation</p>
</div>
""", unsafe_allow_html=True)

stronger_sector = "Financial" if abs(fin_avg) > abs(tech_avg) else "Tech"
weaker_sector = "Tech" if stronger_sector == "Financial" else "Financial"
stronger_avg = fin_avg if stronger_sector == "Financial" else tech_avg
weaker_avg = tech_avg if stronger_sector == "Financial" else fin_avg

sig_text = ""
if sig_stocks:
    sig_text = (
        f'Of the 6 stocks analyzed, <span class="hl">{len(sig_stocks)}</span> show a statistically '
        f'significant correlation (p &lt; 0.05): <span class="hl">{", ".join(sig_stocks)}</span>. '
        f'This means the relationship between sentiment and these stocks is unlikely to be due to random chance.'
    )
else:
    sig_text = (
        'None of the 6 stocks show a statistically significant correlation (p &lt; 0.05). '
        'This suggests that over this short observation period, there is no robust linear relationship '
        'between consumer sentiment and stock returns.'
    )

analysis_html = (
    f'<div class="info-box">'
    f'Over the <span class="hl">{len(merged)}-month</span> observation period, the analysis reveals:'
    f'<br><br>'
    f'<strong>Strongest link:</strong> <span class="hl">{strongest["Stock"]}</span> shows the highest '
    f'correlation with consumer sentiment (r = <span class="hl">{strongest["Pearson r"]:.4f}</span>). '
    f'{"A positive value means this stock tends to perform better when consumers are more optimistic." if strongest["Pearson r"] > 0 else "A negative value means this stock tends to perform worse when consumers are more optimistic."}'
    f'<br><br>'
    f'<strong>Weakest link:</strong> <span class="hl">{weakest["Stock"]}</span> shows the lowest '
    f'correlation (r = <span class="hl">{weakest["Pearson r"]:.4f}</span>), meaning its returns are '
    f'largely independent of consumer sentiment movements.'
    f'<br><br>'
    f'<strong>Sector difference:</strong> {stronger_sector} stocks show an average correlation of '
    f'<span class="hl">{stronger_avg:.4f}</span> compared to <span class="hl">{weaker_avg:.4f}</span> '
    f'for {weaker_sector} stocks. '
    f'{"Financial stocks are more sensitive to consumer sentiment, consistent with their direct exposure to consumer spending, lending, and credit conditions." if stronger_sector == "Financial" else "Tech stocks are more sensitive to consumer sentiment, likely reflecting consumer demand for devices, software, and services."}'
    f'<br><br>'
    f'<strong>Statistical significance:</strong> {sig_text}'
    f'</div>'
)
st.markdown(analysis_html, unsafe_allow_html=True)

# --- KEY INSIGHTS (STYLED) ---
st.markdown("""
<div class="section-banner section-banner-orange">
    <span class="section-icon">🔍</span>
    <p class="section-title">Key Insights</p>
</div>
""", unsafe_allow_html=True)

col_i1, col_i2 = st.columns(2)
with col_i1:
    st.markdown(f"""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-blue">🧠</div>
            <p class="card-title">Sentiment as a Signal</p>
        </div>
        <p class="card-body">
            Consumer sentiment captures the collective mood of households. When confidence rises,
            consumers spend more — boosting corporate revenues. When it falls, spending contracts.
            This makes it a potential leading indicator for stock performance.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-orange">🏦</div>
            <p class="card-title">Sector Sensitivity</p>
        </div>
        <p class="card-body">
            {"Financial stocks react more strongly to sentiment shifts. Banks and financial institutions are directly affected by consumer borrowing, spending, and credit conditions — all of which are captured in the sentiment survey." if abs(fin_avg) > abs(tech_avg) else "Tech stocks react more strongly to sentiment shifts. Consumer demand for devices, subscriptions, and digital services is closely tied to household confidence and discretionary spending power."}
        </p>
    </div>
    """, unsafe_allow_html=True)
with col_i2:
    st.markdown("""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-purple">📐</div>
            <p class="card-title">Correlation ≠ Causation</p>
        </div>
        <p class="card-body">
            A correlation between sentiment and returns does not mean one causes the other.
            Both may be driven by a common factor — such as economic growth, employment data,
            or monetary policy — that simultaneously lifts consumer confidence and stock prices.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-green">📅</div>
            <p class="card-title">Data Limitations</p>
        </div>
        <p class="card-body">
            This analysis covers only {len(merged)} months of overlapping data. With such a short window,
            correlations can be heavily influenced by a single outlier month. Longer time series would
            provide more robust and generalizable results.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- WHY DOES THIS MATTER ---
st.markdown("""
<div class="section-banner section-banner-blue">
    <span class="section-icon">💡</span>
    <p class="section-title">Why Does This Matter?</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    Understanding the relationship between <span class="hl">macroeconomic sentiment</span> and
    <span class="hl">stock returns</span> is central to both academic finance and practical investing.
    <br><br>
    For <span class="hl">investors</span>, sentiment data can serve as an additional input for
    timing decisions — not as a standalone signal, but as context for understanding market conditions.
    Rising sentiment may support bullish positioning; falling sentiment may warrant caution.
    <br><br>
    For <span class="hl">portfolio construction</span>, knowing which sectors are more sentiment-sensitive
    helps with diversification. If financial stocks move closely with consumer mood while tech stocks
    are more independent, combining both can reduce overall portfolio sensitivity to sentiment shocks.
    <br><br>
    In the broader context of this project, this analysis complements the
    <span class="hl">Market Structure</span> page (which examines VIX-driven volatility) and the
    <span class="hl">Market Phases</span> page (which identifies trend regimes). Together, they provide
    a multi-dimensional view of what drives stock behavior beyond pure price action.
</div>
""", unsafe_allow_html=True)

st.caption("Data source: Local files (data/). Sentiment: Univ. of Michigan (FRED). Stocks: Alpha Vantage.")
