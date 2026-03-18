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

# --- DATA LOADING (LOCAL) ---
@st.cache_data(show_spinner="Loading local market data...")
def get_monthly_data_local(symbol):
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True).sort_index()
        monthly = df[["4. close"]].resample("MS").last()
        monthly[f"{symbol}_return"] = monthly["4. close"].pct_change()
        return monthly[[f"{symbol}_return"]].dropna()
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
    "How does the broader Consumer Sentiment Index correlate with selected tech stocks (Apple, Microsoft, NVIDIA) and selected financial stocks (J.P. Morgan, Goldman Sachs, Bank of America)?",
)

# Load data first to know actual range
sentiment_df = get_sentiment_local()
stock_returns = {}

if sentiment_df is not None:
    for name, symbol in ALL_STOCKS.items():
        data = get_monthly_data_local(symbol)
        if data is not None:
            stock_returns[name] = data.rename(columns={f"{symbol}_return": name})

if sentiment_df is None or not stock_returns:
    st.error("Data files not found in /data folder. Please ensure the bot has run successfully.")
    st.stop()

# Merge to find actual available months
merged_all = sentiment_df.copy()
for name, ret_df in stock_returns.items():
    merged_all = merged_all.join(ret_df, how="inner")
merged_all = merged_all.dropna()

max_months = len(merged_all)  # typically 4–5 with 100 trading days

# Sidebar — sliders bounded by actual data
st.sidebar.header("Analysis Parameters")
st.sidebar.caption(f"Available data: {max_months} months")

if max_months < 4:
    st.error(f"Not enough monthly data points ({max_months}) for a meaningful analysis. At least 4 months are required.")
    st.stop()

lookback_months = st.sidebar.slider(
    "Lookback period (months)",
    min_value=2,
    max_value=max_months,
    value=max_months,
)
rolling_window = st.sidebar.slider(
    "Rolling correlation window (months)",
    min_value=2,
    max_value=lookback_months - 1,
    value=2,
)

# Apply lookback filter
merged = merged_all.tail(lookback_months)

if len(merged) < rolling_window:
    st.warning(f"Not enough data for a {rolling_window}-month window. Currently showing all {len(merged)} available months.")
    effective_window = max(2, len(merged))
else:
    effective_window = rolling_window

st.write(f"**Analysis Period:** {merged.index.min().strftime('%Y-%m')} to {merged.index.max().strftime('%Y-%m')} ({len(merged)} months)")

# --- 1. SENTIMENT VISUALIZATION ---
st.subheader("1. Consumer Sentiment Index Over Time")
fig_sent = go.Figure()
fig_sent.add_trace(go.Scatter(
    x=merged.index, y=merged["sentiment"],
    mode="lines+markers", name="Consumer Sentiment",
    line=dict(color="#1f77b4", width=2)
))
fig_sent.update_layout(
    yaxis_title="Sentiment Index",
    template="plotly_white",
    height=400,
    **CHART_STYLE
)
st.plotly_chart(fig_sent, use_container_width=True)

st.download_button(
    label="📥 Graph als PNG herunterladen",
    data=fig_to_pdf_bytes(fig_sent),
    file_name="sentiment_index.png",
    mime="image/png",
    key="download_sentiment_index"
)

# --- 2. CORRELATION MATRIX ---
st.subheader("2. Correlation Matrix")
stock_names = list(stock_returns.keys())
corr_matrix = merged[["sentiment"] + stock_names].corr()

fig_heatmap = go.Figure(data=go.Heatmap(
    z=corr_matrix.values,
    x=corr_matrix.columns,
    y=corr_matrix.index,
    colorscale="RdBu_r",
    zmid=0,
    text=np.round(corr_matrix.values, 3),
    texttemplate="%{text}"
))
fig_heatmap.update_layout(
    template="plotly_white",
    height=500,
    font=dict(color="#718096", size=14),
    xaxis=dict(tickfont=dict(color="#718096", size=13)),
    yaxis=dict(tickfont=dict(color="#718096", size=13)),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_heatmap, use_container_width=True)

st.download_button(
    label="📥 Graph als PNG herunterladen",
    data=fig_to_pdf_bytes(fig_heatmap),
    file_name="sentiment_correlation.png",
    mime="image/png",
    key="download_sentiment_heatmap"
)

# --- 3. DETAILED STATISTICS ---
st.subheader("3. Detailed Correlation Statistics")
corr_results = []
for name in stock_names:
    r_p, p_p = pearsonr(merged["sentiment"], merged[name])
    r_s, p_s = spearmanr(merged["sentiment"], merged[name])
    corr_results.append({
        "Stock": name,
        "Sector": "Tech" if name in TECH_STOCKS else "Financial",
        "Pearson r": round(r_p, 4),
        "P-Value": round(p_p, 4),
        "Spearman r": round(r_s, 4)
    })
st.table(pd.DataFrame(corr_results))

# --- 4. KEY INSIGHTS ---
st.subheader("4. Key Insights")

avg_tech = np.mean([c["Pearson r"] for c in corr_results if c["Sector"] == "Tech"])
avg_fin = np.mean([c["Pearson r"] for c in corr_results if c["Sector"] == "Financial"])

summary_text = f"""
Based on the analysis of the selected {len(merged)} months:

- **Average Tech correlation:** {avg_tech:.4f}
- **Average Financial correlation:** {avg_fin:.4f}

**Interpretation:**
1. **Positive values** indicate that rising consumer optimism is associated with higher stock returns.
2. **Financial stocks** often show higher sensitivity to sentiment as it relates to consumer credit and spending.
3. **Tech stocks** react to sentiment as a leading indicator for discretionary spending on tech hardware/services.
4. **Statistical significance** (P-value < 0.05) suggests the relationship is robust and not due to random noise.
"""
st.markdown(summary_text)
st.caption("Data source: Local files (data/). Sentiment: Univ. of Michigan (FRED). Stocks: Alpha Vantage.")