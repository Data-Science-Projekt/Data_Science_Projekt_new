import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

# --- CONFIG ---
AV_API_KEY = st.secrets.get("AV_API_KEY", "")
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}

@st.cache_data(show_spinner="Lade Risk-Daten...")
def get_stock_returns(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url).json()
        if "Time Series (Daily)" in r:
            df = pd.DataFrame.from_dict(r['Time Series (Daily)'], orient='index').astype(float).sort_index()
            return df['4. close'].pct_change().dropna()
        elif "Note" in r:
            st.warning(f"API Limit erreicht für {symbol}. Bitte kurz warten.")
            return None
    except:
        return None
    return None

# --- SIDEBAR ---
st.sidebar.header("Risk Settings")
conf_level = st.sidebar.slider("Confidence Level (%)", 90.0, 99.0, 95.0, 0.5) / 100
st.sidebar.divider()

st.sidebar.write("**Asset Selection:**")
# Variablen direkt zuweisen
show_apple = st.sidebar.checkbox("Show Apple (AAPL)", value=True)
show_nvidia = st.sidebar.checkbox("Show NVIDIA (NVDA)", value=True)

st.title("Value-at-Risk (VaR) & Expected Shortfall")
st.write(f"Analyse bei {conf_level:.1%} Confidence Interval")

# Logik-Check: Erst wenn die Variablen feststehen, Daten laden
if show_apple or show_nvidia:
    ret_a = get_stock_returns(STOCKS["Apple"]) if show_apple else None
    ret_n = get_stock_returns(STOCKS["NVIDIA"]) if show_nvidia else None

    if ret_a is not None or ret_n is not None:
        fig = go.Figure()
        
        if ret_a is not None:
            v_a = np.percentile(ret_a, (1 - conf_level) * 100)
            fig.add_trace(go.Histogram(x=ret_a, name="Apple", marker_color='#1f77b4', opacity=0.6))
            fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4")

        if ret_n is not None:
            v_n = np.percentile(ret_n, (1 - conf_level) * 100)
            fig.add_trace(go.Histogram(x=ret_n, name="NVIDIA", marker_color='#ff7f0e', opacity=0.6))
            fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e")

        fig.update_layout(barmode='overlay', template="plotly_dark")
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Warte auf API-Daten... Falls dies länger dauert, wurde das Rate-Limit erreicht.")
else:
    st.warning("Bitte wählen Sie mindestens eine Aktie in der Sidebar aus.")
