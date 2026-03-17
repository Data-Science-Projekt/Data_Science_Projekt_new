import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from scipy.stats import pearsonr, spearmanr

# --- CONFIGURATION ---
# Sectors are based on files created by the bot
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
ALL_STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

# --- FUNCTION: LOAD DATA (LOCAL) ---
@st.cache_data(show_spinner="Loading local market data...")
def get_monthly_data_local(symbol):
    """Reads daily stock data and aggregates it to monthly frequency."""
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path):
        return None
    try:
        # Read CSV created by the bot
        df = pd.read_csv(file_path, index_col=0, parse_dates=True).sort_index()
        # Aggregate to month start (MS) for comparability with FRED
        monthly = df[["4. close"]].resample("MS").last()
        monthly[f"{symbol}_return"] = monthly["4. close"].pct_change()
        return monthly[[f"{symbol}_return"]].dropna()
    except Exception:
        return None

@st.cache_data(show_spinner="Loading consumer sentiment...")
def get_sentiment_local():
    """Reads the Consumer Sentiment Index from local CSV."""
    file_path = "data/consumer_sentiment.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        # Normalize date format
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].dt.to_period("M").dt.to_timestamp()
        df = df.rename(columns={"value": "sentiment"})
        # Clean FRED data (convert invalid values to NaN)
        df['sentiment'] = pd.to_numeric(df['sentiment'], errors='coerce')
        return df.set_index('date')[['sentiment']].dropna()
    except Exception:
        return None

# --- UI ---
st.title("Research Question 8: Sentiment Correlation")
st.markdown("""
**Research Question:** How does the Consumer Sentiment Index (University of Michigan)  
correlate with selected tech stocks and financial stocks?
""")

# Sidebar
st.sidebar.header("Analysis Parameters")
lookback_months = st.sidebar.slider("Lookback period (months)", 6, 48, 24)
rolling_window = st.sidebar.slider("Rolling correlation window (months)", 3, 12, 6)

# Load data
sentiment_df = get_sentiment_local()
stock_returns = {}

if sentiment_df is not None:
    for name, symbol in ALL_STOCKS.items():
        df = get_monthly_data_local(symbol)
        if df is not None:
            stock_returns[name] = df.rename(columns={f"{symbol}_return": name})

if sentiment_df is None or not stock_returns:
    st.error("Data could not be loaded. Please check the bot status in the repository.")
    st.stop()

# Merge datasets
merged = sentiment_df.copy()
for name, ret_df in stock_returns.items():
    merged = merged.join(ret_df, how="inner")

# Filter time period
merged = merged.tail(lookback_months).dropna()

if len(merged) < 3:
    st.warning("Not enough overlapping data points available.")
    st.stop()

st.write(f"**Period:** {merged.index.min().strftime('%Y-%m')} to {merged.index.max().strftime('%Y-%m')}")

# --- 1. SENTIMENT VISUALIZATION ---
st.subheader("1. Consumer Sentiment Index Over Time")
fig_sent = go.Figure()
fig_sent.add_trace(go.Scatter(
    x=merged.index, y=merged["sentiment"],
    mode="lines+markers", name="Consumer Sentiment",
    line=dict(color="#1f77b4", width=2)
))
fig_sent.update_layout(yaxis_title="Sentiment Index", template="plotly_white", height=400)
st.plotly_chart(fig_sent, use_container_width=True)

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
fig_heatmap.update_layout(template="plotly_white", height=500)
st.plotly_chart(fig_heatmap, use_container_width=True)

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
        "P-Value (P)": round(p_p, 4),
        "Spearman r": round(r_s, 4)
    })
st.table(pd.DataFrame(corr_results))

# --- 4. ROLLING CORRELATION ---
st.subheader("4. Time Evolution (Rolling Correlation)")
fig_rolling = go.Figure()
for name in stock_names:
    rolling_corr = merged["sentiment"].rolling(rolling_window).corr(merged[name])
    fig_rolling.add_trace(go.Scatter(x=merged.index, y=rolling_corr, mode="lines", name=name))

fig_rolling.add_hline(y=0, line_dash="dash", line_color="gray")
fig_rolling.update_layout(
    yaxis_title=f"Rolling {rolling_window}-month correlation",
    template="plotly_white", height=500
)
st.plotly_chart(fig_rolling, use_container_width=True)

# --- 5. INTERPRETATION ---
st.subheader("5. Key Insights")

# Calculate sector averages
avg_tech = np.mean([c["Pearson r"] for c in corr_results if c["Sector"] == "Tech"])
avg_fin = np.mean([c["Pearson r"] for c in corr_results if c["Sector"] == "Financial"])

summary_text = f"""
Based on the analysis of the last {len(merged)} months, the following insights emerge:

- **Average Tech correlation:** {avg_tech:.4f}
- **Average Financial correlation:** {avg_fin:.4f}

**Interpretation of the results:**
1. Positive values indicate that rising consumer optimism is associated with higher stock returns.
2. Financial stocks often show direct sensitivity to consumer sentiment, as it is closely linked to credit demand.
3. Tech stocks tend to react to sentiment as it serves as a leading indicator for spending on hardware and software services.
4. Statistical significance (P-value < 0.05) indicates whether the observed relationship is robust or likely due to chance.
"""

st.markdown(summary_text)
st.caption("Data source: Local (aggregated via bot). Sentiment: Univ. of Michigan (FRED). Stocks: Alpha Vantage.")
