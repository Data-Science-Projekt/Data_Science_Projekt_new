import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- KONFIGURATION ---
# Keine API-Keys mehr nötig. Sektoren basieren auf den vom Bot geladenen Dateien.
SECTORS = {
    "Tech": ["AAPL", "MSFT", "NVDA"],
    "Financial": ["JPM", "GS", "BAC"]
}

# --- DATEN LADEN (LOKAL) ---
@st.cache_data(show_spinner="Berechne Volumen-Muster...")
def get_volume_zscore_local(symbol):
    """Liest lokale CSV und berechnet den Z-Score des Handelsvolumens."""
    file_path = f"data/stock_{symbol}.csv"
    
    if not os.path.exists(file_path):
        return None
        
    try:
        # Einlesen der vom Bot erstellten CSV
        df = pd.read_csv(file_path, index_col=0, parse_dates=True).sort_index()
        
        # Spaltenname bei Alpha Vantage CSVs ist '5. volume'
        if '5. volume' not in df.columns:
            return None
            
        vol = df["5. volume"]

        # Z-Score Berechnung (20-Tage-Fenster)
        # Formel: (Aktuelles Volumen - Durchschnitt) / Standardabweichung
        avg = vol.rolling(window=20).mean()
        std = vol.rolling(window=20).std()
        z_score = (vol - avg) / std
        
        return z_score.dropna()
    except Exception:
        return None

def get_sector_data_local(sector_name):
    """Aggregiert die Z-Scores aller Aktien eines Sektors."""
    symbols = SECTORS[sector_name]
    all_z = []
    
    for s in symbols:
        data = get_volume_zscore_local(s)
        if data is not None:
            # Wir benennen die Serie nach dem Symbol für das spätere Concatenating
            data.name = s
            all_z.append(data)

    if all_z:
        # Berechnet den Mittelwert über alle Aktien im Sektor pro Tag
        df_combined = pd.concat(all_z, axis=1).mean(axis=1)
        return df_combined
    return None

# --- UI ---
st.title("Volumen-Muster: Tech vs. Finanzsektor")
st.markdown("Vergleich der Handelsintensitaet und abnormaler Volumenspitzen (Spikes) zwischen den Sektoren.")

with st.sidebar:
    st.header("Sektor-Auswahl")

    # Tech Auswahl
    tech_options = ["Alle (Sektor-Durchschnitt)"] + SECTORS["Tech"]
    tech_choice = st.selectbox("Tech-Sektor Asset:", tech_options)

    # Finanz Auswahl
    fin_options = ["Alle (Sektor-Durchschnitt)"] + SECTORS["Financial"]
    fin_choice = st.selectbox("Finanz-Sektor Asset:", fin_options)

    spike_threshold = st.slider("Spike-Schwellenwert (Z-Score):", 1.0, 4.0, 2.0, step=0.1)

# Daten laden (Lokal)
if tech_choice == "Alle (Sektor-Durchschnitt)":
    df_tech = get_sector_data_local("Tech")
    tech_label = "Tech Sektor Schnitt"
else:
    df_tech = get_volume_zscore_local(tech_choice)
    tech_label = tech_choice

if fin_choice == "Alle (Sektor-Durchschnitt)":
    df_fin = get_sector_data_local("Financial")
    fin_label = "Finanz Sektor Schnitt"
else:
    df_fin = get_volume_zscore_local(fin_choice)
    fin_label = fin_choice

# --- VISUALISIERUNG ---
if df_tech is not None and df_fin is not None:
    # Zeitachsen synchronisieren
    plot_df = pd.DataFrame({tech_label: df_tech, fin_label: df_fin}).dropna()

    fig = go.Figure()

    # Tech Balken
    fig.add_trace(go.Bar(
        x=plot_df.index,
        y=plot_df[tech_label],
        name=tech_label,
        marker_color='#1f77b4',
        hovertemplate="Datum: %{x}<br>Z-Score: %{y:.2f}<extra></extra>"
    ))

    # Finanz Balken
    fig.add_trace(go.Bar(
        x=plot_df.index,
        y=plot_df[fin_label],
        name=fin_label,
        marker_color='#ff7f0e',
        hovertemplate="Datum: %{x}<br>Z-Score: %{y:.2f}<extra></extra>"
    ))

    # Schwellenwert-Linie
    fig.add_hline(y=spike_threshold, line_dash="dash", line_color="red",
                  annotation_text=f"Spike-Niveau ({spike_threshold})")

    fig.update_layout(
        title=f"Volumen-Anomalie: {tech_label} vs. {fin_label}",
        xaxis_title="Datum",
        yaxis_title="Volumen Z-Score",
        barmode='group',
        template="plotly_white",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- STATISTIK ---
    st.subheader("Frequenz-Analyse")

    tech_spikes = len(plot_df[plot_df[tech_label] > spike_threshold])
    fin_spikes = len(plot_df[plot_df[fin_label] > spike_threshold])

    c1, c2, c3 = st.columns(3)
    c1.metric(f"{tech_label} Spikes", tech_spikes)
    c2.metric(f"{fin_label} Spikes", fin_spikes)
    c3.metric("Beobachtungstage", len(plot_df))

    # --- INTERPRETATION ---
    st.info(f"""
    **Interpretation:** Ein Z-Score von **{spike_threshold:.1f}** bedeutet, dass das Handelsvolumen signifikant vom Normalwert 
    abweicht (es liegt **{spike_threshold:.1f} Standardabweichungen** ueber dem gleitenden 20-Tage-Durchschnitt). 
    Dies deutet auf ausserordentliche Marktaktivitaet hin, oft ausgeloest durch News oder Earnings.
    """)
else:
    st.error("Lokale Daten konnten nicht geladen werden. Bitte sicherstellen, dass der Daten-Bot die CSV-Dateien erstellt hat.")
