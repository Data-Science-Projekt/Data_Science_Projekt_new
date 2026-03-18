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
    """Liest lokale Aktiendaten und berechnet die täglichen Renditen."""
    file_path = f"data/stock_{symbol}.csv"
    
    if not os.path.exists(file_path):
        return None
        
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        df = df.astype(float).sort_index()
        # Berechnung der prozentualen Veränderung (Renditen)
        return df['4. close'].pct_change().dropna()
    except Exception:
        return None

# --- SIDEBAR (Die alte, stabile Version) ---
st.sidebar.header("Risk Settings")

conf_level = st.sidebar.slider(
    "Confidence level (%)", 
    90.0, 99.0, 97.5, 0.5,
    help="The probability that the actual loss will not exceed the VaR."
) / 100

st.sidebar.divider()

show_apple = st.sidebar.checkbox("Show Apple (AAPL)", value=True, key="risk_a")
show_nvidia = st.sidebar.checkbox("Show NVIDIA (NVDA)", value=True, key="risk_n")

# --- UI HEADER ---
render_page_header(
    "Risk Management",
    f"What is the maximum expected loss (at a {conf_level*100:.1f}% confidence level) for Apple compared to NVIDIA over a 1-day horizon?"
)

# --- DATA LOADING ---
ret_a = None
ret_n = None

if show_apple:
    ret_a = get_local_stock_returns(STOCKS["Apple"])
if show_nvidia:
    ret_n = get_local_stock_returns(STOCKS["NVIDIA"])

# --- PLOTTING ---
if (show_apple and ret_a is not None) or (show_nvidia and ret_n is not None):
    fig = go.Figure()

    if show_apple and ret_a is not None:
        # Historische Simulation des VaR
        v_a = np.percentile(ret_a, (1 - conf_level) * 100)
        # Expected Shortfall
        e_a = ret_a[ret_a <= v_a].mean()
        
        fig.add_trace(go.Histogram(
            x=ret_a, 
            name="Apple", 
            marker_color='#1f77b4', 
            opacity=0.6, 
            nbinsx=50,
            hovertemplate="Avg Return: %{x:.2%}<br>Frequency: %{y:.0f}<extra></extra>"
        ))
        
        # Vertikale Linie für Apple
        fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4")
        
        # TEXT-ANNOTATION APPLE (Fixierte Höhe 95%)
        fig.add_annotation(
            x=v_a,               # Anker an der X-Position des VaR
            y=0.95,              # 95% der vertikalen Charthöhe
            yref="paper",        # Referenz auf das Chart-Fenster (0 bis 1)
            xref="x",            # Referenz auf die Daten-Achse
            text=f"VaR AAPL: {v_a:.2%}",
            showarrow=False,
            font=dict(color="#1f77b4", size=12),
            align="left",
            xanchor="left",      # Text fließt nach RECHTS weg
            xshift=5             # Kleiner horizontaler Abstand zur Linie
        )

    if show_nvidia and ret_n is not None:
        v_n = np.percentile(ret_n, (1 - conf_level) * 100)
        e_n = ret_n[ret_n <= v_n].mean()
        
        fig.add_trace(go.Histogram(
            x=ret_n, 
            name="NVIDIA", 
            marker_color='#ff7f0e', 
            opacity=0.6, 
            nbinsx=50,
            hovertemplate="Avg Return: %{x:.2%}<br>Frequency: %{y:.0f}<extra></extra>"
        ))
        
        # Vertikale Linie für NVIDIA
        fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e")
        
        # TEXT-ANNOTATION NVIDIA (Fixierte Höhe 95%)
        fig.add_annotation(
            x=v_n,               # Anker an der X-Position des VaR
            y=0.95,              # EBENFALLS 95% der vertikalen Charthöhe
            yref="paper",        # Referenz auf das Chart-Fenster (0 bis 1)
            xref="x",            # Referenz auf die Daten-Achse
            text=f"VaR NVDA: {v_n:.2%}",
            showarrow=False,
            font=dict(color="#ff7f0e", size=12),
            align="right",
            xanchor="right",     # Text fließt nach LINKS weg
            xshift=-5            # Kleiner horizontaler Abstand zur Linie
        )

    # Layout-Anpassungen (Automatische Farben durch Streamlit-Theme)
    fig.update_layout(
        barmode='overlay',
        xaxis_title="Daily Return",
        yaxis_title="Frequency",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=80, b=50), 
        hovermode="closest"
    )

    # Chart ausgeben
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    # Metrics unter dem Chart
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    if show_apple and ret_a is not None:
        c1.metric("VaR Apple", f"{v_a:.2%}")
        c2.metric("ES Apple", f"{e_a:.2%}")
    if show_nvidia and ret_n is not None:
        c3.metric("VaR NVIDIA", f"{v_n:.2%}")
        c4.metric("ES NVIDIA", f"{e_n:.2%}")

    # --- INTERPRETATION ---
    st.markdown("---")
    st.subheader("Analysis and Interpretation")
    st.info(f"Historical simulation at a {conf_level * 100:.1f}% confidence level.")
    
    st.markdown("""
    ### Key Insights:
    * **Risk Comparison:** NVIDIA typically shows a wider 'tail', meaning the potential for larger single-day losses is higher than with Apple.
    * **Fat Tails:** Observe how the VaR lines shift when you change the confidence level in the sidebar.
    """)

else:
    st.info("Please select at least one asset in the sidebar.")
