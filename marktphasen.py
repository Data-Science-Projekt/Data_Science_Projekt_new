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

STOCK_COLORS = {
    "Apple": "#1f77b4",
    "NVIDIA": "#2ca02c",
    "Microsoft": "#ff7f0e",
    "J.P. Morgan": "#9467bd",
    "Goldman Sachs": "#d62728",
    "Bank of America": "#8c564b"
}

@st.cache_data(show_spinner="Loading local data...")
def get_stock_data(symbol):
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
    phase_colors = {
        "Bull": "rgba(0, 200, 100, 0.15)",
        "Bear": "rgba(220, 50, 50, 0.15)",
        "Neutral": "rgba(180, 180, 180, 0.07)"
    }

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


def build_stock_chart(stock, df_view, bull_threshold, bear_threshold):
    fig = go.Figure()
    fig = add_phase_shading(fig, df_view)

    fig.add_trace(go.Scatter(
        x=df_view.index,
        y=df_view['close'],
        name='Price',
        mode="lines",
        line=dict(color=STOCK_COLORS[stock], width=2.5),
        hovertemplate='%{x|%d.%m.%Y}<br>$%{y:.2f}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(size=12, color='rgba(0, 200, 100, 0.6)', symbol='square'),
        name=f'Bull (≥+{bull_threshold}%)'
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(size=12, color='rgba(220, 50, 50, 0.6)', symbol='square'),
        name=f'Bear (≤-{bear_threshold}%)'
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(size=12, color='rgba(180, 180, 180, 0.4)', symbol='square'),
        name='Neutral'
    ))

    fig.update_layout(
        title=dict(text=f"{stock}", font=dict(size=18, color="#718096")),
        template="plotly_white",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        font=dict(color="#718096", size=14),
        xaxis=dict(
            tickfont=dict(color="#718096", size=13),
            title_font=dict(color="#718096", size=15),
            gridcolor="#e2e8f0",
            linecolor="#cbd5e0",
        ),
        yaxis=dict(
            tickfont=dict(color="#718096", size=13),
            title_font=dict(color="#718096", size=15),
            gridcolor="#e2e8f0",
            linecolor="#cbd5e0",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#718096", size=13)
        ),
        hovermode="x unified",
        margin=dict(t=60),
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# --- UI ---
render_page_header(
    "Market Phases",
    "How does the correlation between selected technology stocks (Apple, Microsoft, NVIDIA) and selected financial stocks (J.P. Morgan, Goldman Sachs, Bank of America) change during stable market periods compared to crisis periods (bear markets)?",
)

# Sidebar controls
selected_stocks = st.sidebar.multiselect(
    "Select Assets:",
    list(STOCKS.keys()),
    default=["Apple", "NVIDIA"],
    key="selected_stocks_multiselect"
)

if not selected_stocks:
    st.warning("Please select at least one asset.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.subheader("Phase Thresholds")

bull_threshold = st.sidebar.slider(
    "🟢 Bull Market Threshold (%)",
    min_value=1, max_value=20, value=20, step=1,
    help="Minimum rise from rolling 20-day low to qualify as a Bull phase."
)

bear_threshold = st.sidebar.slider(
    "🔴 Bear Market Threshold (%)",
    min_value=1, max_value=20, value=20, step=1,
    help="Minimum drop from rolling 20-day high to qualify as a Bear phase."
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**Current Settings:**\n"
    f"- 🟢 Bull: +{bull_threshold}% from 20d low\n"
    f"- 🔴 Bear: -{bear_threshold}% from 20d high"
)

# --- LOAD DATA ---
all_data = {}
for stock in selected_stocks:
    df_raw = get_stock_data(STOCKS[stock])
    if df_raw is not None:
        all_data[stock] = identify_phases(df_raw, bull_threshold, bear_threshold)

if not all_data:
    st.error("No data could be loaded.")
    st.stop()

# --- CHARTS JEWEILS ZWEI NEBENEINANDER ---
stocks_list = list(all_data.items())

for i in range(0, len(stocks_list), 2):
    cols = st.columns(2)

    for j, col in enumerate(cols):
        if i + j >= len(stocks_list):
            break

        stock, df_view = stocks_list[i + j]

        with col:
            st.subheader(f"📈 {stock}")

            fig = build_stock_chart(stock, df_view, bull_threshold, bear_threshold)
            st.plotly_chart(fig, use_container_width=True)

            st.download_button(
                label=f"📥 {stock} als PNG",
                data=fig_to_pdf_bytes(fig),
                file_name=f"marktphasen_{stock.replace(' ', '_')}.png",
                mime="image/png",
                key=f"download_marktphasen_{stock}"
            )

            counts = df_view['phase'].value_counts()
            percentages = (counts / len(df_view) * 100).round(2)
            dist_df = pd.DataFrame({"Days": counts, "Share (%)": percentages})
            st.markdown(f"**Phase Distribution – {stock}**")
            st.table(dist_df)

    st.markdown("---")

# --- GEMEINSAME INTERPRETATION ---
st.subheader("Interpretation and Insights")
st.markdown(f"""
**1. Thresholds applied to all assets:**
- 🟢 Bull: +{bull_threshold}% rise from 20-day low
- 🔴 Bear: -{bear_threshold}% drop from 20-day high

**2. Volatility and Behavior**
- Stocks like NVIDIA often switch phases more frequently due to higher volatility.
- Established blue-chip titles often show more stable and prolonged trends.

**3. Strategic Implications**
- **Bull Phases:** Trend-following strategies are often advantageous.
- **Bear Phases:** Risk management and defensive positioning are crucial.
- **Neutral Phases:** Range trading or waiting for breakouts is often more effective.
""")

st.caption("Methodology: Rolling 20-day window analysis of price movements.")