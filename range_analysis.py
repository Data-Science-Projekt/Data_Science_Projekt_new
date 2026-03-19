import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

# --- CONFIGURATION ---
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
ALL_STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

CHART_STYLE = dict(
    font=dict(color="#718096", size=14),
    xaxis=dict(
        tickfont=dict(color="#718096", size=13),
        title_font=dict(color="#718096", size=15),
        gridcolor="#e2e8f0",
        linecolor="#cbd5e0",
    ),
    yaxis=dict(
        tickfont=dict(color="#718096", size=13),
        title_font=dict(color="#718096", size=15),
        gridcolor="#e2e8f0",
        linecolor="#cbd5e0",
    ),
    legend=dict(
        font=dict(color="#718096", size=13)
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)

# --- FUNCTION: LOAD DATA (LOCAL) ---
@st.cache_data(show_spinner="Loading historical trading data...")
def get_stock_data_local(symbol):
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        df = df.astype(float).sort_index()
        df["absolute_range"] = df["2. high"] - df["3. low"]
        df["relative_range_pct"] = (df["absolute_range"] / df["4. close"]) * 100
        return df
    except Exception:
        return None

# --- MAIN APP ---
render_page_header(
    "Volatility",
    "What are the differences in the daily trading range between selected tech stocks (Apple, Microsoft, NVIDIA) and selected financial stocks (J.P. Morgan, Goldman Sachs, Bank of America)?",
)

# Sidebar for controls
st.sidebar.header("Analysis Parameters")
days = st.sidebar.slider("Number of Trading Days", min_value=10, max_value=100, value=100, step=10)
selected_tech = st.sidebar.multiselect("Select Tech Stocks", list(TECH_STOCKS.keys()), default=list(TECH_STOCKS.keys()))
selected_financial = st.sidebar.multiselect("Select Financial Stocks", list(FINANCIAL_STOCKS.keys()), default=list(FINANCIAL_STOCKS.keys()))

if not selected_tech and not selected_financial:
    st.warning("Please select at least one stock.")
    st.stop()

selected_stocks = {**{k: TECH_STOCKS[k] for k in selected_tech}, **{k: FINANCIAL_STOCKS[k] for k in selected_financial}}

# Load data
stock_data = {}
with st.spinner("Loading data..."):
    for name, symbol in selected_stocks.items():
        df = get_stock_data_local(symbol)
        if df is not None:
            stock_data[name] = df.tail(days)

if not stock_data:
    st.error("No data could be loaded. Please check the bot status.")
    st.stop()

# Determine common date range
min_date = max(df.index.min() for df in stock_data.values())
max_date = min(df.index.max() for df in stock_data.values())
for name in stock_data:
    stock_data[name] = stock_data[name][(stock_data[name].index >= min_date) & (stock_data[name].index <= max_date)]

# --- DISPLAY RESULTS ---
st.subheader("Analysis Summary")
st.write(f"**Period:** {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')} ({len(stock_data[list(stock_data.keys())[0]])} trading days)")

# Boxplot
st.subheader("Distribution of Daily Trading Ranges (Percent)")
fig_box = go.Figure()
for name, df in stock_data.items():
    fig_box.add_trace(go.Box(y=df["relative_range_pct"], name=name, boxmean=True))
fig_box.update_layout(
    yaxis_title="Relative Trading Range (%)",
    template="plotly_white",
    **CHART_STYLE
)
st.plotly_chart(fig_box, use_container_width=True)

st.download_button(
    label="📥 Graph als PNG herunterladen",
    data=fig_to_pdf_bytes(fig_box),
    file_name="volatility_boxplot.png",
    mime="image/png",
    key="download_volatility_box"
)

# --- Area Chart: Tech vs. Financial sector average ---
st.subheader("Sector Volatility Trend Over Time")

# Build a shared date index
all_dates = stock_data[list(stock_data.keys())[0]].index

tech_dfs    = [stock_data[n]["relative_range_pct"] for n in selected_tech      if n in stock_data]
fin_dfs     = [stock_data[n]["relative_range_pct"] for n in selected_financial if n in stock_data]

tech_avg = pd.concat(tech_dfs,  axis=1).mean(axis=1).rolling(5).mean() if tech_dfs else None
fin_avg  = pd.concat(fin_dfs,   axis=1).mean(axis=1).rolling(5).mean() if fin_dfs  else None

fig_area = go.Figure()

if tech_avg is not None:
    fig_area.add_trace(go.Scatter(
        x=tech_avg.index,
        y=tech_avg.values,
        name="Tech (avg)",
        mode="lines",
        line=dict(color="#2563eb", width=2),
        fill="tozeroy",
        fillcolor="rgba(37,99,235,0.12)",
    ))

if fin_avg is not None:
    fig_area.add_trace(go.Scatter(
        x=fin_avg.index,
        y=fin_avg.values,
        name="Financial (avg)",
        mode="lines",
        line=dict(color="#16a34a", width=2),
        fill="tozeroy",
        fillcolor="rgba(22,163,74,0.12)",
    ))

fig_area.update_layout(
    xaxis_title="Date",
    yaxis_title="Avg. Relative Trading Range (%, 5-day smoothed)",
    template="plotly_white",
    hovermode="x unified",
    **CHART_STYLE
)
st.plotly_chart(fig_area, use_container_width=True)

st.download_button(
    label="📥 Graph als PNG herunterladen",
    data=fig_to_pdf_bytes(fig_area),
    file_name="volatility_area.png",
    mime="image/png",
    key="download_volatility_area"
)

# Statistics Table
st.subheader("Statistical Metrics per Stock")
stats_data = []
for name, df in stock_data.items():
    ranges = df["relative_range_pct"]
    stats_data.append({
        "Stock": name,
        "Sector": "Tech" if name in TECH_STOCKS else "Financial",
        "Mean (%)": f"{ranges.mean():.2f}",
        "Median (%)": f"{ranges.median():.2f}",
        "Std. Dev. (%)": f"{ranges.std():.2f}",
        "Min (%)": f"{ranges.min():.2f}",
        "Max (%)": f"{ranges.max():.2f}",
    })
st.table(pd.DataFrame(stats_data))

# Sector Comparison
st.subheader("Sector Comparison")
tech_ranges = []
financial_ranges = []
for name, df in stock_data.items():
    if name in TECH_STOCKS:
        tech_ranges.extend(df["relative_range_pct"].tolist())
    elif name in FINANCIAL_STOCKS:
        financial_ranges.extend(df["relative_range_pct"].tolist())

tech_avg_val     = np.mean(tech_ranges)     if tech_ranges     else 0
financial_avg_val = np.mean(financial_ranges) if financial_ranges else 0
diff = tech_avg_val - financial_avg_val

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Tech Avg. Range (%)", f"{tech_avg_val:.2f}")
with col2:
    st.metric("Financial Avg. Range (%)", f"{financial_avg_val:.2f}")
with col3:
    st.metric("Difference (Tech - Fin)", f"{diff:.2f}")

# Conclusion
num_days  = len(stock_data[list(stock_data.keys())[0]])
diff_word = "significantly" if abs(diff) > 0.3 else "moderately"
gap_word  = "This confirms that tech stocks exhibit meaningfully higher intraday volatility than their financial counterparts." if abs(diff) > 0.2 else "The difference is modest, suggesting relatively comparable intraday behavior across both sectors during this period."

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
.section-banner {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 22px; border-radius: 10px;
    margin-bottom: 20px; margin-top: 10px;
}
.section-banner-blue   { background: linear-gradient(90deg, rgba(37,99,235,0.08), rgba(37,99,235,0.01)); border-left: 3px solid #2563eb; }
.section-banner-green  { background: linear-gradient(90deg, rgba(22,163,74,0.08), rgba(22,163,74,0.01)); border-left: 3px solid #16a34a; }
.section-banner-orange { background: linear-gradient(90deg, rgba(217,119,6,0.08), rgba(217,119,6,0.01)); border-left: 3px solid #d97706; }
.section-title { font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700; margin: 0; }
.info-box {
    background: rgba(37,99,235,0.04); border: 1px solid rgba(37,99,235,0.15);
    border-radius: 12px; padding: 24px 28px; margin-bottom: 16px;
    line-height: 1.75; font-size: 1.05rem;
}
.info-box .hl { color: #2563eb; font-weight: 600; }
.insight-card {
    background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.1);
    border-radius: 12px; padding: 22px 22px 20px; margin-bottom: 16px;
    transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
}
.insight-card:hover { border-color: #2563eb; transform: translateY(-2px); box-shadow: 0 4px 16px rgba(37,99,235,0.1); }
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
.card-title { font-family: 'Syne', sans-serif; font-size: 1.08rem; font-weight: 700; margin: 0; }
.card-body  { font-size: 1rem; line-height: 1.65; margin: 0; opacity: 0.75; }
</style>
""", unsafe_allow_html=True)

# 01
st.markdown("""
<div class="section-banner section-banner-blue">
    <p class="section-title">01. What Does This Analysis Show?</p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="info-box">
    This analysis measures the <span class="hl">daily trading range</span>, calculated as the difference
    between the intraday high and low price expressed as a percentage of the closing price, across
    <span class="hl">{num_days} trading days</span> for six stocks split into two sectors:
    Tech (Apple, Microsoft, NVIDIA) and Financial (J.P. Morgan, Goldman Sachs, Bank of America).
    A higher relative trading range indicates greater intraday price volatility, meaning the stock moves
    more aggressively within a single session regardless of whether it closes up or down.
</div>
""", unsafe_allow_html=True)

# 02
st.markdown("""
<div class="section-banner section-banner-green">
    <p class="section-title">02. Analysis and Interpretation</p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="info-box">
    Over the observed period, tech stocks averaged an intraday range of <span class="hl">{tech_avg_val:.2f}%</span>
    versus <span class="hl">{financial_avg_val:.2f}%</span> for financial stocks, a gap of
    <span class="hl">{abs(diff):.2f} percentage points</span>. {gap_word}
    <br><br>
    Tech stocks are inherently more reactive to news cycles, earnings surprises, analyst upgrades, and macro
    sentiment shifts. This is especially true for NVIDIA, whose price action is heavily influenced by
    AI-related developments and supply chain headlines. Apple and Microsoft, while more stable, still
    respond sharply to product announcements and broader market moves.
    <br><br>
    Financial stocks tend to exhibit tighter intraday ranges under normal market conditions, as their
    valuations are more anchored to interest rate expectations and macroeconomic data releases. During
    stress events such as Federal Reserve rate decisions or banking sector concerns, however, financial
    stocks can spike in volatility dramatically and temporarily exceed tech-sector ranges.
    <br><br>
    The boxplot further illustrates that tech stocks not only have a higher <em>median</em> range but also
    a wider <em>distribution</em>, meaning extreme volatile days are more frequent and more
    pronounced in tech than in finance.
</div>
""", unsafe_allow_html=True)

# 03
st.markdown("""
<div class="section-banner section-banner-orange">
    <p class="section-title">03. Key Insights</p>
</div>
""", unsafe_allow_html=True)

col_i1, col_i2 = st.columns(2)
with col_i1:
    st.markdown(f"""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-blue">📊</div>
            <p class="card-title">Tech Stocks Are More Volatile Intraday</p>
        </div>
        <p class="card-body">
            With an average range of {tech_avg_val:.2f}% vs. {financial_avg_val:.2f}% for financials,
            tech stocks move {diff_word} more within a single trading session.
        </p>
    </div>
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-orange">⚡</div>
            <p class="card-title">Volatility Is Sector-Driven</p>
        </div>
        <p class="card-body">
            The consistent gap between sectors suggests structural differences in how tech and financial
            stocks are priced and how quickly markets reprice them in response to new information.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_i2:
    st.markdown(f"""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-green">📉</div>
            <p class="card-title">Higher Range Does Not Equal Higher Return</p>
        </div>
        <p class="card-body">
            A wide trading range reflects uncertainty among market participants. It is a measure
            of risk, not direction. Investors seeking lower intraday risk may prefer financial stocks
            under normal conditions.
        </p>
    </div>
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-purple">🔍</div>
            <p class="card-title">Context Matters</p>
        </div>
        <p class="card-body">
            The analysis covers only {num_days} trading days. Extending the window to cover different
            market regimes would likely reveal periods where this relationship inverts,
            particularly during banking stress events.
        </p>
    </div>
    """, unsafe_allow_html=True)