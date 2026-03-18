import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- HILFSFUNKTIONEN (Sicherheits-Check) ---
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
    """Liest lokale Aktiendaten und berechnet die taeglichen Renditen."""
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        df = df.astype(float).sort_index()
        # Berechnung der prozentualen Veraenderung (Renditen)
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

# --- NEUES SPALTEN-LAYOUT: VERTICAL SIDE-BY-SIDE ---
# Wir nutzen eine sehr schmale Spalte fuer den Slider (Breite: 1) und eine breite fuer den Chart (Breite: 12)
c_controls, c_plot = st.columns([1, 12])

# Spalte 1: Der vertikale Schieberegler (und Checkboxen)
with c_controls:
    # Wir fuegen vertikalen Leerraum hinzu, damit die Steuerungselemente 
    # nicht ganz oben an der blauen Box kleben.
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    
    st.markdown("### ⚙️ Settings")
    
    # Vertikaler Schieberegler
    # orientation="vertical" macht den Slider flacher, aber er nimmt immer noch Platz weg.
    conf_level = st.slider(
        "Conf. (%)", 
        min_value=90.0, max_value=99.0, value=97.5, step=0.5,
        help="The probability that the actual loss will not exceed the VaR.",
        # orientation="vertical" # Das wird in Streamlit 1.34+ fuer Slider oft ignoriert, aber es hilft Plotly.
    ) / 100
    
    st.write("---")
    
    # Checkboxen darunter, kompakt gehalten
    show_apple = st.checkbox("AAPL", value=True, key="risk_a")
    show_nvidia = st.checkbox("NVDA", value=True, key="risk_n")

# Spalte 2: Das Diagramm
with c_plot:
    if (show_apple and ret_a is not None) or (show_nvidia and ret_n is not None):
        fig = go.Figure()

        if show_apple and ret_a is not None:
            v_a = np.percentile(ret_a, (1 - conf_level) * 100)
            e_a = ret_a[ret_a <= v_a].mean()
            fig.add_trace(go.Histogram(
                x=ret_a, name="Apple", marker_color='#1f77b4', opacity=0.6, nbinsx=50,
                hovertemplate="Avg Return: %{x:.2%}<br>Frequency: %{y:.0f}<extra></extra>"
            ))
            fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4")
            fig.add_annotation(
                x=v_a, y=0.95, yref="paper", xref="x",
                text=f"VaR AAPL: {v_a:.2%}",
                showarrow=False, font=dict(color="#1f77b4", size=12),
                align="left", xanchor="left", xshift=5
            )

        if show_nvidia and ret_n is not None:
            v_n = np.percentile(ret_n, (1 - conf_level) * 100)
            e_n = ret_n[ret_n <= v_n].mean()
            fig.add_trace(go.Histogram(
                x=ret_n, name="NVIDIA", marker_color='#ff7f0e', opacity=0.6, nbinsx=50,
                hovertemplate="Avg Return: %{x:.2%}<br>Frequency: %{y:.0f}<extra></extra>"
            ))
            fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e")
            fig.add_annotation(
                x=v_n, y=0.95, yref="paper", xref="x",
                text=f"VaR NVDA: {v_n:.2%}",
                showarrow=False, font=dict(color="#ff7f0e", size=12),
                align="right", xanchor="right", xshift=-5
            )

        fig.update_layout(
            barmode='overlay',
            xaxis_title="Daily Return",
            yaxis_title="Frequency",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=50, b=50, l=0), # Left Margin auf 0 fuer nahtlosen Anschluss
            hovermode="closest"
        )

        st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    else:
        st.info("Please select assets in the control panel to the left.")

# --- METRICS UNTER DEM CHART ---
st.divider()
c1, c2 = st.columns(2)
if show_apple and ret_a is not None:
    c1.metric("Value-at-Risk Apple", f"{v_a:.2%}")
    c1.metric("Expected Shortfall Apple", f"{e_a:.2%}")
if show_nvidia and ret_n is not None:
    c2.metric("Value-at-Risk NVIDIA", f"{v_n:.2%}")
    c2.metric("Expected Shortfall NVIDIA", f"{e_n:.2%}")

# --- INTERPRETATION ---
st.markdown("---")
st.subheader("Analysis and Interpretation")
st.info(f"Historical simulation at a {conf_level * 100:.1f}% confidence level.")
st.caption("Data source: Alpha Vantage (local).")
