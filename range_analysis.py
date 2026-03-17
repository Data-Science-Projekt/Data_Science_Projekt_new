import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from analysis.utils import render_page_header

# --- CONFIGURATION ---
# No API keys or local cache folder required anymore.
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
ALL_STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

# --- FUNCTION: LOAD DATA (LOCAL) ---
@st.cache_data(show_spinner="Loading historical trading data...")
def get_stock_data_local(symbol):
    """Reads the CSV file created by the bot from the data folder."""
    file_path = f"data/stock_{symbol}.csv"
    
    if not os.path.exists(file_path):
        return None
        
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        # Sort for correct time-series analysis
        df = df.astype(float).sort_index()
        
        # Calculation of the trading range
        # Column names from Alpha Vantage: 2. high, 3. low, 4. close
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
# Since the bot fetches 100 days by default, this is the maximum
days = st.sidebar.slider("Number of Trading Days", min_value=10, max_value=100, value=100, step=10)
selected_tech = st.sidebar.multiselect("Select Tech Stocks", list(TECH_STOCKS.keys()), default=list(TECH_STOCKS.keys()))
selected_financial = st.sidebar.multiselect("Select Financial Stocks", list(FINANCIAL_STOCKS.keys()), default=list(FINANCIAL_STOCKS.keys()))

if not selected_tech and not selected_financial:
    st.warning("Please select at least one stock.")
    st.stop()

# Combine selection
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
fig_box.update_layout(yaxis_title="Relative Trading Range (%)", template="plotly_white")
st.plotly_chart(fig_box, use_container_width=True)

# Time Series
st.subheader("Trading Range Trend Over Time")
fig_ts = go.Figure()
# Defined colors for better differentiation
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
for i, (name, df) in enumerate(stock_data.items()):
    fig_ts.add_trace(go.Scatter(x=df.index, y=df["relative_range_pct"], mode="lines", name=name, line=dict(color=colors[i % len(colors)], width=1.5)))
fig_ts.update_layout(xaxis_title="Date", yaxis_title="Relative Trading Range (%)", template="plotly_white")
st.plotly_chart(fig_ts, use_container_width=True)

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

tech_avg = np.mean(tech_ranges) if tech_ranges else 0
financial_avg = np.mean(financial_ranges) if financial_ranges else 0
diff = tech_avg - financial_avg

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Tech Avg. Range (%)", f"{tech_avg:.2f}")
with col2:
    st.metric("Financial Avg. Range (%)", f"{financial_avg:.2f}")
with col3:
    st.metric("Difference (Tech - Fin)", f"{diff:.2f}")

# Conclusion Text
st.subheader("Key Findings")
summary_logic = "Tech stocks show higher volatility in daily ranges." if diff > 0 else "Financial stocks show higher volatility." if diff < 0 else "Both sectors show similar trading ranges."
summary = f"""
The analysis of the last {len(stock_data[list(stock_data.keys())[0]])} trading days shows:
Tech stocks have an average range of {tech_avg:.2f}%, while Financial stocks average {financial_avg:.2f}%.
The difference is {diff:.2f} percentage points.
{summary_logic}
"""
st.write(summary)
