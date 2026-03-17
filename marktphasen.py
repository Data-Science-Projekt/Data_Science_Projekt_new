import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- KONFIGURATION ---
# Keine API-Keys mehr erforderlich, da wir lokal lesen.
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA", "Microsoft": "MSFT", "J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}

@st.cache_data(show_spinner="Lade lokale Daten...")
def get_stock_data(symbol):
    """Liest die vom Bot erstellte CSV-Datei aus dem data-Ordner."""
    file_path = f"data/stock_{symbol}.csv"
    
    if not os.path.exists(file_path):
        return None
        
    try:
        # Einlesen der CSV (Index ist das Datum)
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        # Sortieren, damit das älteste Datum oben steht (wichtig für rolling windows)
        df = df.sort_index()
        # Umbenennen der Alpha Vantage Spalte '4. close' zu 'close'
        if '4. close' in df.columns:
            df.rename(columns={"4. close": "close"}, inplace=True)
        return df[["close"]]
    except Exception:
        return None

def identify_phases(df_input):
    """Berechnet Marktphasen basierend auf 20-Tage Rolling Window."""
    df = df_input.copy()
    # Rolling Max/Min für die Phasen-Logik
    df['rolling_max'] = df['close'].rolling(window=20, min_periods=1).max()
    df['rolling_min'] = df['close'].rolling(window=20, min_periods=1).min()

    # Logik: -20% vom Hoch = Bear / +20% vom Tief = Bull
    df['phase'] = np.select(
        [
            (df['close'] - df['rolling_max']) / df['rolling_max'] <= -0.2,
            (df['close'] - df['rolling_min']) / df['rolling_min'] >= 0.2
        ],
        ['Bear', 'Bull'],
        default='Neutral'
    )
    return df

# --- UI ---
st.title("Market Phase Analysis")
st.write("Identifikation von Bull-, Bear- und Neutral-Phasen mittels Rolling-Window-Ansatz.")

selected_stock = st.sidebar.selectbox("Asset auswählen:", list(STOCKS.keys()))
df_raw = get_stock_data(STOCKS[selected_stock])

if df_raw is not None:
    df_view = identify_phases(df_raw)

    # Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_view.index, y=df_view['close'], name='Preis'))
    fig.update_layout(template="plotly_dark", xaxis_title="Datum", yaxis_title="Preis")
    st.plotly_chart(fig, use_container_width=True)

    # Phasen-Verteilung
    st.subheader("Verteilung der Marktphasen")
    counts = df_view['phase'].value_counts()
    percentages = (counts / len(df_view) * 100).round(2)

    dist_df = pd.DataFrame({
        "Tage": counts,
        "Anteil (prozent)": percentages
    })
    st.table(dist_df)

    # --- Interpretation ---
    st.markdown("---")
    st.subheader("Interpretation und Einblicke")

    bull_pct = percentages.get("Bull", 0)
    bear_pct = percentages.get("Bear", 0)
    neutral_pct = percentages.get("Neutral", 0)

    st.markdown(f"""
### Analyse-Ergebnisse

**1. Markt-Regime Uebersicht**
- Das Asset verbrachte **{bull_pct}%** der Zeit in einer Bull-Phase.
- **{bear_pct}%** in einer Bear-Phase.
- **{neutral_pct}%** in einer neutralen Phase.

Dies ermoeglicht ein direktes Verstaendnis der dominanten Marktumgebung im betrachteten Zeitraum.

---

**2. Trendstaerke**
- Ein hoher Bull-Anteil deutet auf starke Aufwaertsdynamik hin.
- Ein hoher Bear-Anteil weist auf laengere Korrekturen oder Abschwuenge hin.
- Ein hoher Neutral-Anteil signalisiert Seitwaertsbewegungen oder Konsolidierungen.

---

**3. Volatilitaet und Verhalten**
- Aktien wie NVIDIA wechseln Phasen oft haeufiger aufgrund hoeherer Volatilitaet.
- Etablierte Titel zeigen oft stabilere und laengere Trends.

---

**4. Strategische Implikationen**
- Bull-Phasen: Trendfolgende Strategien sind oft vorteilhaft.
- Bear-Phasen: Risikomanagement und defensive Positionierung sind entscheidend.
- Neutral-Phasen: Range-Trading oder das Warten auf Ausbrueche ist oft effektiver.

---

**5. Methodischer Hinweis**
Dieses Modell nutzt ein 20-Tage-Fenster:
- 20 prozent Abfall vom letzten Hoch -> Bear
- 20 prozent Anstieg vom letzten Tief -> Bull

Dies ist eine vereinfachte, aber in der Finanzanalyse weit verbreitete Definition von Marktzyklen.
""")

    st.caption("Methodik: Rolling 20-Tage Fenster Analyse der Preisbewegungen.")

else:
    st.error("Daten konnten nicht geladen werden. Bitte sicherstellen, dass die CSV-Dateien im data-Ordner vorhanden sind.")
