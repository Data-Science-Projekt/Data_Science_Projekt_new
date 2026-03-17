import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

# --- CONFIGURATION ---
# No API keys needed anymore. Sectors are based on locally loaded files.
SECTORS = {
    "Tech": ["AAPL", "MSFT", "NVDA"],
    "Financial": ["JPM", "GS", "BAC"]
}

# --- LOAD DATA (LOCAL) ---
@st.cache_data(show_spinner="Calculating volume patterns...")
def get_volume_zscore_local(symbol):
    """Reads local CSV and calculates the volume Z-score."""
    file_path = f"data/stock_{symbol}.csv"
    
    if not os.path.exists(file_path):
        return None
        
    try:
        # Read CSV created by the bot
        df = pd.read_csv(file_path, index_col=0, parse_dates=True).sort_index()
        
        # Column name in Alpha Vantage CSVs is '5. volume'
        if '5. volume' not in df.columns:
            return None
            
        vol = df["5. volume"]

        # Z-score calculation (20-day window)
        # Formula: (Current volume - average) / standard deviation
        avg = vol.rolling(window=20).mean()
        std = vol.rolling(window=20).std()
        z_score = (vol - avg) / std
        
        return z_score.dropna()
    except Exception:
        return None

def get_sector_data_local(sector_name):
    """Aggregates Z-scores of all stocks in a sector."""
    symbols = SECTORS[sector_name]
    all_z = []
    
    for s in symbols:
        data = get_volume_zscore_local(s)
        if data is not None:
            # Name the series for later concatenation
            data.name = s
            all_z.append(data)

    if all_z:
        # Calculate the mean across all stocks per day
        df_combined = pd.concat(all_z, axis=1).mean(axis=1)
        return df_combined
    return None

# --- UI ---
render_page_header(
    "Technical Analysis",
    "How do trading volume patterns (frequency of volume spikes) differ between selected tech stocks (Apple, Microsoft, NVIDIA) and selected financial stocks (J.P. Morgan, Goldman Sachs, Bank of America)?",
)

with st.sidebar:
    st.header("Sector Selection")

    # Tech selection
    tech_options = ["All (sector average)"] + SECTORS["Tech"]
    tech_choice = st.selectbox("Tech sector asset:", tech_options)

    # Financial selection
    fin_options = ["All (sector average)"] + SECTORS["Financial"]
    fin_choice = st.selectbox("Financial sector asset:", fin_options)

    spike_threshold = st.slider("Spike threshold (Z-score):", 1.0, 4.0, 2.0, step=0.1)

# Load data (local)
if tech_choice == "All (sector average)":
    df_tech = get_sector_data_local("Tech")
    tech_label = "Tech sector average"
else:
    df_tech = get_volume_zscore_local(tech_choice)
    tech_label = tech_choice

if fin_choice == "All (sector average)":
    df_fin = get_sector_data_local("Financial")
    fin_label = "Financial sector average"
else:
    df_fin = get_volume_zscore_local(fin_choice)
    fin_label = fin_choice

# --- VISUALIZATION ---
if df_tech is not None and df_fin is not None:
    # Synchronize time axes
    plot_df = pd.DataFrame({tech_label: df_tech, fin_label: df_fin}).dropna()

    fig = go.Figure()

    # Tech bars
    fig.add_trace(go.Bar(
        x=plot_df.index,
        y=plot_df[tech_label],
        name=tech_label,
        marker_color='#1f77b4',
        hovertemplate="Date: %{x}<br>Z-Score: %{y:.2f}<extra></extra>"
    ))

    # Financial bars
    fig.add_trace(go.Bar(
        x=plot_df.index,
        y=plot_df[fin_label],
        name=fin_label,
        marker_color='#ff7f0e',
        hovertemplate="Date: %{x}<br>Z-Score: %{y:.2f}<extra></extra>"
    ))

    # Threshold line
    fig.add_hline(y=spike_threshold, line_dash="dash", line_color="red",
                  annotation_text=f"Spike level ({spike_threshold})")

    fig.update_layout(
        title=f"Volume anomaly: {tech_label} vs. {fin_label}",
        xaxis_title="Date",
        yaxis_title="Volume Z-Score",
        barmode='group',
        template="plotly_white",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.download_button(
        label="📥 Graph als PDF herunterladen",
        data=fig_to_pdf_bytes(fig),
        file_name="marktphasen.pdf",
        mime="application/pdf"
    )

    # --- STATISTICS ---
    st.subheader("Frequency Analysis")

    tech_spikes = len(plot_df[plot_df[tech_label] > spike_threshold])
    fin_spikes = len(plot_df[plot_df[fin_label] > spike_threshold])

    c1, c2, c3 = st.columns(3)
    c1.metric(f"{tech_label} spikes", tech_spikes)
    c2.metric(f"{fin_label} spikes", fin_spikes)
    c3.metric("Observation days", len(plot_df))

    # --- INTERPRETATION ---
    st.info(f"""
    **Interpretation:** A Z-score of **{spike_threshold:.1f}** means that trading volume significantly deviates 
    from the normal level (it is **{spike_threshold:.1f} standard deviations** above the 20-day moving average). 
    This indicates unusual market activity, often triggered by news or earnings.
    """)
else:
    st.error("Local data could not be loaded. Please ensure that the data bot has created the CSV files.")
