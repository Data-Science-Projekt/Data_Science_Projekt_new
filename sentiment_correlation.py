import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from scipy.stats import pearsonr, spearmanr

# --- KONFIGURATION ---
# Die Sektoren basieren auf den vom Bot erstellten Dateien
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
        # Einlesen der vom Bot erstellten CSV
        df = pd.read_csv(file_path, index_col=0, parse_dates=True).sort_index()
        # Aggregation auf Monatsstart (MS) fuer Vergleichbarkeit mit FRED
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
        # Datum vereinheitlichen
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].dt.to_period("M").dt.to_timestamp()
        df = df.rename(columns={"value": "sentiment"})
        # FRED-Daten bereinigen (Punkte zu NaN)
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

# Sidebar
st.sidebar.header("Analyse-Parameter")
lookback_months = st.sidebar.slider("Betrachtungszeitraum (Monate)", 6, 48, 24)
rolling_window = st.sidebar.slider("Rolling Correlation Fenster (Monate)", 3, 12, 6)

# Daten laden
sentiment_df = get_sentiment_local()
stock_returns = {}

if sentiment_df is not None:
    for name, symbol in ALL_STOCKS.items():
        df = get_monthly_data_local(symbol)
        if df is not None:
            stock_returns[name] = df.rename(columns={f"{symbol}_return": name})

if sentiment_df is None or not stock_returns:
    st.error("Daten konnten nicht geladen werden. Bitte Bot-Status im Repository prüfen.")
    st.stop()

# Zusammenfuehren
merged = sentiment_df.copy()
for name, ret_df in stock_returns.items():
    merged = merged.join(ret_df, how="inner")

# Zeitraum filtern
merged = merged.tail(lookback_months).dropna()

if len(merged) < 3:
    st.warning("Zu wenige ueberschneidende Datenpunkte vorhanden.")
    st.stop()

st.write(f"**Zeitraum:** {merged.index.min().strftime('%Y-%m')} bis {merged.index.max().strftime('%Y-%m')}")

# --- 1. VISUALISIERUNG SENTIMENT ---
st.subheader("1. Verlauf des Consumer Sentiment Index")
fig_sent = go.Figure()
fig_sent.add_trace(go.Scatter(
    x=merged.index, y=merged["sentiment"],
    mode="lines+markers", name="Consumer Sentiment",
    line=dict(color="#1f77b4", width=2)
))
fig_sent.update_layout(yaxis_title="Sentiment Index", template="plotly_white", height=400)
st.plotly_chart(fig_sent, use_container_width=True)

# --- 2. KORRELATIONSMATRIX ---
st.subheader("2. Korrelations-Matrix")
stock_names = list(stock_returns.keys())
corr_matrix = merged[["sentiment"] + stock_names].corr()

fig_heatmap = go.Figure(data=go.Heatmap(
    z=corr_matrix.values,
    x=corr_matrix.columns,
    y=corr_matrix.index,
    colorscale="RdBu_r",
    zmid=0,
    text=np.round(corr_matrix.values, 3),
    texttemplate="%{text}"
))
fig_heatmap.update_layout(template="plotly_white", height=500)
st.plotly_chart(fig_heatmap, use_container_width=True)

# --- 3. DETAILLIERTE STATISTIK ---
st.subheader("3. Detaillierte Korrelations-Statistik")
corr_results = []
for name in stock_names:
    r_p, p_p = pearsonr(merged["sentiment"], merged[name])
    r_s, p_s = spearmanr(merged["sentiment"], merged[name])
    corr_results.append({
        "Aktie": name,
        "Sektor": "Tech" if name in TECH_STOCKS else "Finanz",
        "Pearson r": round(r_p, 4),
        "P-Value (P)": round(p_p, 4),
        "Spearman r": round(r_s, 4)
    })
st.table(pd.DataFrame(corr_results))

# --- 4. ROLLING CORRELATION ---
st.subheader("4. Zeitliche Entwicklung (Rolling Correlation)")
fig_rolling = go.Figure()
for name in stock_names:
    rolling_corr = merged["sentiment"].rolling(rolling_window).corr(merged[name])
    fig_rolling.add_trace(go.Scatter(x=merged.index, y=rolling_corr, mode="lines", name=name))

fig_rolling.add_hline(y=0, line_dash="dash", line_color="gray")
fig_rolling.update_layout(
    yaxis_title=f"Rolling {rolling_window}-Monats Korrelation",
    template="plotly_white", height=500
)
st.plotly_chart(fig_rolling, use_container_width=True)

# --- 5. INTERPRETATION ---
st.subheader("5. Zentrale Erkenntnisse")

# Berechnung der Sektor-Durchschnitte
avg_tech = np.mean([c["Pearson r"] for c in corr_results if c["Sektor"] == "Tech"])
avg_fin = np.mean([c["Pearson r"] for c in corr_results if c["Sektor"] == "Finanz"])

summary_text = f"""
Basierend auf der Analyse der letzten {len(merged)} Monate ergeben sich folgende Punkte:

- **Durchschnittliche Tech-Korrelation:** {avg_tech:.4f}
- **Durchschnittliche Finanz-Korrelation:** {avg_fin:.4f}

**Interpretation der Ergebnisse:**
1. Positive Werte deuten darauf hin, dass steigender Optimismus der Konsumenten mit hoeheren Aktienrenditen einhergeht.
2. Finanz-Aktien zeigen oft eine direkte Sensitivitaet gegenueber der Konsumstimmung, da diese eng mit der Kreditnachfrage verknuepft ist.
3. Tech-Aktien reagieren oft sensibel auf das Sentiment, da dieses als Fruehindikator fuer Ausgaben fuer Hardware und Software-Services gilt.
4. Die statistische Signifikanz (P-Value < 0.05) gibt an, ob die beobachtete Beziehung stabil oder zufaellig ist.
"""

st.markdown(summary_text)
st.caption("Datenquelle: Lokal (aggregiert via Bot). Sentiment: Univ. of Michigan (FRED). Aktien: Alpha Vantage.")
