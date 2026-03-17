import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import time

# --- CONFIG ---
AV_API_KEY = st.secrets.get("AV_API_KEY", "")
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}


@st.cache_data(show_spinner=False)
def get_stock_returns(symbol):
    # Small delay to avoid hitting the 5-requests-per-minute API limit
    if symbol == "NVDA":
        time.sleep(2)

    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url, timeout=10).json()
        if "Time Series (Daily)" in r:
            df = pd.DataFrame.from_dict(r['Time Series (Daily)'], orient='index').astype(float).sort_index()
            return df['4. close'].pct_change().dropna()
        elif "Note" in r:
            st.error(f"API Limit for {symbol} reached. Please reload in 60 seconds.")
            return None
    except:
        return None
    return None


# --- SIDEBAR ---
st.sidebar.header("Risk Settings")
conf_level = st.sidebar.slider("Confidence Level (%)", 90.0, 99.0, 95.0, 0.5) / 100
st.sidebar.divider()
show_apple = st.sidebar.checkbox("Show Apple (AAPL)", value=True, key="risk_a")
show_nvidia = st.sidebar.checkbox("Show NVIDIA (NVDA)", value=True, key="risk_n")

st.title("Value-at-Risk (VaR) & Expected Shortfall")
st.write("Quantifying potential losses and tail risks for individual assets.")

# --- DATA LOADING ---
data_load_info = st.empty()
ret_a = None
ret_n = None

if show_apple:
    ret_a = get_stock_returns(STOCKS["Apple"])
if show_nvidia:
    ret_n = get_stock_returns(STOCKS["NVIDIA"])

# --- PLOTTING ---
if (show_apple and ret_a is not None) or (show_nvidia and ret_n is not None):
    fig = go.Figure()

    if show_apple and ret_a is not None:
        v_a = np.percentile(ret_a, (1 - conf_level) * 100)
        e_a = ret_a[ret_a <= v_a].mean()
        fig.add_trace(go.Histogram(x=ret_a, name="Apple", marker_color='#1f77b4', opacity=0.6))
        fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4", annotation_text=f"VaR AAPL")

    if show_nvidia and ret_n is not None:
        v_n = np.percentile(ret_n, (1 - conf_level) * 100)
        e_n = ret_n[ret_n <= v_n].mean()
        fig.add_trace(go.Histogram(x=ret_n, name="NVIDIA", marker_color='#ff7f0e', opacity=0.6))
        fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e", annotation_text=f"VaR NVDA")

    fig.update_layout(
        barmode='overlay',
        template="plotly_dark",
        xaxis_title="Daily Return",
        yaxis_title="Frequency",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Metrics below the chart
    c1, c2 = st.columns(2)
    if show_apple and ret_a is not None:
        c1.subheader("Apple (AAPL)")
        c1.metric("Value-at-Risk", f"{v_a:.2%}")
        c1.metric("Expected Shortfall", f"{e_a:.2%}")
    if show_nvidia and ret_n is not None:
        c2.subheader("NVIDIA (NVDA)")
        c2.metric("Value-at-Risk", f"{v_n:.2%}")
        c2.metric("Expected Shortfall", f"{e_n:.2%}")

    # --- INTERPRETATION & EXPLANATION ---
    st.markdown("---")
    st.subheader("Analysis & Interpretation")

    st.info(f"""
    **Risk Metrics Definition:**
    - **Value-at-Risk (VaR):** Represents the maximum expected loss over a specific time horizon at a given confidence level ({conf_level * 100:.1f}%). 
    - **Expected Shortfall (CVaR):** Represents the average loss that occurs when the VaR threshold is breached (the 'average of the worst cases').
    """)

    st.markdown("""
    ### Key Insights:

    * **Tail Risk Assessment:** While the standard deviation (volatility) measures general uncertainty, **VaR** and **Expected Shortfall** focus specifically on the "left tail" of the distribution—where the most significant losses happen.

    * **Apple vs. NVIDIA:** - Generally, NVIDIA tends to have a **deeper VaR** than Apple, reflecting its higher historical volatility and beta. 
        - A larger gap between VaR and Expected Shortfall indicates **"Fat Tails"** (Leptokurtosis), meaning extreme crashes are more likely than a normal distribution would predict.

    * **The Confidence Level Impact:** - Increasing the confidence level (e.g., from 95% to 99%) shifts the VaR line further to the left, capturing more extreme but less frequent events. 
        - Investors with low risk tolerance should focus on the **Expected Shortfall**, as it provides a more realistic picture of potential damage during a market crisis.

    * **Limitations:** These metrics are based on historical data (last 100 trading days). They assume that future market behavior will resemble the past, which may not hold true during unprecedented "Black Swan" events.
    """)

    st.caption("Calculation: Historical simulation based on the latest 100 trading days of data from Alpha Vantage.")

else:
    st.info("Please select assets or wait for the API response.")
