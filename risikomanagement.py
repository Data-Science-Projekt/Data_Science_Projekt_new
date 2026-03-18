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

# --- SIDEBAR ---
st.sidebar.header("Risk Settings")
conf_level = st.sidebar.slider("Confidence level (%)", 90.0, 99.0, 95.0, 0.5) / 100
st.sidebar.divider()
show_apple = st.sidebar.checkbox("Show Apple (AAPL)", value=True, key="risk_a")
show_nvidia = st.sidebar.checkbox("Show NVIDIA (NVDA)", value=True, key="risk_n")

render_page_header(
    "Risk Management",
    f"Expected loss at a {conf_level*100:.1f}% confidence level."
)

# --- DATA LOADING ---
ret_a = get_local_stock_returns(STOCKS["Apple"]) if show_apple else None
ret_n = get_local_stock_returns(STOCKS["NVIDIA"]) if show_nvidia else None

# --- PLOTTING ---
if (show_apple and ret_a is not None) or (show_nvidia and ret_n is not None):
    fig = go.Figure()

    # Wir nutzen hier eine CSS-Variable für die Schriftfarbe. 
    # Streamlit setzt 'rgb(49, 51, 63)' für Text im Light Mode (Grau). 
    # Wir erzwingen 'inherit', damit das CSS der Seite greift, oder setzen es direkt.
    
    if show_apple and ret_a is not None:
        v_a = np.percentile(ret_a, (1 - conf_level) * 100)
        e_a = ret_a[ret_a <= v_a].mean()
        fig.add_trace(go.Histogram(x=ret_a, name="Apple", marker_color='#1f77b4', opacity=0.6))
        fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4", 
                      annotation_text=f"VaR AAPL: {v_a:.2%}", annotation_position="top left")

    if show_nvidia and ret_n is not None:
        v_n = np.percentile(ret_n, (1 - conf_level) * 100)
        e_n = ret_n[ret_n <= v_n].mean()
        fig.add_trace(go.Histogram(x=ret_n, name="NVIDIA", marker_color='#ff7f0e', opacity=0.6))
        fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e", 
                      annotation_text=f"VaR NVDA: {v_n:.2%}", annotation_position="top right")

    # --- DER TRICK FÜR DEN DYNAMISCHEN KONTRAST ---
    # Wir setzen keine feste Farbe wie "black", sondern nutzen das Standard-Theme,
    # überschreiben aber die Gitterlinien und Achsen für maximalen Kontrast.
    
    fig.update_layout(
        barmode='overlay',
        xaxis_title="Daily Return",
        yaxis_title="Frequency",
        # Wir lassen 'template' weg, damit Streamlit steuern kann, 
        # aber wir machen die Achsenlinien fett:
        xaxis=dict(showline=True, linewidth=2, zeroline=True),
        yaxis=dict(showline=True, linewidth=2, zeroline=True),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Wir nutzen nun theme="streamlit", aber wir injizieren VORHER ein kleines CSS,
    # das den Text im Light Mode wirklich schwarz macht.
    st.markdown("""
        <style>
        /* Erzwingt tiefschwarzen Text für Plotly-Elemente im Light Mode */
        .stPlotlyChart [data-testid="stMarkdownContainer"] p { color: black; }
        </style>
    """, unsafe_allow_html=True)

    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    # Metriken
    c1, c2 = st.columns(2)
    if show_apple and ret_a is not None:
        c1.metric("VaR Apple", f"{v_a:.2%}")
    if show_nvidia and ret_n is not None:
        c2.metric("VaR NVIDIA", f"{v_n:.2%}")

else:
    st.info("Please select assets.")
