import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

# --- CONFIGURATION ---
STOCKS = {
    "Apple": "AAPL",
    "NVIDIA": "NVDA",
    "Microsoft": "MSFT",
    "J.P. Morgan": "JPM",
    "Goldman Sachs": "GS",
    "Bank of America": "BAC"
}

@st.cache_data(show_spinner="Loading local data...")
def get_stock_data(symbol):
    """Reads the CSV file created by the bot from the data folder."""
    file_path = f"data/stock_{symbol}.csv"

    if not os.path.exists(file_path):
        return None

    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        df = df.sort_index()
        if '4. close' in df.columns:
            df.rename(columns={"4. close": "close"}, inplace=True)
        return df[["close"]]
    except Exception:
        return None


def identify_phases(df_input, bull_threshold, bear_threshold):
    """Calculates market phases based on a 20-day rolling window and custom thresholds."""
    df = df_input.copy()
    df['rolling_max'] = df['close'].rolling(window=20, min_periods=1).max()
    df['rolling_min'] = df['close'].rolling(window=20, min_periods=1).min()

    bear_limit = -bear_threshold / 100
    bull_limit = bull_threshold / 100

    df['phase'] = np.select(
        [
            (df['close'] - df['rolling_max']) / df['rolling_max'] <= bear_limit,
            (df['close'] - df['rolling_min']) / df['rolling_min'] >= bull_limit
        ],
        ['Bear', 'Bull'],
        default='Neutral'
    )
    return df


def add_phase_shading(fig, df):
    """Adds colored background shading for each market phase as vrect shapes."""
    phase_colors = {
        "Bull": "rgba(0, 200, 100, 0.15)",
        "Bear": "rgba(220, 50, 50, 0.15)",
        "Neutral": "rgba(180, 180, 180, 0.07)"
    }

    # Group consecutive rows with the same phase into segments
    df = df.reset_index()
    df.columns = ['date'] + list(df.columns[1:])

    segments = []
    current_phase = df['phase'].iloc[0]
    start_date = df['date'].iloc[0]

    for i in range(1, len(df)):
        if df['phase'].iloc[i] != current_phase:
            segments.append((start_date, df['date'].iloc[i - 1], current_phase))
            current_phase = df['phase'].iloc[i]
            start_date = df['date'].iloc[i]
    segments.append((start_date, df['date'].iloc[-1], current_phase))

    for seg_start, seg_end, phase in segments:
        fig.add_vrect(
            x0=seg_start,
            x1=seg_end,
            fillcolor=phase_colors.get(phase, "rgba(0,0,0,0)"),
            opacity=1.0,
            layer="below",
            line_width=0,
        )

    return fig


# --- UI ---
render_page_header(
    "Market Phases",
    "How do Apple and NVIDIA stock prices react during periods of extreme market volatility (when the VIX index exceeds a threshold of 30)?",
)

# Sidebar controls
selected_stock = st.sidebar.selectbox("Select Asset:", list(STOCKS.keys()))

st.sidebar.markdown("---")
st.sidebar.subheader("Phase Thresholds")

bull_threshold = st.sidebar.slider(
    "🟢 Bull Market Threshold (%)",
    min_value=1,
    max_value=20,
    value=20,
    step=1,
    help="Minimum rise from rolling 20-day low to qualify as a Bull phase."
)

bear_threshold = st.sidebar.slider(
    "🔴 Bear Market Threshold (%)",
    min_value=1,
    max_value=20,
    value=20,
    step=1,
    help="Minimum drop from rolling 20-day high to qualify as a Bear phase."
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**Current Settings:**\n"
    f"- 🟢 Bull: +{bull_threshold}% from 20d low\n"
    f"- 🔴 Bear: -{bear_threshold}% from 20d high"
)

# Load and process data
df_raw = get_stock_data(STOCKS[selected_stock])

if df_raw is not None:
    df_view = identify_phases(df_raw, bull_threshold, bear_threshold)

    # Chart
    fig = go.Figure()

    # Add phase shading first (below price line)
    fig = add_phase_shading(fig, df_view)

    # Price line
    fig.add_trace(go.Scatter(
        x=df_view.index,
        y=df_view['close'],
        name='Price',
        line=dict(color='#E8E8E8', width=1.8),
        hovertemplate='%{x|%d.%m.%Y}<br>$%{y:.2f}<extra></extra>'
    ))

    # Add invisible legend traces for phase colors
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(size=10, color='rgba(0, 200, 100, 0.6)', symbol='square'),
        name=f'Bull (≥+{bull_threshold}%)'
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(size=10, color='rgba(220, 50, 50, 0.6)', symbol='square'),
        name=f'Bear (≤-{bear_threshold}%)'
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(size=10, color='rgba(180, 180, 180, 0.4)', symbol='square'),
        name='Neutral'
    ))

    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        margin=dict(t=60)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.download_button(
        label="📥 Graph als PDF herunterladen",
        data=fig_to_pdf_bytes(fig),
        file_name="marktphasen.pdf",
        mime="application/pdf"
    )

    # Phase Distribution
    st.subheader("Market Phase Distribution")
    counts = df_view['phase'].value_counts()
    percentages = (counts / len(df_view) * 100).round(2)

    dist_df = pd.DataFrame({
        "Days": counts,
        "Share (%)": percentages
    })
    st.table(dist_df)

    # --- Interpretation ---
    st.markdown("---")
    st.subheader("Interpretation and Insights")

    bull_pct = percentages.get("Bull", 0)
    bear_pct = percentages.get("Bear", 0)
    neutral_pct = percentages.get("Neutral", 0)

    st.markdown(f"""
### Analysis Results

**1. Market Regime Overview**
- The asset spent **{bull_pct}%** of the time in a Bull phase.
- **{bear_pct}%** in a Bear phase.
- **{neutral_pct}%** in a neutral phase.

This provides a direct understanding of the dominant market environment during the observed period.

---

**2. Trend Strength**
- A high Bull share indicates strong upward momentum.
- A high Bear share points to longer corrections or downturns.
- A high Neutral share signals sideways movements or consolidations.

---

**3. Volatility and Behavior**
- Stocks like NVIDIA often switch phases more frequently due to higher volatility.
- Established blue-chip titles often show more stable and prolonged trends.

---

**4. Strategic Implications**
- **Bull Phases:** Trend-following strategies are often advantageous.
- **Bear Phases:** Risk management and defensive positioning are crucial.
- **Neutral Phases:** Range trading or waiting for breakouts is often more effective.

---

**5. Methodological Note**
This model uses a 20-day rolling window with your custom thresholds:
- {bear_threshold}% drop from the recent high → Bear 🔴
- {bull_threshold}% rise from the recent low → Bull 🟢

This is a simplified but widely used definition of market cycles in financial analysis.
""")

    st.caption("Methodology: Rolling 20-day window analysis of price movements.")

else:
    st.error("Data could not be loaded. Please ensure that the CSV files are present in the 'data' folder.")
