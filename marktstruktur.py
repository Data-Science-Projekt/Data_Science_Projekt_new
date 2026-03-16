import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

# --- CONFIGURATION ---
AV_API_KEY = st.secrets["AV_API_KEY"]
FRED_API_KEY = st.secrets["FRED_API_KEY"]
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}



# --- DATA FETCHING ---
@st.cache_data(show_spinner="Loading Stock Data...")
def get_stock_data(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url).json()
        if "Time Series (Daily)" in r:
            df = pd.DataFrame.from_dict(r['Time Series (Daily)'], orient='index').astype(float).sort_index()
            df.index = pd.to_datetime(df.index)
            # Log-Returns für genauere Statistik
            df['Returns'] = np.log(df['4. close'] / df['4. close'].shift(1))
            return df[['4. close', 'Returns']].dropna()
    except:
        return None
    return None


@st.cache_data(show_spinner="Loading VIX Data...")
def get_vix_data():
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=VIXCLS&api_key={FRED_API_KEY}&file_type=json"
    try:
        r = requests.get(url).json()
        df = pd.DataFrame(r['observations'])
        df['date'] = pd.to_datetime(df['date'])
        df['VIX'] = pd.to_numeric(df['value'], errors='coerce')
        return df.set_index('date')[['VIX']].dropna()
    except:
        return None


# --- UI ---
st.title("Market Reaction: Stocks vs. VIX")
st.markdown("Analysis of how stock prices react during periods of market fear (VIX).")

with st.sidebar:
    st.header("Settings")
    selected_stock = st.selectbox("Select Stock:", list(STOCKS.keys()))
    # Slider auf 15-20 stellen, um Flächen in den letzten 100 Tagen zu sehen
    vix_threshold = st.slider("VIX Panic Threshold:", 10.0, 40.0, 20.0, step=0.5)
    st.info("The red shaded areas represent days where VIX > Threshold.")

# Process Data
df_vix = get_vix_data()
df_stock = get_stock_data(STOCKS[selected_stock])

if df_stock is not None and df_vix is not None:
    # Daten zusammenführen
    combined = df_stock.join(df_vix, how='inner')

    # Markierung für Panik-Tage
    combined['Panic'] = combined['VIX'] > vix_threshold
    panic_days = combined[combined['Panic']]

    # --- PLOT ---
    fig = go.Figure()

    # Aktienkurs (Y1)
    fig.add_trace(go.Scatter(
        x=combined.index, y=combined['4. close'],
        name=f"{selected_stock} Price", yaxis="y1",
        line=dict(color='#1f77b4', width=2)
    ))

    # VIX (Y2)
    fig.add_trace(go.Scatter(
        x=combined.index, y=combined['VIX'],
        name="VIX Index", yaxis="y2",
        line=dict(color='gray', dash='dot', width=1),
        opacity=0.5
    ))

    # Rote Bereiche zeichnen (mit 1 Tag Breite)
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
        title=f"{selected_stock} Response to Market Volatility (Threshold: {vix_threshold})",
        xaxis_title="Date",
        yaxis=dict(title="Stock Price ($)", side="left"),
        yaxis2=dict(title="VIX Index", overlaying="y", side="right", range=[0, 50]),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- STATISTICS ---
    st.subheader("Statistical Impact Analysis")

    normal_data = combined[~combined['Panic']]
    panic_data = combined[combined['Panic']]

    col1, col2, col3 = st.columns(3)

    # Normaler Move
    if not normal_data.empty:
        normal_move = normal_data['Returns'].mean()
        col1.metric("Avg. Return (Normal)", f"{normal_move:.2%}")

    # Panik Move
    if not panic_data.empty:
        panic_move = panic_data['Returns'].mean()
        col2.metric(f"Avg. Return (VIX > {vix_threshold})", f"{panic_move:.2%}",
                    delta=f"{(panic_move - normal_move):.2%}" if not normal_data.empty else None,
                    delta_color="inverse")
        col3.metric("Days in Panic State", len(panic_data))
    else:
        col2.metric(f"Avg. Return (VIX > {vix_threshold})", "No Data")
        st.warning(f"No days found where VIX was above {vix_threshold}. Try lowering the slider!")

    # Interpretation
    st.divider()
    st.markdown(f"""
    **How to read this chart:**
    * **Blue Line:** The closing price of {selected_stock}.
    * **Gray Dotted Line:** The VIX Index (Fear Gauge).
    * **Red Shaded Areas:** Times of market stress. If the blue line drops sharply inside or immediately after these red zones, the stock is highly sensitive to market fear.
    """)
