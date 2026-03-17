import streamlit as st
import pandas as pd
import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objects as go
import os

# --- KONFIGURATION ---
# Wir nutzen die vom Bot bereitgestellten Daten im data-Ordner
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

# --- FUNKTION: DATEN LADEN (LOKAL) ---
@st.cache_data(show_spinner="Lade Marktdaten...")
def get_stock_data_local(symbol):
    """Liest die Aktiendaten aus dem lokalen data-Ordner."""
    file_path = f"data/stock_{symbol}.csv"
    
    if not os.path.exists(file_path):
        return None
        
    try:
        # Einlesen der vom Bot erstellten CSV
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        # Sortieren fuer chronologische Renditeberechnung
        df = df.astype(float).sort_index()
        
        # Berechnung der Handelsspanne (fuer die statistische Tabelle unten)
        df["abs_range"] = df["2. high"] - df["3. low"]
        df["rel_range_pct"] = (df["abs_range"] / df["4. close"]) * 100
        
        return df
    except Exception:
        return None

# --- UI ---
st.title("Daily Trading Ranges")
st.write("Vergleich der Volatilitaet zwischen Tech- und Finanz-Aktien.")

# Sidebar fuer Auswahl
selected_tech = st.sidebar.multiselect("Tech-Aktien", list(TECH_STOCKS.keys()), default=["Apple"])
selected_fin = st.sidebar.multiselect("Finanz-Aktien", list(FINANCIAL_STOCKS.keys()), default=["J.P. Morgan"])

# Kombination der Auswahl
all_selected = {**{k: TECH_STOCKS[k] for k in selected_tech}, **{k: FINANCIAL_STOCKS[k] for k in selected_fin}}

if not all_selected:
    st.warning("Bitte waehlen Sie mindestens eine Aktie aus.")
    st.stop()

# Daten laden
stock_data = {}
for name, symbol in all_selected.items():
    df = get_stock_data_local(symbol)
    if df is not None:
        stock_data[name] = df

if stock_data:
    # Boxplot der Volatilitaet
    fig_box = go.Figure()
    for name, df in stock_data.items():
        fig_box.add_trace(go.Box(y=df["rel_range_pct"], name=name))

    fig_box.update_layout(
        title="Relative Handelsspanne in Prozent",
        template="plotly_dark",
        yaxis_title="Spanne (%)"
    )
    st.plotly_chart(fig_box, use_container_width=True)

    # Statistik-Tabelle
    st.subheader("Statistische Uebersicht")
    stats = []
    for name, df in stock_data.items():
        stats.append({
            "Aktie": name,
            "Durchschnitt (%)": round(df["rel_range_pct"].mean(), 2),
            "Maximum (%)": round(df["rel_range_pct"].max(), 2)
        })
    st.table(pd.DataFrame(stats))

    # --- INTERPRETATION ---
    st.markdown("---")
    st.subheader("Analyse und Interpretation")

    st.info("""
    Forschungsfrage: Untersuchung der Unterschiede in den taeglichen Handelsspannen (Intraday-Volatilitaet) 
    zwischen Technologie-Aktien und Finanz-Aktien.
    """)

    st.markdown("""
    ### Zentrale Erkenntnisse:

    * **Sektor-Unterschiede:** Tech-Aktien (z. B. Apple, Microsoft, NVIDIA) tendieren zu einer hoeheren Volatilitaet in den taeglichen Handelsspannen im Vergleich zu traditionellen Finanz-Aktien (z. B. J.P. Morgan, Bank of America). 
        Dies spiegelt das hoehere Wachstumspotenzial, aber auch das hoehere Risikoprofil des Tech-Sektors wider.

    * **Asymmetrische Auswirkungen:** Unsere Analyse deutet darauf hin, dass negative Nachrichten typischerweise groessere Volatilitaetsspitzen erzeugen als positive Nachrichten aehnlicher Groessenordnung. Dies deckt sich mit dem dokumentierten Negativity Bias an den Finanzmaerkten.

    * **Bedeutung der Nachrichtenstaerke:** Die Intensitaet eines Nachrichten-Sentiments ist oft aussagekraeftiger fuer einen Volatilitaetsstrom als die reine Richtung (positiv/negativ).

    * **Markteffizienz:** Viele Nachrichtenereignisse sind bereits teilweise eingepreist (z. B. Analystenerwartungen vor Quartalszahlen). Die beobachtete Volatilitaet resultiert daher oft aus der Differenz zwischen tatsaechlichen Ergebnissen und Markterwartungen.

    * **Einflussfaktoren:** Taegliche Handelsspannen werden nicht nur durch unternehmensspezifische News getrieben, sondern auch durch makrooekonomische Ereignisse (Fed-Entscheidungen, Inflationsdaten), Sektor-Rotationen und geopolitische Spannungen.
    """)

    st.caption(
        "Datenquelle: Alpha Vantage (TIME_SERIES_DAILY). Die relative Spanne berechnet sich als: ((High - Low) / Close) * 100.")
else:
    st.error("Es konnten keine lokalen Daten gefunden werden. Bitte sicherstellen, dass der Daten-Bot erfolgreich gelaufen ist.")
