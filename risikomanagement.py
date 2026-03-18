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

    # --- LAYOUT MIT TIEFSCHWARZEM TEXT-FOKUS ---
    fig.update_layout(
        barmode='overlay',
        xaxis_title="Daily Return",
        yaxis_title="Frequency",
        
        # Schriftfarbe auf absolutes Schwarz setzen (#000000)
        font=dict(color="#000000", family="Arial"),
        
        # Achsen-Farben und Gitterlinien
        xaxis=dict(
            color="#000000",
            gridcolor="rgba(0,0,0,0.1)",  # Sehr dezente schwarze Linien
            zerolinecolor="#000000"
        ),
        yaxis=dict(
            color="#000000",
            gridcolor="rgba(0,0,0,0.1)",
            zerolinecolor="#000000"
        ),
        
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            font=dict(color="#000000")
        ),
        
        # Transparenter Hintergrund fuer nahtlose Integration in Streamlit
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50)
    )

    # WICHTIG: theme="streamlit" sorgt fuer den automatischen Wechsel bei Dark Mode
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
    - **Value-at-Risk (VaR):** The maximum expected loss at a {conf_level * 100:.1f}% confidence level.
    - **Expected Shortfall (CVaR):** The average loss occurring in the worst {((1-conf_level)*100):.1f}% of cases.
    """)

    st.markdown(f"""
    ### Key Insights:
    * **Tail Risk:** VaR and Expected Shortfall focus on the "left tail" of the distribution.
    * **Comparison:** You can observe that NVIDIA generally shows a wider distribution and a more negative VaR, indicating higher market risk.
    * **Fat Tails:** If Expected Shortfall is significantly lower than VaR, it indicates a high risk of extreme "Black Swan" events.
    """)

    st.caption("Method: Historical simulation based on local CSV data. Data source: Alpha Vantage.")

else:
    st.info("Please select assets in the sidebar to view the risk analysis.")
