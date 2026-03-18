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

# --- CSS FÜR KLEINERE SCHRIFT IN DER KONTROLLSPALTE ---
st.markdown("""
    <style>
    /* Macht die Überschrift in der schmalen Spalte kleiner */
    .small-font h3 {
        font-size: 16px !important;
        margin-bottom: 0px;
    }
    /* Verkleinert die Beschriftung des Sliders und der Checkboxen */
    .small-font label {
        font-size: 12px !important;
    }
    /* Verringert den Abstand zwischen den Elementen */
    .stCheckbox {
        margin-top: -15px;
    }
    </style>
    """, unsafe_allow_html=True)

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

# --- DATA LOADING ---
ret_a = get_local_stock_returns(STOCKS["Apple"])
ret_n = get_local_stock_returns(STOCKS["NVIDIA"])

# --- LAYOUT: CONTROLS LINKS NEBEN DEM CHART ---
# Wir nutzen ein Container-Div mit der Klasse 'small-font' für die linke Spalte
c_controls, c_plot = st.columns([1.2, 10])

with c_controls:
    # Wir hüllen die Controls in ein div für das CSS
    st.markdown('<div class="small-font">', unsafe_allow_html=True)
    
    # Vertikaler Abstand, damit es auf Höhe des Charts beginnt
    for _ in range(5): st.write("")
    
    st.markdown("### Settings")
    
    conf_level = st.slider(
        "Conf. (%)", 
        90.0, 99.0, 97.5, 0.5
    ) / 100
    
    st.write("---")
    
    show_apple = st.checkbox("AAPL", value=True)
    show_nvidia = st.checkbox("NVDA", value=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Spalte 2: Das Diagramm
with c_plot:
    if (show_apple and ret_a is not None) or (show_nvidia and ret_n is not None):
        fig = go.Figure()

        if show_apple and ret_a is not None:
            v_a = np.percentile(ret_a, (1 - conf_level) * 100)
            fig.add_trace(go.Histogram(
                x=ret_a, name="Apple", marker_color='#1f77b4', opacity=0.6, nbinsx=50,
                hovertemplate="Avg Return: %{x:.2%}<br>Frequency: %{y:.0f}<extra></extra>"
            ))
            fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4")
            fig.add_annotation(
                x=v_a, y=0.95, yref="paper", xref="x", text=f"AAPL: {v_a:.2%}",
                showarrow=False, font=dict(color="#1f77b4", size=11), xanchor="left", xshift=5
            )

        if show_nvidia and ret_n is not None:
            v_n = np.percentile(ret_n, (1 - conf_level) * 100)
            fig.add_trace(go.Histogram(
                x=ret_n, name="NVIDIA", marker_color='#ff7f0e', opacity=0.6, nbinsx=50,
                hovertemplate="Avg Return: %{x:.2%}<br>Frequency: %{y:.0f}<extra></extra>"
            ))
            fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e")
            fig.add_annotation(
                x=v_n, y=0.95, yref="paper", xref="x", text=f"NVDA: {v_n:.2%}",
                showarrow=False, font=dict(color="#ff7f0e", size=11), xanchor="right", xshift=-5
            )

        fig.update_layout(
            barmode='overlay', height=450,
            xaxis_title="Daily Return", yaxis_title="Frequency",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=50, b=50, l=0), hovermode="closest"
        )
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")

# --- METRICS UNTER DEM CHART ---
st.divider()
m1, m2, m3, m4 = st.columns(4)
if show_apple and ret_a is not None:
    m1.metric("VaR AAPL", f"{v_a:.2%}")
    m2.metric("ES AAPL", f"{(ret_a[ret_a <= v_a].mean()):.2%}")
if show_nvidia and ret_n is not None:
    m3.metric("VaR NVDA", f"{v_n:.2%}")
    m4.metric("ES NVDA", f"{(ret_n[ret_n <= v_n].mean()):.2%}")
