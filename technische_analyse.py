import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

# --- CONFIGURATION ---
AV_API_KEY = st.secrets.get("AV_API_KEY", "")
SECTORS = {
    "Tech": ["AAPL", "MSFT", "NVDA"],
    "Financial": ["JPM", "GS", "BAC"]
}



# --- DATA FETCHING ---
@st.cache_data(show_spinner="Fetching market data...")
def get_volume_zscore(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url).json()
        if "Time Series (Daily)" in r:
            df = pd.DataFrame.from_dict(r['Time Series (Daily)'], orient='index').astype(float).sort_index()
            df.index = pd.to_datetime(df.index)
            vol = df["5. volume"]

            # Z-Score Calculation (20-day window)
            avg = vol.rolling(window=20).mean()
            std = vol.rolling(window=20).std()
            z_score = (vol - avg) / std
            return z_score.dropna()
    except:
        return None
    return None


def get_sector_data(sector_name):
    symbols = SECTORS[sector_name]
    all_z = []
    for s in symbols:
        data = get_volume_zscore(s)
        if data is not None:
            all_z.append(data)

    if all_z:
        # Calculates the mean across all stocks in the sector for each day
        df_combined = pd.concat(all_z, axis=1).mean(axis=1)
        return df_combined
    return None


# --- UI ---
st.title("Volume Patterns: Tech vs. Financials")
st.markdown("Comparing trading intensity and abnormal volume spikes across sectors.")

with st.sidebar:
    st.header("Sector Selection")

    # Tech Selection
    tech_options = ["All (Sector Average)"] + SECTORS["Tech"]
    tech_choice = st.selectbox("Tech Sector Asset:", tech_options)

    # Financial Selection
    fin_options = ["All (Sector Average)"] + SECTORS["Financial"]
    fin_choice = st.selectbox("Financial Sector Asset:", fin_options)

    spike_threshold = st.slider("Spike Threshold (Z-Score):", 1.0, 4.0, 2.0, step=0.1)

# Load Data
if tech_choice == "All (Sector Average)":
    df_tech = get_sector_data("Tech")
    tech_label = "Tech Sector Avg"
else:
    df_tech = get_volume_zscore(tech_choice)
    tech_label = tech_choice

if fin_choice == "All (Sector Average)":
    df_fin = get_sector_data("Financial")
    fin_label = "Financial Sector Avg"
else:
    df_fin = get_volume_zscore(fin_choice)
    fin_label = fin_choice

# --- VISUALIZATION ---
if df_tech is not None and df_fin is not None:
    # Synchronize time axes
    plot_df = pd.DataFrame({tech_label: df_tech, fin_label: df_fin}).dropna()

    fig = go.Figure()

    # Tech Bars
    fig.add_trace(go.Bar(
        x=plot_df.index,
        y=plot_df[tech_label],
        name=tech_label,
        marker_color='#1f77b4',
        hovertemplate="Date: %{x}<br>Z-Score: %{y:.2f}<extra></extra>"
    ))

    # Financial Bars
    fig.add_trace(go.Bar(
        x=plot_df.index,
        y=plot_df[fin_label],
        name=fin_label,
        marker_color='#ff7f0e',
        hovertemplate="Date: %{x}<br>Z-Score: %{y:.2f}<extra></extra>"
    ))

    # Threshold Line
    fig.add_hline(y=spike_threshold, line_dash="dash", line_color="red",
                  annotation_text=f"Spike Level ({spike_threshold})")

    fig.update_layout(
        title=f"Volume Abnormality: {tech_label} vs {fin_label}",
        xaxis_title="Date",
        yaxis_title="Volume Z-Score",
        barmode='group',
        template="plotly_white",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- STATISTICS ---
    st.subheader("Frequency Analysis")

    tech_spikes = len(plot_df[plot_df[tech_label] > spike_threshold])
    fin_spikes = len(plot_df[plot_df[fin_label] > spike_threshold])

    c1, c2, c3 = st.columns(3)
    c1.metric(f"{tech_label} Spikes", tech_spikes)
    c2.metric(f"{fin_label} Spikes", fin_spikes)
    c3.metric("Observation Days", len(plot_df))

    # --- INTERPRETATION (The Blue Box) ---
    st.info(f"""
    **Interpretation:** A Z-Score of **{spike_threshold:.1f}** indicates that the trading volume deviates significantly 
    from the normal value (it is **{spike_threshold:.1f} standard deviations** above the 20-day moving average). 
    This points to extraordinary trading activity.
    """)
else:
    st.error("Could not load data. Check API limits (max 5 requests/min) and keys.")
