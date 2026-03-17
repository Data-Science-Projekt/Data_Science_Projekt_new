import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- CONFIGURATION ---
# No API keys required as we are reading data locally.
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
        # Read CSV (Index is the date)
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        # Sort so the oldest date is at the top (crucial for rolling windows)
        df = df.sort_index()
        # Rename Alpha Vantage column '4. close' to 'close'
        if '4. close' in df.columns:
            df.rename(columns={"4. close": "close"}, inplace=True)
        return df[["close"]]
    except Exception:
        return None

def identify_phases(df_input):
    """Calculates market phases based on a 20-day rolling window."""
    df = df_input.copy()
    # Rolling Max/Min for phase logic
    df['rolling_max'] = df['close'].rolling(window=20, min_periods=1).max()
    df['rolling_min'] = df['close'].rolling(window=20, min_periods=1).min()

    # Logic: -20% from high = Bear / +20% from low = Bull
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
st.write("Identification of Bull, Bear, and Neutral phases using a rolling window approach.")

selected_stock = st.sidebar.selectbox("Select Asset:", list(STOCKS.keys()))
df_raw = get_stock_data(STOCKS[selected_stock])

if df_raw is not None:
    df_view = identify_phases(df_raw)

    # Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_view.index, y=df_view['close'], name='Price'))
    fig.update_layout(
        template="plotly_dark", 
        xaxis_title="Date", 
        yaxis_title="Price ($)"
    )
    st.plotly_chart(fig, use_container_width=True)

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
This model uses a 20-day window:
- 20% drop from the recent high -> Bear
- 20% rise from the recent low -> Bull

This is a simplified but widely used definition of market cycles in financial analysis.
""")

    st.caption("Methodology: Rolling 20-day window analysis of price movements.")

else:
    st.error("Data could not be loaded. Please ensure that the CSV files are present in the 'data' folder.")
