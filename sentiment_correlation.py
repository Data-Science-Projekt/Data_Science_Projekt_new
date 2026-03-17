import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from scipy.stats import pearsonr, spearmanr

# --- CONFIGURATION ---
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
ALL_STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

# --- DATA LOADING ---
@st.cache_data
def get_monthly_data_local(symbol):
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path): return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True).sort_index()
        monthly = df[["4. close"]].resample("MS").last()
        monthly[f"{symbol}_return"] = monthly["4. close"].pct_change()
        return monthly[[f"{symbol}_return"]].dropna()
    except: return None

@st.cache_data
def get_sentiment_local():
    file_path = "data/consumer_sentiment.csv"
    if not os.path.exists(file_path): return None
    try:
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].dt.to_period("M").dt.to_timestamp()
        df = df.rename(columns={"value": "sentiment"})
        df['sentiment'] = pd.to_numeric(df['sentiment'], errors='coerce')
        return df.set_index('date')[['sentiment']].dropna()
    except: return None

# --- UI PREPARATION ---
st.title("Research Question 8: Sentiment Correlation")

sentiment_df = get_sentiment_local()
stock_returns = {}
if sentiment_df is not None:
    for name, symbol in ALL_STOCKS.items():
        data = get_monthly_data_local(symbol)
        if data is not None: stock_returns[name] = data.rename(columns={f"{symbol}_return": name})

# Check if we have any data at all
if sentiment_df is None or not stock_returns:
    st.error("No data found in /data. Please run the GitHub Bot first.")
    st.stop()

# Merge and determine available months
merged_all = sentiment_df.copy()
for name, ret_df in stock_returns.items():
    merged_all = merged_all.join(ret_df, how="inner")

available_months = len(merged_all)

# --- SIDEBAR WITH DYNAMIC LIMITS ---
st.sidebar.header("Analysis Parameters")
st.sidebar.info(f"Total months available in CSV: {available_months}")

# Lookback slider - cannot be larger than available data
lookback = st.sidebar.slider("Lookback period (months)", 
                             min_value=2, 
                             max_value=max(2, available_months), 
                             value=min(24, available_months))

# Rolling window - cannot be larger than the selected lookback
rolling_window = st.sidebar.slider("Rolling correlation window (months)", 
                                   min_value=2, 
                                   max_value=max(2, lookback), 
                                   value=min(6, lookback))

# --- FILTERING ---
merged = merged_all.tail(lookback)

# --- VISUALIZATION ---
st.write(f"**Current View:** Analyzing {len(merged)} months of data.")

# 1. Sentiment Chart
fig_sent = go.Figure()
fig_sent.add_trace(go.Scatter(x=merged.index, y=merged["sentiment"], mode="lines+markers", name="Sentiment"))
fig_sent.update_layout(title="Consumer Sentiment Index", template="plotly_white", height=300)
st.plotly_chart(fig_sent, use_container_width=True)

# 2. Statistics & Correlation
st.subheader("Correlation Analysis")
corr_results = []
for name in stock_returns.keys():
    if len(merged) > 2:
        r_p, _ = pearsonr(merged["sentiment"], merged[name])
        corr_results.append({"Stock": name, "Pearson r": round(r_p, 4)})

if corr_results:
    st.table(pd.DataFrame(corr_results))

# 3. Rolling Correlation
st.subheader(f"Rolling {rolling_window}-Month Correlation")
if len(merged) >= rolling_window:
    fig_rolling = go.Figure()
    for name in stock_returns.keys():
        rolling_corr = merged["sentiment"].rolling(rolling_window).corr(merged[name])
        fig_rolling.add_trace(go.Scatter(x=merged.index, y=rolling_corr, mode="lines", name=name))
    fig_rolling.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_rolling.update_layout(template="plotly_white", height=400)
    st.plotly_chart(fig_rolling, use_container_width=True)
else:
    st.warning(f"Increase data history to see the rolling {rolling_window}-month correlation.")

# --- INTERPRETATION ---
st.info("The correlation shows how much the stock market follows consumer confidence. "
        "With more data over time, these charts will become more expressive.")
