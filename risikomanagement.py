import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

# --- CONFIG ---
AV_API_KEY = st.secrets.get("AV_API_KEY", "")
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}

@st.cache_data(show_spinner="Lade Daten...")
def get_stock_returns(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url, timeout=10).json()
        if "Time Series (Daily)" in r:
            df = pd.DataFrame.from_dict(r['Time Series (Daily)'], orient='index').astype(float).sort_index()
            return df['4. close'].pct_change().dropna()
        return None
    except:
        return None

# --- SIDEBAR ---
st.sidebar.header("Risk Settings")
conf_level = st.sidebar.slider("Confidence Level (%)", 90.0, 99.0, 95.0, 0.5) / 100

st.sidebar.divider()
st.sidebar.write("**Asset Selection:**")

# Wichtig: Eindeutige Keys für die Checkboxen vergeben
show_apple = st.sidebar.checkbox("Show Apple (AAPL)", value=True, key="chk_apple")
show_nvidia = st.sidebar.checkbox("Show NVIDIA (NVDA)", value=True, key="chk_nvidia")

st.title("Value-at-Risk (VaR) & Expected Shortfall")
st.write(f"Analyse basierend auf einem Konfidenzniveau von {conf_level:.1%}")

# --- LOGIK ---
if not show_apple and not show_nvidia:
    st.warning("Bitte waehlen Sie mindestens eine Aktie in der Sidebar aus.")
else:
    # Daten nur laden, wenn ausgewählt
    ret_a = get_stock_returns(STOCKS["Apple"]) if show_apple else None
    ret_n = get_stock_returns(STOCKS["NVIDIA"]) if show_nvidia else None

    fig = go.Figure()

    # Apple Plot
    if show_apple and ret_a is not None:
        v_a = np.percentile(ret_a, (1 - conf_level) * 100)
        e_a = ret_a[ret_a <= v_a].mean()
        fig.add_trace(go.Histogram(x=ret_a, name="Apple", marker_color='#1f77b4', opacity=0.6))
        fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4", annotation_text=f"VaR AAPL: {v_a:.2%}")

    # NVIDIA Plot
    if show_nvidia and ret_n is not None:
        v_n = np.percentile(ret_n, (1 - conf_level) * 100)
        e_n = ret_n[ret_n <= v_n].mean()
        fig.add_trace(go.Histogram(x=ret_n, name="NVIDIA", marker_color='#ff7f0e', opacity=0.6))
        fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e", annotation_text=f"VaR NVDA: {v_n:.2%}", annotation_position="top left")

    fig.update_layout(barmode='overlay', template="plotly_dark", xaxis_title="Daily Return", yaxis_title="Frequency")
    st.plotly_chart(fig, width='stretch')

    # Metriken in Spalten
    col1, col2 = st.columns(2)
    if show_apple and ret_a is not None:
        col1.metric("VaR Apple", f"{v_a:.2%}")
        col1.metric("Expected Shortfall AAPL", f"{e_a:.2%}")
    if show_nvidia and ret_n is not None:
        col2.metric("VaR NVIDIA", f"{v_n:.2%}")
        col2.metric("Expected Shortfall NVDA", f"{e_n:.2%}")
