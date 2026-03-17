import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import time

# --- CONFIGURATION ---
AV_API_KEY = st.secrets.get("AV_API_KEY", "")

TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
ALL_STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}


# --- FUNCTION: LOAD DATA (ALPHA VANTAGE) ---
@st.cache_data(show_spinner="Loading market data...")
def get_stock_data_compact(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        if "Time Series (Daily)" in data:
            df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
            df.index = pd.to_datetime(df.index)
            df = df.astype(float).sort_index()
            # Calculation of the trading range
            df["abs_range"] = df["2. high"] - df["3. low"]
            df["rel_range_pct"] = (df["abs_range"] / df["4. close"]) * 100
            return df
        return None
    except:
        return None


# --- UI ---
st.title("Daily Trading Ranges")
st.write("Comparison of volatility between Tech and Financial stocks.")

selected_tech = st.sidebar.multiselect("Tech Stocks", list(TECH_STOCKS.keys()), default=["Apple"])
selected_fin = st.sidebar.multiselect("Financial Stocks", list(FINANCIAL_STOCKS.keys()), default=["J.P. Morgan"])

all_selected = {**{k: TECH_STOCKS[k] for k in selected_tech}, **{k: FINANCIAL_STOCKS[k] for k in selected_fin}}

if not all_selected:
    st.warning("Please select at least one stock.")
    st.stop()

# Load Data
stock_data = {}
for name, symbol in all_selected.items():
    df = get_stock_data_compact(symbol)
    if df is not None:
        stock_data[name] = df

if stock_data:
    # Boxplot of Volatility
    fig_box = go.Figure()
    for name, df in stock_data.items():
        fig_box.add_trace(go.Box(y=df["rel_range_pct"], name=name))

    fig_box.update_layout(
        title="Relative Trading Range in %",
        template="plotly_dark",
        yaxis_title="Range (%)"
    )
    st.plotly_chart(fig_box, use_container_width=True)

    # Statistics Table
    stats = []
    for name, df in stock_data.items():
        stats.append({
            "Stock": name,
            "Average (%)": round(df["rel_range_pct"].mean(), 2),
            "Max (%)": round(df["rel_range_pct"].max(), 2)
        })
    st.table(pd.DataFrame(stats))

    # --- INTERPRETATION & EXPLANATION (Extracted from range_analysis.py) ---
    st.markdown("---")
    st.subheader("Analysis & Interpretation")

    st.info("""
    **Research Question:** Investigation of the differences in daily trading ranges (intraday volatility) 
    between Technology stocks and Financial stocks.
    """)

    st.markdown("""
    ### Key Findings:

    * **Sector Differences:** Tech stocks (e.g., Apple, Microsoft, NVIDIA) tend to exhibit **higher volatility** in daily trading ranges compared to traditional Financial stocks (e.g., J.P. Morgan, Bank of America). 
        This reflects higher growth potential but also the higher risk profile of the tech sector.

    * **Asymmetric Impact:** Our analysis indicates that negative news typically produces larger volatility 
        spikes than positive news of a similar magnitude. This is consistent with the well-documented 
        **'negativity bias'** and loss aversion in financial markets.

    * **News Magnitude Matters:** The *strength* of the news sentiment (how extreme the news is) is often 
        more predictive of a volatility spike than the mere *direction* (positive or negative) of the news.

    * **Market Efficiency:** Many news events are partially "priced in" before official publication 
        (e.g., analyst expectations before earnings). Therefore, the observed volatility often results 
        from the gap between actual results and market expectations.

    * **Confounding Factors:** Daily ranges are not only driven by company-specific news but also by 
        macroeconomic events (Fed decisions, inflation data), sector rotation, and geopolitical tensions.
    """)

    st.caption(
        "Data Source: Alpha Vantage (TIME_SERIES_DAILY). Relative range is calculated as: ((High - Low) / Close) * 100.")
