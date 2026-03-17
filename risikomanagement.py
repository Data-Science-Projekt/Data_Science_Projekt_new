import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- CONFIG ---
# Datenquellen werden nun lokal aus dem vom Bot gepflegten Ordner bezogen
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}

@st.cache_data(show_spinner=False)
def get_local_stock_returns(symbol):
    """Liest Aktiendaten lokal und berechnet die taeglichen Renditen."""
    file_path = f"data/stock_{symbol}.csv"
    
    if not os.path.exists(file_path):
        return None
        
    try:
        # Einlesen der vom Bot erstellten CSV
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        # Sortieren fuer korrekte zeitliche Abfolge der Renditen
        df = df.astype(float).sort_index()
        # Prozentuale Veraenderung (Returns) berechnen
        return df['4. close'].pct_change().dropna()
    except Exception:
        return None

# --- SIDEBAR ---
st.sidebar.header("Risiko-Einstellungen")
conf_level = st.sidebar.slider("Konfidenzniveau (prozent)", 90.0, 99.0, 95.0, 0.5) / 100
st.sidebar.divider()
show_apple = st.sidebar.checkbox("Apple (AAPL) anzeigen", value=True, key="risk_a")
show_nvidia = st.sidebar.checkbox("NVIDIA (NVDA) anzeigen", value=True, key="risk_n")

st.title("Value-at-Risk (VaR) und Expected Shortfall")
st.write("Quantifizierung potenzieller Verluste und Tail-Risiken fuer einzelne Assets.")

# --- DATA LOADING ---
ret_a = None
ret_n = None

if show_apple:
    ret_a = get_local_stock_returns(STOCKS["Apple"])
if show_nvidia:
    ret_n = get_local_stock_returns(STOCKS["NVIDIA"])

# --- PLOTTING ---
if (show_apple and ret_a is not None) or (show_nvidia and ret_n is not None):
    fig = go.Figure()

    if show_apple and ret_a is not None:
        # Historische Simulation des VaR
        v_a = np.percentile(ret_a, (1 - conf_level) * 100)
        # Expected Shortfall (Durchschnitt der Verluste jenseits des VaR)
        e_a = ret_a[ret_a <= v_a].mean()
        fig.add_trace(go.Histogram(x=ret_a, name="Apple", marker_color='#1f77b4', opacity=0.6))
        fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4", annotation_text="VaR AAPL")

    if show_nvidia and ret_n is not None:
        v_n = np.percentile(ret_n, (1 - conf_level) * 100)
        e_n = ret_n[ret_n <= v_n].mean()
        fig.add_trace(go.Histogram(x=ret_n, name="NVIDIA", marker_color='#ff7f0e', opacity=0.6))
        fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e", annotation_text="VaR NVDA")

    fig.update_layout(
        barmode='overlay',
        template="plotly_dark",
        xaxis_title="Taegliche Rendite",
        yaxis_title="Haeufigkeit",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Metriken unter dem Chart
    c1, c2 = st.columns(2)
    if show_apple and ret_a is not None:
        c1.subheader("Apple (AAPL)")
        c1.metric("Value-at-Risk", f"{v_a:.2%}")
        c1.metric("Expected Shortfall", f"{e_a:.2%}")
    if show_nvidia and ret_n is not None:
        c2.subheader("NVIDIA (NVDA)")
        c2.metric("Value-at-Risk", f"{v_n:.2%}")
        c2.metric("Expected Shortfall", f"{e_n:.2%}")

    # --- INTERPRETATION ---
    st.markdown("---")
    st.subheader("Analyse und Interpretation")

    st.info(f"""
    **Definition der Risikometriken:**
    - **Value-at-Risk (VaR):** Repraesentiert den maximal erwarteten Verlust ueber einen bestimmten Zeitraum bei einem gegebenen Konfidenzniveau ({conf_level * 100:.1f} prozent). 
    - **Expected Shortfall (CVaR):** Repraesentiert den durchschnittlichen Verlust, der eintritt, wenn der VaR-Schwellenwert ueberschritten wird (der Durchschnitt der schlimmsten Faelle).
    """)

    st.markdown("""
    ### Zentrale Erkenntnisse:

    * **Tail-Risk-Bewertung:** Waehrend die Standardabweichung (Volatilitaet) die allgemeine Unsicherheit misst, konzentrieren sich **VaR** und **Expected Shortfall** gezielt auf das linke Ende der Verteilung – dort, wo die signifikantesten Verluste auftreten.

    * **Apple vs. NVIDIA:** - Generell weist NVIDIA tendenziell einen **tieferen VaR** als Apple auf, was die hoehere historische Volatilitaet und das hoehere Beta widerspiegelt. 
        - Eine groessere Luecke zwischen VaR und Expected Shortfall deutet auf **Fat Tails** (Leptokurtosis) hin, was bedeutet, dass extreme Kursstuerze wahrscheinlicher sind, als eine Normalverteilung vermuten liesse.

    * **Einfluss des Konfidenzniveaus:** - Eine Erhoehung des Konfidenzniveaus (z. B. von 95 auf 99 prozent) verschiebt die VaR-Linie weiter nach links und erfasst extremere, aber seltenere Ereignisse. 
        - Anleger mit geringer Risikotoleranz sollten sich auf den **Expected Shortfall** konzentrieren, da dieser ein realistischeres Bild des potenziellen Schadens waehrend einer Marktkrise liefert.

    * **Limitierungen:** Diese Metriken basieren auf historischen Daten (letzte 100 Handelstage). Sie setzen voraus, dass sich das kuenftige Marktverhalten an der Vergangenheit orientiert, was waehrend beispielloser Black Swan Events nicht zwingend der Fall sein muss.
    """)

    st.caption("Berechnung: Historische Simulation basierend auf den letzten 100 Handelstagen. Datenquelle: Lokal (via Bot).")

else:
    st.info("Bitte waehlen Sie Assets aus oder stellen Sie sicher, dass die lokalen Daten vorhanden sind.")
