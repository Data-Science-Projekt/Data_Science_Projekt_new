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
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        df = df.astype(float).sort_index()
        return df['4. close'].pct_change().dropna()
    except Exception:
        return None

# --- UI HEADER ---
render_page_header(
    "Risk Management",
    "What is the maximum expected loss (at a specified confidence level) for Apple compared to NVIDIA over a 1-day horizon?"
)

# --- KOMPAKTE SETTINGS (Eine schmale Zeile) ---
# Wir nutzen 4 Spalten: Eine breitere fuer den Slider, zwei fuer Checkboxen, eine als Puffer
c1, c2, c3, c4 = st.columns([2, 1, 1, 1])

with c1:
    conf_level = st.select_slider(
        "Confidence (%)", 
        options=[90.0, 95.0, 97.5, 99.0], 
        value=97.5
    ) / 100

with c2:
    # label_visibility="collapsed" spart massiv Platz (keine Beschriftung ueber der Box)
    st.write("Apple")
    show_apple = st.checkbox("AAPL", value=True, key="risk_a", label_visibility="collapsed")

with c3:
    st.write("NVIDIA")
    show_nvidia = st.checkbox("NVDA", value=True, key="risk_n", label_visibility="collapsed")

st.divider()

# --- DATA LOADING ---
ret_a = get_local_stock_returns(STOCKS["Apple"]) if show_apple else None
ret_n = get_local_stock_returns(STOCKS["NVIDIA"]) if show_nvidia else None

# --- PLOTTING ---
if (show_apple and ret_a is not None) or (show_nvidia and ret_n is not None):
    fig = go.Figure()

    if show_apple and ret_a is not None:
        v_a = np.percentile(ret_a, (1 - conf_level) * 100)
        fig.add_trace(go.Histogram(
            x=ret_a, name="Apple", marker_color='#1f77b4', opacity=0.6, nbinsx=50,
            hovertemplate="Return: %{x:.2%}<br>Count: %{y}<extra></extra>"
        ))
        fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4")
        fig.add_annotation(
            x=v_a, y=0.95, yref="paper", xref="x",
            text=f"VaR AAPL: {v_a:.2%}", showarrow=False,
            font=dict(color="#1f77b4", size=12), align="left", xanchor="left", xshift=5
        )

    if show_nvidia and ret_n is not None:
        v_n = np.percentile(ret_n, (1 - conf_level) * 100)
        fig.add_trace(go.Histogram(
            x=ret_n, name="NVIDIA", marker_color='#ff7f0e', opacity=0.6, nbinsx=50,
            hovertemplate="Return: %{x:.2%}<br>Count: %{y}<extra></extra>"
        ))
        fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e")
        fig.add_annotation(
            x=v_n, y=0.95, yref="paper", xref="x",
            text=f"VaR NVDA: {v_n:.2%}", showarrow=False,
            font=dict(color="#ff7f0e", size=12), align="right", xanchor="right", xshift=-5
        )

    fig.update_layout(
        barmode='overlay', height=450, # Hoehe des Charts leicht reduziert
        xaxis_title="Daily Return", yaxis_title="Frequency",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50, b=50), hovermode="closest"
    )

    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    # Metrics kompakt nebeneinander
    m1, m2, m3, m4 = st.columns(4)
    if show_apple and ret_a is not None:
        m1.metric("VaR Apple", f"{v_a:.2%}")
        e_a = ret_a[ret_a <= v_a].mean()
        m2.metric("ES Apple", f"{e_a:.2%}")
    if show_nvidia and ret_n is not None:
        m3.metric("VaR NVIDIA", f"{v_n:.2%}")
        e_n = ret_n[ret_n <= v_n].mean()
        m4.metric("ES NVIDIA", f"{e_n:.2%}")

else:
    st.info("Please select assets above.")
