import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- CONFIG ---
# Data sources are now loaded locally from the folder maintained by the bot
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}

@st.cache_data(show_spinner=False)
def get_local_stock_returns(symbol):
    """Reads stock data locally and calculates daily returns."""
    file_path = f"data/stock_{symbol}.csv"
    
    if not os.path.exists(file_path):
        return None
        
    try:
        # Read CSV created by the bot
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        # Sort to ensure correct chronological order
        df = df.astype(float).sort_index()
        # Calculate percentage change (returns)
        return df['4. close'].pct_change().dropna()
    except Exception:
        return None

# --- SIDEBAR ---
st.sidebar.header("Risk Settings")
conf_level = st.sidebar.slider("Confidence level (percent)", 90.0, 99.0, 95.0, 0.5) / 100
st.sidebar.divider()
show_apple = st.sidebar.checkbox("Show Apple (AAPL)", value=True, key="risk_a")
show_nvidia = st.sidebar.checkbox("Show NVIDIA (NVDA)", value=True, key="risk_n")

st.title("Value-at-Risk (VaR) and Expected Shortfall")
st.write("Quantifying potential losses and tail risks for individual assets.")

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
        # Historical simulation of VaR
        v_a = np.percentile(ret_a, (1 - conf_level) * 100)
        # Expected Shortfall (average loss beyond VaR)
        e_a = ret_a[ret_a <= v_a].mean()
        fig.add_trace(go.Histogram(x=ret_a, name="Apple", marker_color='#1f77b4', opacity=0.6))
        fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4", annotation_text="VaR AAPL")

    if show_nvidia and ret_n is not None:
        v_n = np.percentile(ret_n, (1 - conf_level) * 100)
        e_n = ret_n[ret_n <= v_n].mean()
        fig.add_trace(go.Histogram(x=ret_n, name="NVIDIA", marker_color='#ff7f0e', opacity=0.6))
        fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e", annotation_text="VaR NVDA")

    fig.update_layout(
        barmode='overlay',
        template="plotly_dark",
        xaxis_title="Daily Return",
        yaxis_title="Frequency",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Metrics below the chart
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
    - **Value-at-Risk (VaR):** Represents the maximum expected loss over a given time horizon at a specified confidence level ({conf_level * 100:.1f} percent).  
    - **Expected Shortfall (CVaR):** Represents the average loss that occurs once the VaR threshold is exceeded (the average of the worst-case outcomes).
    """)

    st.markdown("""
    ### Key Insights:

    * **Tail Risk Assessment:** While standard deviation (volatility) measures overall uncertainty, **VaR** and **Expected Shortfall** specifically focus on the left tail of the distribution—where the most significant losses occur.

    * **Apple vs. NVIDIA:**  
        - NVIDIA typically exhibits a **lower (more negative) VaR** than Apple, reflecting higher historical volatility and beta.  
        - A larger gap between VaR and Expected Shortfall suggests **fat tails** (leptokurtosis), meaning extreme downside events are more likely than under a normal distribution.

    * **Impact of Confidence Level:**  
        - Increasing the confidence level (e.g., from 95 to 99 percent) shifts the VaR threshold further left, capturing more extreme but rarer events.  
        - Investors with low risk tolerance should focus on **Expected Shortfall**, as it provides a more realistic estimate of losses during market stress.

    * **Limitations:** These metrics are based on historical data (last 100 trading days). They assume that future market behavior resembles the past, which may not hold during unprecedented black swan events.
    """)

    st.caption("Method: Historical simulation based on the last 100 trading days. Data source: Local (via bot).")

else:
    st.info("Please select assets or ensure that local data is available.")
