import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import os

# --- CONFIGURATION ---
# Nutze .get() um Abstuerze bei fehlenden Keys zu verhindern
AV_API_KEY = st.secrets.get("AV_API_KEY", "")
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA", "S&P 500": "SPY"}

# Hinweis: st.set_page_config wurde entfernt, da es zentral in app.py steht.

# --- FUNCTION: LOAD DATA ---
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
@st.cache_data
def identify_phases(close_values, index_values, bear_threshold=-0.20, bull_threshold=0.20):
    df = pd.DataFrame({'close': close_values}, index=pd.to_datetime(index_values))
    window = 20
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

    fig.add_trace(go.Scatter(
        x=df.index, y=df['close'],
        mode='lines',
        name=f'{stock_name} Price',
        line=dict(color='white', width=1.5)
    ))

    bull_mask = df['phase'] == 'Bull'
    bear_mask = df['phase'] == 'Bear'

    def add_phase_shading(fig, df, mask, color, name):
        in_phase = False
        start = None
        for idx, val in mask.items():
            if val and not in_phase:
                start = idx
                in_phase = True
            elif not val and in_phase:
                fig.add_vrect(
                    x0=start, x1=idx,
                    fillcolor=color, opacity=0.25,
                    layer="below", line_width=0,
                    annotation_text=name if (df.index.get_loc(idx) - df.index.get_loc(start)) > 5 else "",
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

    df = df.copy()
    df['MA50'] = df['close'].rolling(50).mean()
    fig.add_trace(go.Scatter(
        x=df.index, y=df['MA50'],
        mode='lines', name='50-Day MA',
        line=dict(color='orange', width=1, dash='dot')
    ))

    fig.update_layout(
        title=f"Market Phases: {stock_name} (Green: Bull, Red: Bear)",
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
st.markdown("Research Question: Can market phases (bull and bear markets) be systematically identified and what are their characteristic features?")

with st.sidebar:
    st.header("Settings")
    selected_stock = st.selectbox("Select stock:", list(STOCKS.keys()))
    bear_threshold = st.slider("Bear Market Threshold (%)", min_value=-40, max_value=-5, value=-20, step=5)
    bull_threshold = st.slider("Bull Market Threshold (%)", min_value=5, max_value=50, value=20, step=5)
    st.divider()
    st.info("Bear: price falls >= threshold from rolling peak\nBull: price rises >= threshold from rolling trough")

# Load & process
df_raw = get_stock_data(STOCKS[selected_stock])

if df_raw is not None:
    df_phases = identify_phases(
        df_raw['close'].tolist(),
        df_raw.index.tolist(),
        bear_threshold / 100,
        bull_threshold / 100
    )

    total_days = len(df_phases)
    days_to_show = st.slider("Show last N days:", min_value=10, max_value=total_days, value=total_days, step=5)
    df_view = df_phases.tail(days_to_show)

    fig, df_view = build_chart(df_view, selected_stock)
    # Nutzt width='stretch' statt use_container_width
    st.plotly_chart(fig, width='stretch')

    # Phase statistics
    st.subheader("Phase Statistics")
    phase_counts = df_view['phase'].value_counts()
    total = len(df_view)

    c1, c2, c3 = st.columns(3)
    c1.metric("Bull Market Days", phase_counts.get('Bull', 0),
              f"{phase_counts.get('Bull', 0) / total * 100:.1f}% of time")
    c2.metric("Bear Market Days", phase_counts.get('Bear', 0),
              f"{phase_counts.get('Bear', 0) / total * 100:.1f}% of time")
    c3.metric("Neutral Days", phase_counts.get('Neutral', 0),
              f"{phase_counts.get('Neutral', 0) / total * 100:.1f}% of time")

    # Transition Probabilities
    st.subheader("Transition Probabilities")
    phases = df_view['phase'].values
    transitions = {'Bull': {'Bull': 0, 'Bear': 0, 'Neutral': 0},
                   'Bear': {'Bull': 0, 'Bear': 0, 'Neutral': 0},
                   'Neutral': {'Bull': 0, 'Bear': 0, 'Neutral': 0}}

    for i in range(len(phases) - 1):
        transitions[phases[i]][phases[i + 1]] += 1

    rows = []
    for from_phase in ['Bull', 'Bear', 'Neutral']:
        total_from = sum(transitions[from_phase].values())
        row = {"From / To": from_phase}
        for to_phase in ['Bull', 'Bear', 'Neutral']:
            prob = transitions[from_phase][to_phase] / total_from * 100 if total_from > 0 else 0
            row[to_phase] = f"{prob:.1f}%"
        rows.append(row)

    trans_df = pd.DataFrame(rows).set_index("From / To")
    st.dataframe(trans_df, width='stretch')

    st.subheader("Analysis Summary")
    st.write(
        f"Based on the rolling window method, {selected_stock} spent {phase_counts.get('Bull', 0) / total * 100:.1f}% "
        f"of trading days in a bull market and {phase_counts.get('Bear', 0) / total * 100:.1f}% in a bear market."
    )
