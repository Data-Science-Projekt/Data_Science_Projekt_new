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
@st.cache_data(show_spinner="Lade Marktdaten...")
def get_stock_data_compact(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        if "Time Series (Daily)" in data:
            df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
            df.index = pd.to_datetime(df.index)
            df = df.astype(float).sort_index()
            # Berechnung der Handelsspanne
            df["abs_range"] = df["2. high"] - df["3. low"]
            df["rel_range_pct"] = (df["abs_range"] / df["4. close"]) * 100
            return df
        return None
    except:
        return None

# --- UI ---
st.title("Daily Trading Ranges")
st.write("Vergleich der Volatilitaet zwischen Tech- und Finanzwerten.")

selected_tech = st.sidebar.multiselect("Tech Stocks", list(TECH_STOCKS.keys()), default=["Apple"])
selected_fin = st.sidebar.multiselect("Financial Stocks", list(FINANCIAL_STOCKS.keys()), default=["J.P. Morgan"])

all_selected = {**{k: TECH_STOCKS[k] for k in selected_tech}, **{k: FINANCIAL_STOCKS[k] for k in selected_fin}}

if not all_selected:
    st.warning("Bitte waehlen Sie mindestens eine Aktie aus.")
    st.stop()

# Daten laden
stock_data = {}
for name, symbol in all_selected.items():
    df = get_stock_data_compact(symbol)
    if df is not None:
        stock_data[name] = df

if stock_data:
    # Boxplot der Volatilitaet
    fig_box = go.Figure()
    for name, df in stock_data.items():
        fig_box.add_trace(go.Box(y=df["rel_range_pct"], name=name))
    
    fig_box.update_layout(title="Relative Handelsspanne in %", template="plotly_dark")
    # Hier die neue Syntax 'width'
    st.plotly_chart(fig_box, width='stretch')
    
    # Tabelle mit Statistiken
    stats = []
    for name, df in stock_data.items():
        stats.append({
            "Aktie": name,
            "Durchschnitt (%)": round(df["rel_range_pct"].mean(), 2),
            "Max (%)": round(df["rel_range_pct"].max(), 2)
        })
    st.table(pd.DataFrame(stats))
