import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from scipy.stats import norm, kurtosis, skew

# --- CONFIGURATION ---
AV_API_KEY = "REMOVED_AV_KEY".strip()
FRED_API_KEY = "REMOVED_FRED_KEY".strip()
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}

st.set_page_config(page_title="Financial Analysis: RQ1", layout="wide")


# --- FUNCTION: LOAD DATA (ALPHA VANTAGE - COMPACT ONLY) ---
@st.cache_data(show_spinner="Fetching latest 100 days...")
def get_stock_data_compact(symbol):
    # 'compact' returns the latest 100 data points (Free Tier limit)
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url)
        data = r.json()

        if "Note" in data:
            st.error("API Rate Limit reached. Please wait 60 seconds.")
            return None

        if "Time Series (Daily)" in data:
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float).sort_index()
            # Calculate log returns
            df['log_return'] = np.log(df['4. close'] / df['4. close'].shift(1))
            return df.dropna()
        else:
            st.warning("No data found. Check if the market is open or API key is valid.")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None


# --- FUNCTION: FRED BENCHMARK ---
@st.cache_data
def get_fred_benchmark(series_id="SP500"):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json"}
    try:
        r = requests.get(url, params=params)
        data = r.json()
        df = pd.DataFrame(data['observations'])
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df.set_index('date').dropna()
        df['log_return'] = np.log(df['value'] / df['value'].shift(1))
        return df.dropna()
    except:
        return None


# --- UI LAYOUT ---
st.title("Return Distribution Analysis (Latest 100 Days)")
st.markdown("**Research Question 1:** How do recent daily log-returns deviate from a normal distribution?")

with st.sidebar:
    st.header("Settings")
    selected_stock = st.selectbox("Select stock:", list(STOCKS.keys()))

    # Slider restricted to 100 days due to API limitations
    days_to_show = st.slider("Lookback Period (last X trading days):",
                             min_value=5,
                             max_value=100,
                             value=100)

    show_benchmark = st.checkbox("Show S&P 500 (FRED)", value=True)
    st.divider()
    st.info("Note: Alpha Vantage Free Tier is limited to the most recent 100 days.")

# Fetch data
df_stock_raw = get_stock_data_compact(STOCKS[selected_stock])

if df_stock_raw is not None:
    # Slice the data based on slider
    df_filtered = df_stock_raw.tail(days_to_show)
    returns = df_filtered['log_return']

    # Date Info
    st.caption(
        f"Showing last {len(df_filtered)} days from {df_filtered.index.min().date()} to {df_filtered.index.max().date()}")

    # Plotting
    fig = go.Figure()

    # 1. Stock Histogram
    fig.add_trace(go.Histogram(
        x=returns, nbinsx=30, name=f'{selected_stock}',
        histnorm='probability density', marker_color='#1f77b4', opacity=0.6
    ))

    # 2. FRED Benchmark
    if show_benchmark:
        df_fred_all = get_fred_benchmark()
        if df_fred_all is not None:
            df_fred = df_fred_all[df_fred_all.index >= df_filtered.index.min()]
            fig.add_trace(go.Histogram(
                x=df_fred['log_return'], nbinsx=30, name='S&P 500',
                histnorm='probability density', marker_color='#ff7f0e', opacity=0.4
            ))

    # 3. Normal Distribution Reference
    mu, std = norm.fit(returns)
    x_range = np.linspace(returns.min(), returns.max(), 100)
    y_norm = norm.pdf(x_range, mu, std)
    fig.add_trace(
        go.Scatter(x=x_range, y=y_norm, mode='lines', name='Normal Dist.', line=dict(color='red', dash='dash')))

    fig.update_layout(
        title=f"Distribution of Log-Returns: {selected_stock}",
        barmode='overlay',
        template="plotly_white",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Metrics Board
    k_val = kurtosis(returns)  # Excess Kurtosis
    s_val = skew(returns)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Excess Kurtosis", f"{k_val:.2f}")
    c2.metric("Skewness", f"{s_val:.2f}")
    c3.metric("Volatility", f"{std:.4f}")
    c4.metric("Mean", f"{mu:.5f}")

    # Short Analysis
    st.subheader("Analysis Summary")
    if k_val > 0.5:
        st.write(
            f"Even within the last 100 days, {selected_stock} shows signs of **Leptokurtosis** (Kurtosis > 0), indicating 'fatter tails' than a normal distribution.")
    else:
        st.write("Over this short-term period, the distribution remains relatively close to the normal model.")