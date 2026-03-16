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
    # Kleiner Delay, um das 5-Requests-pro-Minute Limit nicht zu sprengen
    if symbol == "NVDA":
        time.sleep(2) 
        
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url, timeout=10).json()
        if "Time Series (Daily)" in r:
            df = pd.DataFrame.from_dict(r['Time Series (Daily)'], orient='index').astype(float).sort_index()
            return df['4. close'].pct_change().dropna()
        elif "Note" in r:
            st.error(f"API-Limit für {symbol} erreicht. Bitte Seite in 60 Sek. neu laden.")
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

# --- DATEN LADEN ---
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

    fig.update_layout(barmode='overlay', template="plotly_dark")
    st.plotly_chart(fig, width='stretch')

    # Metriken unter dem Chart
    c1, c2 = st.columns(2)
    if show_apple and ret_a is not None:
        c1.subheader("Apple")
        c1.metric("VaR", f"{v_a:.2%}")
        c1.metric("Expected Shortfall", f"{e_a:.2%}")
    if show_nvidia and ret_n is not None:
        c2.subheader("NVIDIA")
        c2.metric("VaR", f"{v_n:.2%}")
        c2.metric("Expected Shortfall", f"{e_n:.2%}")
else:
    st.info("Bitte wählen Sie Assets aus oder warten Sie auf die API-Antwort.")
