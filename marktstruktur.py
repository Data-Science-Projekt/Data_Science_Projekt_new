import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}

# --- DATA LOADING ---
@st.cache_data(show_spinner="Loading stock data...")
def get_stock_data(symbol):
    """Reads stock data from the local CSV file."""
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path):
        return None
    try:
        # Read and format index as date
        df = pd.read_csv(file_path, index_col=0, parse_dates=True).sort_index()
        # Calculate log returns for accurate statistical comparison
        df['Returns'] = np.log(df['4. close'] / df['4. close'].shift(1))
        # Keep '4. close' column for plotting
        return df[['4. close', 'Returns']].dropna()
    except Exception:
        return None

@st.cache_data(show_spinner="Loading VIX data...")
def get_vix_data():
    """Reads VIX data from local macro_vix.csv."""
    file_path = "data/macro_vix.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        # In FRED CSVs, the column is often lowercase ('date')
        df['date'] = pd.to_datetime(df['date'])
        # Convert VIX values to numerical format (handles dots/errors as NaN)
        df['VIX'] = pd.to_numeric(df['value'], errors='coerce')
        return df.set_index('date')[['VIX']].dropna()
    except Exception:
        return None

# --- UI ---
render_page_header(
    "Market Structure",
    "How do Apple and NVIDIA stock prices react during periods of extreme market volatility (when the VIX index exceeds a threshold of 30)?",
)

with st.sidebar:
    st.header("Settings")
    selected_stock = st.selectbox("Select Stock:", list(STOCKS.keys()))
    # Threshold for panic zones (VIX > threshold)
    vix_threshold = st.sidebar.slider("VIX Panic Threshold:", 10.0, 40.0, 20.0, step=0.5)
    st.info("The red shaded areas represent days when the VIX > threshold.")

# Process data
df_vix = get_vix_data()
df_stock = get_stock_data(STOCKS[selected_stock])

if df_stock is not None and df_vix is not None:
    # Merge data (Inner join combines only days existing in both datasets)
    combined = df_stock.join(df_vix, how='inner')

    # Mark panic days
    combined['Panic'] = combined['VIX'] > vix_threshold
    panic_days = combined[combined['Panic']]

    # --- PLOT ---
    fig = go.Figure()

    # Stock Price (Y1 - Left)
    fig.add_trace(go.Scatter(
        x=combined.index, y=combined['4. close'],
        name=f"{selected_stock} Price", yaxis="y1",
        line=dict(color='#1f77b4', width=2)
    ))

    # VIX (Y2 - Right)
    fig.add_trace(go.Scatter(
        x=combined.index, y=combined['VIX'],
        name="VIX Index", yaxis="y2",
        line=dict(color='gray', dash='dot', width=1),
        opacity=0.5
    ))

    # Draw red panic zones (1-day width)
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
        title=f"{selected_stock} Reaction to Market Volatility (Threshold: {vix_threshold})",
        xaxis_title="Date",
        yaxis=dict(title="Stock Price ($)", side="left"),
        yaxis2=dict(title="VIX Index", overlaying="y", side="right", range=[0, 50]),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.download_button(
        label="📥 Graph als PNG herunterladen",
        data=fig_to_pdf_bytes(fig),
        file_name="marktphasen.png",
        mime="application/png"
    )

    # --- STATISTICS ---
    st.subheader("Statistical Impact")

    normal_data = combined[~combined['Panic']]
    panic_data = combined[combined['Panic']]

    col1, col2, col3 = st.columns(3)

    # Normal movement
    normal_move = 0
    if not normal_data.empty:
        normal_move = normal_data['Returns'].mean()
        col1.metric("Avg. Return (Normal)", f"{normal_move:.2%}")

    # Panic movement
    if not panic_data.empty:
        panic_move = panic_data['Returns'].mean()
        col2.metric(f"Return during VIX > {vix_threshold}", f"{panic_move:.2%}",
                    delta=f"{(panic_move - normal_move):.2%}" if not normal_data.empty else None,
                    delta_color="inverse")
        col3.metric("Days in Panic State", len(panic_data))
    else:
        col2.metric(f"Return during VIX > {vix_threshold}", "No data")
        st.warning(f"No days found where the VIX was above {vix_threshold}. Please lower the threshold!")

    # --- INTERPRETATION ---
    st.divider()
    st.subheader("Analysis and Interpretation")

    st.markdown(f"""
    **How to read this chart:**
    * **Blue Line:** The closing price of {selected_stock}.
    * **Gray Dotted Line:** The VIX Index, often referred to as the "fear gauge."
    * **Red Areas:** Time periods where volatility exceeded your threshold.

    ### Key Insights:

    * **Market Sensitivity:** High-beta stocks like NVIDIA often show a stronger negative correlation to the VIX. If the price drops sharply during VIX spikes (red zones), it indicates high vulnerability to systemic risks.

    * **Statistical Deviation:** The comparison between normal returns and panic returns shows the direct influence of market fear. Significantly negative returns during panic phases suggest that the asset is not perceived as a safe haven.

    * **Recovery Speed:** Observe the behavior immediately after a red zone ends. Fast recoveries suggest strong fundamentals, while prolonged declines may indicate a trend reversal.

    * **Threshold Significance:** A low value (e.g., VIX 15) captures general market noise, while a high value (e.g., VIX 30) isolates genuine crises or Black Swan events.
    """)

    st.caption("Data sources: Alpha Vantage (Stock Prices) and FRED (CBOE Volatility Index - VIX).")
else:
    st.info("Please wait while the local data is being loaded.")
