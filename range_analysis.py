import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import os
import time

# --- CONFIGURATION ---
AV_API_KEY = st.secrets.get("AV_API_KEY", "")
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
ALL_STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

# --- FILE-BASED CACHE (survives restarts) ---
CACHE_DIR = os.path.join(os.path.dirname(__file__), "data", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(key):
    return os.path.join(CACHE_DIR, f"{key}.csv")


def _save_to_disk(key, df):
    """Save DataFrame to disk cache."""
    try:
        df.to_csv(_cache_path(key))
    except Exception:
        pass


def _load_from_disk(key):
    """Load DataFrame from disk cache if it exists."""
    path = _cache_path(key)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            return df
        except Exception:
            pass
    return None



# --- FUNCTION: LOAD DATA (ALPHA VANTAGE - COMPACT ONLY) ---
_av_last_call = [0.0]  # track last API call time for rate limiting

@st.cache_data(show_spinner="Fetching latest 100 days...")
def get_stock_data_compact(symbol):
    # Rate limit: wait if last API call was less than 15s ago
    elapsed = time.time() - _av_last_call[0]
    if elapsed < 15:
        time.sleep(15 - elapsed)
    _av_last_call[0] = time.time()

    # 'compact' returns the latest 100 data points (Free Tier limit)
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url, timeout=15)
        data = r.json()

        if "Note" in data or "Information" in data:
            # API limit — try disk cache
            cached = _load_from_disk(f"stock_{symbol}")
            if cached is not None:
                st.warning(f"API limit reached for {symbol}. Using cached data.")
                return cached
            st.error(f"API limit reached for {symbol} and no cached data available.")
            return None

        if "Time Series (Daily)" not in data:
            cached = _load_from_disk(f"stock_{symbol}")
            if cached is not None:
                st.warning(f"No fresh data for {symbol}. Using cached data.")
                return cached
            st.error(f"No data found for {symbol}. Check if the market is open or the API key is valid.")
            return None

        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
        df.index = pd.to_datetime(df.index)
        df = df.astype(float).sort_index()
        df["absolute_range"] = df["2. high"] - df["3. low"]
        df["relative_range_pct"] = (df["absolute_range"] / df["4. close"]) * 100

        # Save to disk for future fallback
        _save_to_disk(f"stock_{symbol}", df)

        return df
    except Exception as e:
        cached = _load_from_disk(f"stock_{symbol}")
        if cached is not None:
            st.warning(f"Connection error for {symbol}. Using cached data.")
            return cached
        st.error(f"Connection Error for {symbol}: {e}")
        return None

# --- MAIN APP ---
st.title("Research Question 2: Daily Trading Ranges")
st.markdown("""
**Research Question:** What are the differences in the daily trading range between selected tech stocks (Apple, Microsoft, NVIDIA) and selected financial stocks (J.P. Morgan, Goldman Sachs, Bank of America)?
""")

# Sidebar for controls
st.sidebar.header("Analysis Parameters")
days = st.sidebar.slider("Number of Trading Days", min_value=30, max_value=100, value=100, step=10)
selected_tech = st.sidebar.multiselect("Select Tech Stocks", list(TECH_STOCKS.keys()), default=list(TECH_STOCKS.keys()))
selected_financial = st.sidebar.multiselect("Select Financial Stocks", list(FINANCIAL_STOCKS.keys()), default=list(FINANCIAL_STOCKS.keys()))

if not selected_tech and not selected_financial:
    st.warning("Please select at least one stock.")
    st.stop()

selected_stocks = {**{k: TECH_STOCKS[k] for k in selected_tech}, **{k: FINANCIAL_STOCKS[k] for k in selected_financial}}

# Fetch data
stock_data = {}
with st.spinner("Loading data..."):
    for name, symbol in selected_stocks.items():
        df = get_stock_data_compact(symbol)
        if df is not None:
            stock_data[name] = df.tail(days)

if not stock_data:
    st.error("No data could be loaded.")
    st.stop()

# Determine common date range
min_date = max(df.index.min() for df in stock_data.values())
max_date = min(df.index.max() for df in stock_data.values())
for name in stock_data:
    stock_data[name] = stock_data[name][(stock_data[name].index >= min_date) & (stock_data[name].index <= max_date)]

# --- DISPLAY RESULTS ---
st.subheader("Analysis Summary")
st.write(f"**Period:** {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')} ({len(stock_data[list(stock_data.keys())[0]])} trading days)")

# Box plot
st.subheader("Distribution of Daily Range Percentages")
fig_box = go.Figure()
for name, df in stock_data.items():
    fig_box.add_trace(go.Box(y=df["relative_range_pct"], name=name, boxmean=True))
fig_box.update_layout(yaxis_title="Relative Daily Range (%)", template="plotly_white")
st.plotly_chart(fig_box, use_container_width=True)

# Time series
st.subheader("Daily Range Percentages Over Time")
fig_ts = go.Figure()
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
for i, (name, df) in enumerate(stock_data.items()):
    fig_ts.add_trace(go.Scatter(x=df.index, y=df["relative_range_pct"], mode="lines", name=name, line=dict(color=colors[i % len(colors)], width=1)))
fig_ts.update_layout(xaxis_title="Date", yaxis_title="Relative Daily Range (%)", template="plotly_white")
st.plotly_chart(fig_ts, use_container_width=True)

# Statistics table
st.subheader("Summary Statistics per Stock")
stats_data = []
for name, df in stock_data.items():
    ranges = df["relative_range_pct"]
    stats_data.append({
        "Stock": name,
        "Mean (%)": f"{ranges.mean():.2f}",
        "Median (%)": f"{ranges.median():.2f}",
        "Std Dev (%)": f"{ranges.std():.2f}",
        "Min (%)": f"{ranges.min():.2f}",
        "Max (%)": f"{ranges.max():.2f}",
    })
st.table(pd.DataFrame(stats_data))

# Sector comparison
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
    st.metric("Tech Avg Range (%)", f"{tech_avg:.2f}")
with col2:
    st.metric("Financial Avg Range (%)", f"{financial_avg:.2f}")
with col3:
    st.metric("Difference (Tech - Financial)", f"{diff:.2f}")

# Summary text
st.subheader("Key Insights")
summary = f"""
Analysis of daily trading ranges for the last {len(stock_data[list(stock_data.keys())[0]])} trading days from {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}.
Tech stocks show an average daily range of {tech_avg:.2f}%, while financial stocks average {financial_avg:.2f}%.
The difference is {diff:.2f}%.
{'Tech stocks exhibit higher volatility in daily ranges.' if diff > 0 else 'Financial stocks exhibit higher volatility in daily ranges.' if diff < 0 else 'Both sectors show similar daily range volatility.'}
"""
st.write(summary)
