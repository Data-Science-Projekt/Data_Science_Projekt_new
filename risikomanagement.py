import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

# --- CONFIG ---
AV_API_KEY = st.secrets.get("AV_API_KEY", "")
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}



@st.cache_data
def get_stock_returns(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url).json()
        if "Time Series (Daily)" in r:
            df = pd.DataFrame.from_dict(r['Time Series (Daily)'], orient='index').astype(float).sort_index()
            return df['4. close'].pct_change().dropna()
    except:
        return None
    return None


# --- SIDEBAR (Stil wie gewünscht) ---
with st.sidebar:
    st.header("Risk Settings")

    # Der Slider für das Confidence Level
    conf_level = st.slider("Confidence Level (%)", 90.0, 99.0, 95.0, 0.5) / 100

    st.markdown("---")

    # Auswahlmenü im gewünschten Stil
    st.write("**Asset Selection:**")
    show_apple = st.checkbox("Show Apple (AAPL)", value=True)
    show_nvidia = st.checkbox("Show NVIDIA (NVDA)", value=True)

    selected_assets = []
    if show_apple: selected_assets.append("Apple")
    if show_nvidia: selected_assets.append("NVIDIA")

st.title("Value-at-Risk (VaR) & Expected Shortfall")
st.markdown(f"**Current Analysis:** {conf_level:.1%} Confidence Interval")

# Daten laden
ret_a = get_stock_returns(STOCKS["Apple"]) if show_apple else None
ret_n = get_stock_returns(STOCKS["NVIDIA"]) if show_nvidia else None

if ret_a is not None or ret_n is not None:
    fig = go.Figure()

    # --- APPLE DATA ---
    if ret_a is not None:
        v_a = np.percentile(ret_a, (1 - conf_level) * 100)
        e_a = ret_a[ret_a <= v_a].mean()

        fig.add_trace(go.Histogram(
            x=ret_a, name="Apple", marker_color='#1f77b4', opacity=0.6,
            xbins=dict(size=0.005),
            hovertemplate="Return: %{x:.2%}<br>Days: %{y}<extra></extra>"
        ))
        fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4", annotation_text=f"VaR: {v_a:.2%}")

    # --- NVIDIA DATA ---
    if ret_n is not None:
        v_n = np.percentile(ret_n, (1 - conf_level) * 100)
        e_n = ret_n[ret_n <= v_n].mean()

        fig.add_trace(go.Histogram(
            x=ret_n, name="NVIDIA", marker_color='#ff7f0e', opacity=0.6,
            xbins=dict(size=0.005),
            hovertemplate="Return: %{x:.2%}<br>Days: %{y}<extra></extra>"
        ))
        fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e", annotation_text=f"VaR: {v_n:.2%}",
                      annotation_position="top left")

    # Layout
    fig.update_layout(
        barmode='overlay',
        template="plotly_white",
        xaxis_title="Daily Return (0.01 = 1%)",
        yaxis_title="Frequency (Days)",
        hovermode="x",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_xaxes(tickformat=".1%")
    st.plotly_chart(fig, use_container_width=True)

    # --- METRICS ---
    c1, c2 = st.columns(2)

    if ret_a is not None:
        with c1:
            st.subheader("Apple Risk Metrics")
            st.metric("Value-at-Risk", f"{v_a:.2%}")
            st.metric("Expected Shortfall", f"{e_a:.2%}")

    if ret_n is not None:
        with c2:
            st.subheader("NVIDIA Risk Metrics")
            st.metric("Value-at-Risk", f"{v_n:.2%}")
            st.metric("Expected Shortfall", f"{e_n:.2%}")

    # --- INFO BOX ---
    st.info(f"""
    **Interpretation:** A VaR of e.g. -3.0% means that with {conf_level:.1%} certainty, the daily loss will not exceed 3.0%. 
    The CVaR (Expected Shortfall) shows the average loss in those cases where the VaR is actually breached.
    """)

else:
    st.warning("Please select at least one asset in the sidebar to start the analysis.")
