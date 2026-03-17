import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- KONFIGURATION ---
# Keine API-Keys oder lokaler Cache-Ordner mehr nötig.
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
ALL_STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

# --- FUNKTION: DATEN LADEN (LOKAL) ---
@st.cache_data(show_spinner="Lade historische Handelsdaten...")
def get_stock_data_local(symbol):
    """Liest die vom Bot erstellte CSV-Datei aus dem data-Ordner."""
    file_path = f"data/stock_{symbol}.csv"
    
    if not os.path.exists(file_path):
        return None
        
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        # Sortieren fuer korrekte Zeitreihen-Analyse
        df = df.astype(float).sort_index()
        
        # Berechnung der Handelsspanne (Range)
        # Spaltennamen von Alpha Vantage: 2. high, 3. low, 4. close
        df["absolute_range"] = df["2. high"] - df["3. low"]
        df["relative_range_pct"] = (df["absolute_range"] / df["4. close"]) * 100
        
        return df
    except Exception:
        return None

# --- HAUPT APP ---
st.title("Forschungsfrage 2: Taegliche Handelsspannen")
st.markdown("""
**Forschungsfrage:** Welche Unterschiede bestehen in der taeglichen Handelsspanne zwischen ausgewaehlten Tech-Aktien (Apple, Microsoft, NVIDIA) und Finanz-Aktien (J.P. Morgan, Goldman Sachs, Bank of America)?
""")

# Sidebar fuer Steuerlemente
st.sidebar.header("Analyse-Parameter")
# Da der Bot standardmaessig 100 Tage holt, ist dies das Maximum
days = st.sidebar.slider("Anzahl der Handelstage", min_value=10, max_value=100, value=100, step=10)
selected_tech = st.sidebar.multiselect("Tech-Aktien waehlen", list(TECH_STOCKS.keys()), default=list(TECH_STOCKS.keys()))
selected_financial = st.sidebar.multiselect("Finanz-Aktien waehlen", list(FINANCIAL_STOCKS.keys()), default=list(FINANCIAL_STOCKS.keys()))

if not selected_tech and not selected_financial:
    st.warning("Bitte waehlen Sie mindestens eine Aktie aus.")
    st.stop()

# Zusammenfuehren der Auswahl
selected_stocks = {**{k: TECH_STOCKS[k] for k in selected_tech}, **{k: FINANCIAL_STOCKS[k] for k in selected_financial}}

# Daten laden
stock_data = {}
with st.spinner("Lade Daten..."):
    for name, symbol in selected_stocks.items():
        df = get_stock_data_local(symbol)
        if df is not None:
            stock_data[name] = df.tail(days)

if not stock_data:
    st.error("Es konnten keine Daten geladen werden. Bitte Bot-Status pruefen.")
    st.stop()

# Gemeinsamen Datumsbereich ermitteln
min_date = max(df.index.min() for df in stock_data.values())
max_date = min(df.index.max() for df in stock_data.values())
for name in stock_data:
    stock_data[name] = stock_data[name][(stock_data[name].index >= min_date) & (stock_data[name].index <= max_date)]

# --- ERGEBNISSE ANZEIGEN ---
st.subheader("Zusammenfassung der Analyse")
st.write(f"**Zeitraum:** {min_date.strftime('%Y-%m-%d')} bis {max_date.strftime('%Y-%m-%d')} ({len(stock_data[list(stock_data.keys())[0]])} Handelstage)")

# Boxplot
st.subheader("Verteilung der taeglichen Handelsspannen (Prozent)")
fig_box = go.Figure()
for name, df in stock_data.items():
    fig_box.add_trace(go.Box(y=df["relative_range_pct"], name=name, boxmean=True))
fig_box.update_layout(yaxis_title="Relative Handelsspanne (%)", template="plotly_white")
st.plotly_chart(fig_box, use_container_width=True)

# Zeitreihe
st.subheader("Verlauf der Handelsspannen ueber Zeit")
fig_ts = go.Figure()
# Definierte Farben fuer bessere Unterscheidung
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
for i, (name, df) in enumerate(stock_data.items()):
    fig_ts.add_trace(go.Scatter(x=df.index, y=df["relative_range_pct"], mode="lines", name=name, line=dict(color=colors[i % len(colors)], width=1.5)))
fig_ts.update_layout(xaxis_title="Datum", yaxis_title="Relative Handelsspanne (%)", template="plotly_white")
st.plotly_chart(fig_ts, use_container_width=True)

# Statistik-Tabelle
st.subheader("Statistische Kennzahlen pro Aktie")
stats_data = []
for name, df in stock_data.items():
    ranges = df["relative_range_pct"]
    stats_data.append({
        "Aktie": name,
        "Sektor": "Tech" if name in TECH_STOCKS else "Finanz",
        "Mittelwert (%)": f"{ranges.mean():.2f}",
        "Median (%)": f"{ranges.median():.2f}",
        "Std. Abw. (%)": f"{ranges.std():.2f}",
        "Min (%)": f"{ranges.min():.2f}",
        "Max (%)": f"{ranges.max():.2f}",
    })
st.table(pd.DataFrame(stats_data))

# Sektor-Vergleich
st.subheader("Sektor-Vergleich")
tech_ranges = []
financial_ranges = []
for name, df in stock_data.items():
    if name in TECH_STOCKS:
        tech_ranges.extend(df["relative_range_pct"].tolist())
    elif name in FINANCIAL_STOCKS:
        financial_ranges.extend(df["relative_range_pct"].tolist())

tech_avg = np.mean(tech_ranges) if tech_ranges else 0
financial_avg = np.mean(financial_ranges) if financial_ranges else 0
diff = tech_avg - financial_avg

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Tech Durchschn. Spanne (%)", f"{tech_avg:.2f}")
with col2:
    st.metric("Finanz Durchschn. Spanne (%)", f"{financial_avg:.2f}")
with col3:
    st.metric("Differenz (Tech - Finanz)", f"{diff:.2f}")

# Fazit-Text
st.subheader("Zentrale Erkenntnisse")
summary_logic = "Tech-Aktien weisen eine hoehere Volatilitaet in den taeglichen Spannen auf." if diff > 0 else "Finanz-Aktien weisen eine hoehere Volatilitaet auf." if diff < 0 else "Beide Sektoren zeigen aehnliche Handelsspannen."
summary = f"""
Die Analyse der letzten {len(stock_data[list(stock_data.keys())[0]])} Handelstage zeigt:
Tech-Aktien haben eine durchschnittliche Spanne von {tech_avg:.2f}%, waehrend Finanz-Aktien im Schnitt bei {financial_avg:.2f}% liegen.
Die Differenz betraegt {diff:.2f} Prozentpunkte.
{summary_logic}
"""
st.write(summary)
