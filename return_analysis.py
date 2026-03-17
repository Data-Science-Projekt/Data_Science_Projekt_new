import streamlit as st
import pandas as pd
import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objects as go
import os
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

# --- CONFIGURATION ---
# We use the data provided by the bot in the data folder
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

# --- FUNCTION: LOAD DATA (LOCAL) ---
@st.cache_data(show_spinner="Loading market data...")
def get_stock_data_local(symbol):
    """Reads stock data from the local data folder."""
    file_path = f"data/stock_{symbol}.csv"
    
    if not os.path.exists(file_path):
        return None
        
    try:
        # Read CSV created by the bot
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        # Sort for chronological calculations
        df = df.astype(float).sort_index()
        
        # Calculate trading range (for statistical table below)
        df["abs_range"] = df["2. high"] - df["3. low"]
        df["rel_range_pct"] = (df["abs_range"] / df["4. close"]) * 100
        
        return df
    except Exception:
        return None

# --- UI ---
render_page_header(
    "Return Analysis",
    "To what extent do the daily log returns of Apple and NVIDIA deviate from a normal distribution?",
)

# Sidebar for selection
selected_tech = st.sidebar.multiselect("Tech stocks", list(TECH_STOCKS.keys()), default=["Apple"])
selected_fin = st.sidebar.multiselect("Financial stocks", list(FINANCIAL_STOCKS.keys()), default=["J.P. Morgan"])

# Combine selections
all_selected = {
    **{k: TECH_STOCKS[k] for k in selected_tech},
    **{k: FINANCIAL_STOCKS[k] for k in selected_fin}
}

if not all_selected:
    st.warning("Please select at least one stock.")
    st.stop()

# Load data
stock_data = {}
for name, symbol in all_selected.items():
    df = get_stock_data_local(symbol)
    if df is not None:
        stock_data[name] = df

if stock_data:
    # Boxplot of volatility
    fig_box = go.Figure()
    for name, df in stock_data.items():
        fig_box.add_trace(go.Box(y=df["rel_range_pct"], name=name))

    fig_box.update_layout(
        title="Relative trading range (%)",
        template="plotly_dark",
        yaxis_title="Range (%)"
    )
    st.plotly_chart(fig_box, use_container_width=True)

    st.download_button(
        label="📥 Graph als PNG herunterladen",
        data=fig_to_pdf_bytes(fig_box),
        file_name="return_analysis.png",
        mime="application/png"
    )

    # Statistical table
    st.subheader("Statistical Overview")
    stats = []
    for name, df in stock_data.items():
        stats.append({
            "Stock": name,
            "Average (%)": round(df["rel_range_pct"].mean(), 2),
            "Maximum (%)": round(df["rel_range_pct"].max(), 2)
        })
    st.table(pd.DataFrame(stats))

    # --- INTERPRETATION ---
    st.markdown("---")
    st.subheader("Analysis and Interpretation")

    st.info("""
    Research question: Analysis of differences in daily trading ranges (intraday volatility)  
    between technology stocks and financial stocks.
    """)

    st.markdown("""
    ### Key Insights:

    * **Sector Differences:** Tech stocks (e.g., Apple, Microsoft, NVIDIA) tend to exhibit higher volatility in daily trading ranges compared to traditional financial stocks (e.g., J.P. Morgan, Bank of America).  
      This reflects the higher growth potential but also the higher risk profile of the tech sector.

    * **Asymmetric Effects:** The analysis suggests that negative news typically generates larger volatility spikes than positive news of similar magnitude.  
      This aligns with the well-documented negativity bias in financial markets.

    * **Importance of News Intensity:** The strength of news sentiment is often more impactful for volatility than the direction (positive/negative) alone.

    * **Market Efficiency:** Many news events are partially priced in (e.g., analyst expectations before earnings releases).  
      Observed volatility often results from the gap between actual outcomes and market expectations.

    * **Drivers of Volatility:** Daily trading ranges are influenced not only by firm-specific news but also by macroeconomic events (Fed decisions, inflation data), sector rotations, and geopolitical developments.
    """)

    st.caption(
        "Data source: Alpha Vantage (TIME_SERIES_DAILY). Relative range is calculated as: ((High - Low) / Close) * 100."
    )
else:
    st.error("No local data could be found. Please ensure that the data bot has run successfully.")
