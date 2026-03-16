import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import os

AV_API_KEY = st.secrets.get("AV_API_KEY", "")
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA", "S&P 500": "SPY"}

@st.cache_data(show_spinner="Lade Daten...")
def get_stock_data(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url)
        data = r.json()
        if "Time Series (Daily)" in data:
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float).sort_index()
            df.rename(columns={"4. close": "close"}, inplace=True)
            return df[["close"]]
        return None
    except:
        return None

def identify_phases(close_values, index_values):
    df = pd.DataFrame({'close': close_values}, index=pd.to_datetime(index_values))
    df['rolling_max'] = df['close'].rolling(window=20, min_periods=1).max()
    df['rolling_min'] = df['close'].rolling(window=20, min_periods=1).min()
    df['phase'] = 'Neutral'
    df.loc[(df['close'] - df['rolling_max']) / df['rolling_max'] <= -0.2, 'phase'] = 'Bear'
    df.loc[(df['close'] - df['rolling_min']) / df['rolling_min'] >= 0.2, 'phase'] = 'Bull'
    return df

st.title("Marktphasen Analyse")

selected_stock = st.sidebar.selectbox("Aktie waehlen:", list(STOCKS.keys()))
df_raw = get_stock_data(STOCKS[selected_stock])

if df_raw is not None:
    df_view = identify_phases(df_raw['close'].tolist(), df_raw.index.tolist())
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_view.index, y=df_view['close'], name='Preis'))
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, width='stretch')
    
    st.write("Anzahl Tage pro Phase:")
    st.table(df_view['phase'].value_counts())
