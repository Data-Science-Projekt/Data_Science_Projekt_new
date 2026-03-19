import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from scipy.stats import norm, kurtosis, skew
import os
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

# --- CONFIGURATION ---
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}


# --- FUNCTION: LOAD DATA (LOCAL CSV) ---
@st.cache_data(show_spinner="Loading stock data...")
def get_stock_data_local(symbol):
    file_path = os.path.join(os.path.dirname(__file__), "data", f"stock_{symbol}.csv")
    if not os.path.exists(file_path):
        st.warning(f"No data file found for {symbol}.")
        return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        df = df.astype(float).sort_index()
        df['log_return'] = np.log(df['4. close'] / df['4. close'].shift(1))
        return df.dropna()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


# --- FUNCTION: FRED BENCHMARK ---
@st.cache_data
def get_fred_benchmark(series_id="SP500"):
    if not FRED_API_KEY:
        return None
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
    except Exception:
        return None


# --- UI LAYOUT ---
render_page_header(
    "Return Analysis",
    "To what extent do the daily log returns of Apple and NVIDIA deviate from a normal distribution?",
)

st.info("⬅️ Use the **sidebar** to select a stock, adjust the lookback period, and toggle the S&P 500 benchmark.")

with st.sidebar:
    st.header("Settings")
    selected_stock = st.selectbox("Select stock:", list(STOCKS.keys()))

    days_to_show = st.slider("Lookback Period (last X trading days):",
                             min_value=5,
                             max_value=100,
                             value=100)

    show_benchmark = st.checkbox("Show S&P 500 (FRED)", value=True)

# Fetch data
df_stock_raw = get_stock_data_local(STOCKS[selected_stock])

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

    st.download_button(
        label="📥 Graph als PNG herunterladen",
        data=fig_to_pdf_bytes(fig),
        file_name="volatility_area.png",
        mime="image/png",
    )

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
            f"The log-returns of {selected_stock} show signs of **Leptokurtosis** (Excess Kurtosis = {k_val:.2f} > 0), indicating 'fatter tails' than a normal distribution. Extreme price movements occur more frequently than a Gaussian model would predict.")
    else:
        st.write(f"Over this period, the distribution of {selected_stock} remains relatively close to the normal model (Excess Kurtosis = {k_val:.2f}).")
