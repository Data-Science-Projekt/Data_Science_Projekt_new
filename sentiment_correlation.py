import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from scipy.stats import pearsonr, spearmanr

# --- KONFIGURATION ---
# Keine API-Keys mehr notwendig, da wir die vom Bot erstellten CSVs nutzen.
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
ALL_STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

# --- FUNKTION: DATEN LADEN (LOKAL) ---
@st.cache_data(show_spinner="Lade lokale Marktdaten...")
def get_monthly_data_local(symbol):
    """Liest taegliche Aktiendaten und aggregiert sie auf Monatsbasis."""
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True).sort_index()
        # Aggregation auf Monatsstart (MS), um mit FRED-Daten kompatibel zu sein
        monthly = df[["4. close"]].resample("MS").last()
        monthly[f"{symbol}_return"] = monthly["4. close"].pct_change()
        return monthly[[f"{symbol}_return"]].dropna()
    except Exception:
        return None

@st.cache_data(show_spinner="Lade Consumer Sentiment...")
def get_sentiment_local():
    """Liest den Consumer Sentiment Index aus der lokalen CSV."""
    file_path = "data/consumer_sentiment.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])
        # Sicherstellen, dass das Datum auf den Monatsanfang normiert ist
        df['date'] = df['date'].dt.to_period("M").dt.to_timestamp()
        df = df.rename(columns={"value": "sentiment"})
        # Filtern von Platzhaltern (.) in FRED-Daten
        df['sentiment'] = pd.to_numeric(df['sentiment'], errors='coerce')
        return df.set_index('date')[['sentiment']].dropna()
    except Exception:
        return None

# --- UI ---
st.title("Forschungsfrage 8: Sentiment-Korrelation")
st.markdown("""
**Forschungsfrage:** Wie korreliert der Consumer Sentiment Index (University of Michigan) 
mit ausgewaehlten Tech-Aktien und Finanz-Aktien?
""")

st.markdown("""
#### Methodik
- **Consumer Sentiment Index:** Monatliche Umfrage zur Konsumstimmung (via FRED/Bot)
- **Monatliche Aktienrenditen:** Aggregiert aus taeglichen Daten (via Alpha Vantage/Bot)
- **Korrelationen:** Berechnung von Pearson (linear) und Spearman (Rang-basiert)
- **Rolling Correlation:** Analyse der zeitlichen Entwicklung der Beziehung
""")

# Sidebar
st.sidebar.header("Analyse-Parameter")
lookback_months = st.sidebar.slider("Betrachtungszeitraum (Monate)", 6, 48, 24)
rolling_window = st.sidebar.slider("Rolling Correlation Fenster (Monate)", 3, 12, 6)

# Daten laden
sentiment_df = get_sentiment_local()
if sentiment_df is None:
    st.error("Consumer Sentiment Daten konnten nicht geladen werden.")
    st.stop()

stock_returns = {}
for name, symbol in ALL_STOCKS.items():
    df = get_monthly_data_local(symbol)
    if df is not None:
        stock_returns[name] = df.rename(columns={f"{symbol}_return": name})

if not stock_returns:
    st.error("Keine Aktiendaten verfuegbar.")
    st.stop()

# Zusammenfuehren der Daten
merged = sentiment_df.copy()
for name, ret_df in stock_returns.items():
    merged = merged.join(ret_df, how="inner")

# Zeitraum filtern
merged = merged.tail(lookback_months).dropna()

if len(merged) < 3:
    st.warning("Zu wenig ueberschneidende Datenpunkte fuer eine Korrelation.")
    st.stop()

st.write(f"**Zeitraum:** {merged.index.min().strftime('%Y-%m')} bis {merged.index.max().strftime('%Y-%m')} ({len(merged)} Monate)")

# --- 1. VISUALISIERUNG SENTIMENT ---
st.subheader("1. Verlauf
