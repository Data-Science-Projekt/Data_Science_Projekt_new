import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

# --- CONFIGURATION ---
AV_API_KEY = "REMOVED_AV_KEY".strip()
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA", "S&P 500": "SPY"}

st.set_page_config(page_title="Market Phases Analysis", layout="wide")


# --- FUNCTION: LOAD DATA (FULL = 20 years) ---
@st.cache_data(show_spinner="Fetching stock data...")
def get_stock_data(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url)
        data = r.json()

        if "Note" in data:
            st.error("API Rate Limit reached. Please wait 60 seconds.")
            return None

        if "Time Series (Daily)" in data:
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float).sort_index()
            df.rename(columns={"4. close": "close"}, inplace=True)
            return df[["close"]]
        else:
            st.warning("No data found. Check API key or symbol.")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None


# --- FUNCTION: IDENTIFY MARKET PHASES ---
def identify_phases(df, bear_threshold=-0.20, bull_threshold=0.20, window=60):
    """
    Identifies Bull and Bear market phases based on rolling peak/trough method.
    - Bear: price drops >= 20% from rolling peak
    - Bull: price rises >= 20% from rolling trough
    """
    df = df.copy()
    df['rolling_max'] = df['close'].rolling(window=window, min_periods=1).max()
    df['rolling_min'] = df['close'].rolling(window=window, min_periods=1).min()
    df['drawdown'] = (df['close'] - df['rolling_max']) / df['rolling_max']
    df['rally'] = (df['close'] - df['rolling_min']) / df['rolling_min']

    df['phase'] = 'Neutral'
    df.loc[df['drawdown'] <= bear_threshold, 'phase'] = 'Bear'
    df.loc[df['rally'] >= bull_threshold, 'phase'] = 'Bull'

    return df


# --- FUNCTION: BUILD CHART ---
def build_chart(df, stock_name):
    fig = go.Figure()

    # Price line
    fig.add_trace(go.Scatter(
        x=df.index, y=df['close'],
        mode='lines',
        name=f'{stock_name} Price',
        line=dict(color='white', width=1.5),
        zorder=2
    ))

    # Highlight Bull phases
    bull_mask = df['phase'] == 'Bull'
    bear_mask = df['phase'] == 'Bear'

    def add_phase_shading(fig, df, mask, color, name):
        in_phase = False
        start = None
        for i, (idx, val) in enumerate(mask.items()):
            if val and not in_phase:
                start = idx
                in_phase = True
            elif not val and in_phase:
                fig.add_vrect(
                    x0=start, x1=idx,
                    fillcolor=color, opacity=0.25,
                    layer="below", line_width=0,
                    annotation_text=name if (df.index.get_loc(idx) - df.index.get_loc(start)) > 30 else "",
                    annotation_position="top left",
                    annotation_font_size=10,
                    annotation_font_color=color
                )
                in_phase = False
        if in_phase:
            fig.add_vrect(
                x0=start, x1=df.index[-1],
                fillcolor=color, opacity=0.25,
                layer="below", line_width=0
            )

    add_phase_shading(fig, df, bull_mask, "green", "Bull")
    add_phase_shading(fig, df, bear_mask, "red", "Bear")

    # Moving averages
    df['MA50'] = df['close'].rolling(50).mean()
    df['MA200'] = df['close'].rolling(200).mean()

    fig.add_trace(go.Scatter(
        x=df.index, y=df['MA50'],
        mode='lines', name='50-Day MA',
        line=dict(color='orange', width=1, dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df['MA200'],
        mode='lines', name='200-Day MA',
        line=dict(color='cyan', width=1, dash='dot')
    ))

    fig.update_layout(
        title=f"Market Phases: {stock_name}  🟢 Bull  🔴 Bear",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        height=600,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        hovermode="x unified"
    )

    return fig, df


# --- UI ---
st.title("Market Phase Analysis")
st.markdown("**Research Question:** Can market phases (bull and bear markets) be systematically identified and what are their characteristic features?")

with st.sidebar:
    st.header("Settings")
    selected_stock = st.selectbox("Select stock:", list(STOCKS.keys()))
    bear_threshold = st.slider("Bear Market Threshold (%)", min_value=-40, max_value=-5, value=-20, step=5)
    bull_threshold = st.slider("Bull Market Threshold (%)", min_value=5, max_value=50, value=20, step=5)
    window = st.slider("Rolling Window (days)", min_value=20, max_value=120, value=60, step=10)
    st.divider()
    st.info("Bear: price falls ≥ threshold from rolling peak\nBull: price rises ≥ threshold from rolling trough")

# Load & process
df_raw = get_stock_data(STOCKS[selected_stock])

if df_raw is not None:
    df_phases = identify_phases(df_raw, bear_threshold / 100, bull_threshold / 100, window)
    fig, df_phases = build_chart(df_phases, selected_stock)

    st.plotly_chart(fig, use_container_width=True)

    # Phase statistics
    st.subheader("Phase Statistics")
    phase_counts = df_phases['phase'].value_counts()
    total = len(df_phases)

    c1, c2, c3 = st.columns(3)
    c1.metric("🟢 Bull Market Days", phase_counts.get('Bull', 0),
              f"{phase_counts.get('Bull', 0) / total * 100:.1f}% of time")
    c2.metric("🔴 Bear Market Days", phase_counts.get('Bear', 0),
              f"{phase_counts.get('Bear', 0) / total * 100:.1f}% of time")
    c3.metric("⚪ Neutral Days", phase_counts.get('Neutral', 0),
              f"{phase_counts.get('Neutral', 0) / total * 100:.1f}% of time")

    # Characteristic features per phase
    st.subheader("Characteristic Features per Phase")
    for phase, color in [("Bull", "🟢"), ("Bear", "🔴"), ("Neutral", "⚪")]:
        subset = df_phases[df_phases['phase'] == phase]
        if len(subset) > 1:
            returns = subset['close'].pct_change().dropna()
            avg_return = returns.mean() * 100
            volatility = returns.std() * 100
            with st.expander(f"{color} {phase} Market — {len(subset)} days"):
                col1, col2 = st.columns(2)
                col1.metric("Avg. Daily Return", f"{avg_return:.3f}%")
                col2.metric("Daily Volatility", f"{volatility:.3f}%")

    st.subheader("Analysis Summary")
    bull_pct = phase_counts.get('Bull', 0) / total * 100
    bear_pct = phase_counts.get('Bear', 0) / total * 100
    st.write(
        f"Based on the rolling window method, **{selected_stock}** spent **{bull_pct:.1f}%** of trading days in a bull market "
        f"and **{bear_pct:.1f}%** in a bear market. "
        f"The 50-day and 200-day moving averages serve as additional confirmation signals — "
        f"a **Golden Cross** (50MA crossing above 200MA) typically marks the start of a bull phase, "
        f"while a **Death Cross** signals a bear phase."
    )
