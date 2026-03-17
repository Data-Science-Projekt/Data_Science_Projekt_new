import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os


STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}

# --- DATA LOADING ---
@st.cache_data(show_spinner="Lade Aktiendaten...")
def get_stock_data(symbol):
    """Liest Aktiendaten aus der lokalen CSV-Datei."""
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path):
        return None
    try:
        # Einlesen und Index als Datum formatieren
        df = pd.read_csv(file_path, index_col=0, parse_dates=True).sort_index()
        # Log-Returns fuer genaueren statistischen Vergleich berechnen
        df['Returns'] = np.log(df['4. close'] / df['4. close'].shift(1))
        # Wir behalten die Spalte '4. close' fuer den Plot bei
        return df[['4. close', 'Returns']].dropna()
    except Exception:
        return None

@st.cache_data(show_spinner="Lade VIX-Daten...")
def get_vix_data():
    """Liest VIX-Daten aus der lokalen macro_vix.csv."""
    file_path = "data/macro_vix.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        # In FRED-CSVs ist die Spalte oft klein geschrieben ('date')
        df['date'] = pd.to_datetime(df['date'])
        # VIX-Werte in numerisches Format umwandeln (behandelt Punkte/Fehler als NaN)
        df['VIX'] = pd.to_numeric(df['value'], errors='coerce')
        return df.set_index('date')[['VIX']].dropna()
    except Exception:
        return None

# --- UI ---
st.title("Market Reaction: Stocks vs. VIX")
st.markdown("Analyse der Aktienreaktion waehrend Perioden erhoehter Marktvolatilitaet (VIX).")

with st.sidebar:
    st.header("Einstellungen")
    selected_stock = st.selectbox("Aktie waehlen:", list(STOCKS.keys()))
    # Schwellenwert fuer Panik-Zonen (VIX > Schwelle)
    vix_threshold = st.slider("VIX Panik-Schwellenwert:", 10.0, 40.0, 20.0, step=0.5)
    st.info("Die rot schraffierten Flaechen stellen Tage dar, an denen der VIX > Schwellenwert ist.")

# Daten verarbeiten
df_vix = get_vix_data()
df_stock = get_stock_data(STOCKS[selected_stock])

if df_stock is not None and df_vix is not None:
    # Daten zusammenfuehren (Inner Join kombiniert nur Tage, die in beiden Datensaetzen existieren)
    combined = df_stock.join(df_vix, how='inner')

    # Panik-Tage markieren
    combined['Panic'] = combined['VIX'] > vix_threshold
    panic_days = combined[combined['Panic']]

    # --- PLOT ---
    fig = go.Figure()

    # Aktienkurs (Y1 - Links)
    fig.add_trace(go.Scatter(
        x=combined.index, y=combined['4. close'],
        name=f"{selected_stock} Preis", yaxis="y1",
        line=dict(color='#1f77b4', width=2)
    ))

    # VIX (Y2 - Rechts)
    fig.add_trace(go.Scatter(
        x=combined.index, y=combined['VIX'],
        name="VIX Index", yaxis="y2",
        line=dict(color='gray', dash='dot', width=1),
        opacity=0.5
    ))

    # Rote Panik-Zonen einzeichnen (1-Tages-Breite)
    for day in panic_days.index:
        fig.add_vrect(
            x0=day,
            x1=day + pd.Timedelta(days=1),
            fillcolor="red",
            opacity=0.25,
            layer="below",
            line_width=0
        )

    fig.update_layout(
        title=f"{selected_stock} Reaktion auf Marktvolatilitaet (Schwellenwert: {vix_threshold})",
        xaxis_title="Datum",
        yaxis=dict(title="Aktienkurs ($)", side="left"),
        yaxis2=dict(title="VIX Index", overlaying="y", side="right", range=[0, 50]),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- STATISTIK ---
    st.subheader("Statistische Auswirkung")

    normal_data = combined[~combined['Panic']]
    panic_data = combined[combined['Panic']]

    col1, col2, col3 = st.columns(3)

    # Normale Bewegung
    normal_move = 0
    if not normal_data.empty:
        normal_move = normal_data['Returns'].mean()
        col1.metric("Durchschn. Rendite (Normal)", f"{normal_move:.2%}")

    # Panik-Bewegung
    if not panic_data.empty:
        panic_move = panic_data['Returns'].mean()
        col2.metric(f"Rendite bei VIX > {vix_threshold}", f"{panic_move:.2%}",
                    delta=f"{(panic_move - normal_move):.2%}" if not normal_data.empty else None,
                    delta_color="inverse")
        col3.metric("Tage im Panik-Zustand", len(panic_data))
    else:
        col2.metric(f"Rendite bei VIX > {vix_threshold}", "Keine Daten")
        st.warning(f"Keine Tage gefunden, an denen der VIX ueber {vix_threshold} lag. Verringern Sie den Schwellenwert!")

    # --- INTERPRETATION ---
    st.divider()
    st.subheader("Analyse und Interpretation")

    st.markdown(f"""
    **Anleitung zum Lesen des Charts:**
    * **Blaue Linie:** Der Schlusskurs von {selected_stock}.
    * **Grau gepunktete Linie:** Der VIX Index, oft als Angstbarometer bezeichnet.
    * **Rote Bereiche:** Zeitraeume, in denen die Volatilitaet Ihren Schwellenwert ueberschritt.

    ### Zentrale Erkenntnisse:

    * **Marktsensitivitaet:** Aktien mit hohem Beta wie NVIDIA zeigen oft eine staerkere negative Korrelation zum VIX. Sinkt der Kurs stark bei VIX-Spitzen (rote Zonen), deutet dies auf hohe Anfaelligkeit fuer systemische Risiken hin.

    * **Statistische Abweichung:** Der Vergleich zwischen normaler Rendite und Panik-Rendite zeigt den direkten Einfluss von Marktangst. Signifikant negative Renditen in Panik-Phasen deuten darauf hin, dass das Asset nicht als sicherer Hafen wahrgenommen wird.

    * **Erholungsgeschwindigkeit:** Beobachten Sie das Verhalten unmittelbar nach Ende einer roten Zone. Schnelle Erholungen deuten auf starke Fundamentaldaten hin, waehrend laengere Rueckgaenge auf einen Trendwechsel hindeuten koennen.

    * **Bedeutung des Schwellenwerts:** Ein niedriger Wert (z. B. VIX 15) erfasst allgemeines Marktrauschen, waehrend ein hoher Wert (z. B. VIX 30) echte Krisen oder Black Swan Events isoliert.
    """)

    st.caption("Datenquellen: Alpha Vantage (Aktienkurse) und FRED (CBOE Volatilitätsindex - VIX).")
else:
    st.info("Bitte warten Sie, waehrend die lokalen Daten geladen werden.")
