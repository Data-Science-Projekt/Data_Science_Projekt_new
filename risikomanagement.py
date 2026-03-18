import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- HILFSFUNKTIONEN ---
try:
    from analysis.utils import render_page_header
except ImportError:
    def render_page_header(title, subtitle):
        st.title(title)
        st.write(subtitle)

# --- CONFIG ---
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}

@st.cache_data(show_spinner=False)
def get_local_stock_returns(symbol):
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path): return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        df = df.astype(float).sort_index()
        return df['4. close'].pct_change().dropna()
    except Exception: return None

# --- UI HEADER ---
render_page_header(
    "Risk Management",
    "What is the maximum expected loss for Apple compared to NVIDIA over a 1-day horizon?"
)

# --- ULTRA KOMPAKTE CONTROLS ---
# Wir nutzen 5 schmale Spalten fuer eine minimale Hoehe
c1, c2, c3, c4, c5 = st.columns([1.5, 1, 1, 1, 2])

with c1:
    # Selectbox ist flacher als ein Slider
    conf_level = st.selectbox("Confidence", [90.0, 95.0, 97.5, 99.0], index=2) / 100

with c2:
    st.write("") # Platzhalter fuer vertikale Ausrichtung
    show_apple = st.checkbox("AAPL", value=True)

with c3:
    st.write("") 
    show_nvidia = st.checkbox("NVDA", value=True)

with c4:
    # Ein kleiner Button zum Zuruecksetzen oder einfach als Platzhalter
    st.write("")
    if st.button("Reset"): st.rerun()

st.divider()

# --- DATA LOADING ---
ret_a = get_local_stock_returns(STOCKS["Apple"]) if show_apple else None
ret_n = get_local_stock_returns(STOCKS["NVIDIA"]) if show_nvidia else None

# --- PLOTTING ---
if (show_apple and ret_a is not None) or (show_nvidia and ret_n is not None):
    fig = go.Figure()

    if show_apple and ret_a is not None:
        v_a = np.percentile(ret_a, (1 - conf_level) * 100)
        fig.add_trace(go.Histogram(x=ret_a, name="Apple", marker_color='#1f77b4', opacity=0.6, nbinsx=50))
        fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4")
        fig.add_annotation(x=v_a, y=0.98, yref="paper", xref="x", text=f"AAPL: {v_a:.2%}",
                           showarrow=False, font=dict(color="#1f77b4", size=11), xanchor="left", xshift=5)

    if show_nvidia and ret_n is not None:
        v_n = np.percentile(ret_n, (1 - conf_level) * 100)
        fig.add_trace(go.Histogram(x=ret_n, name="NVIDIA", marker_color='#ff7f0e', opacity=0.6, nbinsx=50))
        fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e")
        fig.add_annotation(x=v_n, y=0.98, yref="paper", xref="x", text=f"NVDA: {v_n:.2%}",
                           showarrow=False, font=dict(color="#ff7f0e", size=11), xanchor="right", xshift=-5)

    fig.update_layout(
        barmode='overlay', height=400, # Chart noch flacher
        margin=dict(t=30, b=40, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    # Metrics in einer einzigen Zeile
    m_cols = st.columns(4)
    if show_apple and ret_a is not None:
        m_cols[0].metric("VaR AAPL", f"{v_a:.2%}")
        m_cols[1].metric("ES AAPL", f"{(ret_a[ret_a <= v_a].mean()):.2%}")
    if show_nvidia and ret_n is not None:
        m_cols[2].metric("VaR NVDA", f"{v_n:.2%}")
        m_cols[3].metric("ES NVDA", f"{(ret_n[ret_n <= v_n].mean()):.2%}")
else:
    st.info("Select assets.")
