import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# Falls diese Hilfsfunktionen in deinem Projekt existieren, bleiben sie drin.
# Wenn sie Fehler verursachen, kannst du sie durch st.title/st.write ersetzen.
try:
    from analysis.utils import render_page_header
    from utils.export import fig_to_pdf_bytes
except ImportError:
    def render_page_header(title, subtitle):
        st.title(title)
        st.write(subtitle)
    def fig_to_pdf_bytes(fig):
        return b""

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

# --- SIDEBAR ---
st.sidebar.header("Risk Settings")
conf_level = st.sidebar.slider("Confidence level (%)", 90.0, 99.0, 95.0, 0.5) / 100
st.sidebar.divider()
show_apple = st.sidebar.checkbox("Show Apple (AAPL)", value=True, key="risk_a")
show_nvidia = st.sidebar.checkbox("Show NVIDIA (NVDA)", value=True, key="risk_n")

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
        # Expected Shortfall (Durchschnittlicher Verlust jenseits des VaR)
        e_a = ret_a[ret_a <= v_a].mean()
        fig.add_trace(go.Histogram(
            x=ret_a, 
            name="Apple", 
            marker_color='#1f77b4', 
            opacity=0.6,
            nbinsx=50
        ))
        fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4", 
                      annotation_text=f"VaR AAPL: {v_a:.2%}",
                      annotation_position="top left")

    if show_nvidia and ret_n is not None:
        v_n = np.percentile(ret_n, (1 - conf_level) * 100)
        e_n = ret_n[ret_n <= v_n].mean()
        fig.add_trace(go.Histogram(
            x=ret_n, 
            name="NVIDIA", 
            marker_color='#ff7f0e', 
            opacity=0.6,
            nbinsx=50
        ))
        fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e", 
                      annotation_text=f"VaR NVDA: {v_n:.2%}",
                      annotation_position="top right")

    # Layout-Anpassung fuer dynamische Farben (Light/Dark Mode)
    fig.update_layout(
        barmode='overlay',
        xaxis_title="Daily Return",
        yaxis_title="Frequency",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        # Hintergruende transparent machen, damit das Streamlit-Theme wirkt
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50)
    )

    # WICHTIG: theme="streamlit" sorgt fuer den automatischen Farbwechsel der Achsen
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    # Metrics unter dem Chart
    c1, c2 = st.columns(2)
    if show_apple and ret_a is not None:
        c1.subheader("Apple (AAPL)")
        c1.metric("Value-at-Risk", f"{v_a:.2%}")
        c1.metric("Expected Shortfall", f"{e_a:.2%}")
    if show_nvidia and ret_n is not None:
        c2.subheader("NVIDIA (NVDA)")
        c2.metric("Value-at-Risk", f"{v_n:.2%}")
        c2.metric("Expected Shortfall", f"{e_n:.2%}")

    # --- INTERPRETATION ---
    st.markdown("---")
    st.subheader("Analysis and Interpretation")

    st.info(f"""
    **Definition of risk metrics:**
    - **Value-at-Risk (VaR):** Represents the maximum expected loss over a 1-day horizon at a {conf_level * 100:.1f}% confidence level.
    - **Expected Shortfall (CVaR):** The average loss that occurs once the VaR threshold is breached (tail risk).
    """)

    st.markdown(f"""
    ### Key Insights:

    * **Tail Risk Assessment:** Unlike standard deviation, **VaR** and **Expected Shortfall** focus specifically on extreme downside events.
    * **Comparison:** NVIDIA typically shows a more negative VaR, indicating higher risk due to its higher beta and volatility compared to Apple.
    * **Current Selection:** At a {conf_level*100:.1f}% confidence level, you can see how the distribution of returns for both stocks behaves.
    """)

    st.caption("Method: Historical simulation based on local CSV data. Data source: Alpha Vantage.")

else:
    st.info("Please select assets in the sidebar to view the risk analysis.")
