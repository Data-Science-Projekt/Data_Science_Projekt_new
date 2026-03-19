import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}

CHART_STYLE = dict(
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
        font=dict(color="#718096", size=13)
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)

# --- DATA LOADING ---
@st.cache_data(show_spinner="Loading stock data...")
def get_stock_data(symbol):
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True).sort_index()
        df['Returns'] = np.log(df['4. close'] / df['4. close'].shift(1))
        return df[['4. close', 'Returns']].dropna()
    except Exception:
        return None

@st.cache_data(show_spinner="Loading VIX data...")
def get_vix_data():
    file_path = "data/macro_vix.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])
        df['VIX'] = pd.to_numeric(df['value'], errors='coerce')
        return df.set_index('date')[['VIX']].dropna()
    except Exception:
        return None

# --- UI ---
render_page_header(
    "Market Structure",
    "How do Apple and NVIDIA stock prices react during periods of extreme market volatility (when the VIX index exceeds a threshold of 30)?",
)

st.info("⬅️ Use the **sidebar** to select a stock and adjust the VIX panic threshold.")

with st.sidebar:
    st.header("Settings")
    selected_stock = st.selectbox("Select Stock:", list(STOCKS.keys()))
    vix_threshold = st.sidebar.slider("VIX Panic Threshold:", 10.0, 40.0, 20.0, step=0.5)
    st.info("The red shaded areas represent days when the VIX > threshold.")

# Process data
df_vix = get_vix_data()
df_stock = get_stock_data(STOCKS[selected_stock])

if df_stock is not None and df_vix is not None:
    combined = df_stock.join(df_vix, how='inner')
    combined['Panic'] = combined['VIX'] > vix_threshold
    panic_days = combined[combined['Panic']]

    # --- PLOT ---
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=combined.index, y=combined['4. close'],
        name=f"{selected_stock} Price", yaxis="y1",
        line=dict(color='#1f77b4', width=4)
    ))

    fig.add_trace(go.Scatter(
        x=combined.index, y=combined['VIX'],
        name="VIX Index", yaxis="y2",
        line=dict(color='purple', dash='dot', width=4),
        opacity=0.5
    ))

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
        title=dict(
            text=f"{selected_stock} Reaction to Market Volatility (Threshold: {vix_threshold})",
            font=dict(color="#718096", size=18)
        ),
        xaxis_title="Date",
        yaxis=dict(
            title="Stock Price ($)",
            side="left",
            tickfont=dict(color="#718096", size=13),
            title_font=dict(color="#718096", size=15),
            gridcolor="#e2e8f0",
            linecolor="#cbd5e0",
        ),
        yaxis2=dict(
            title="VIX Index",
            overlaying="y",
            side="right",
            range=[0, 50],
            tickfont=dict(color="#718096", size=13),
            title_font=dict(color="#718096", size=15),
            gridcolor="#e2e8f0",
            linecolor="#cbd5e0",
        ),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#718096", size=13)
        ),
        font=dict(color="#718096", size=14),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.download_button(
        label="📥 Graph als PNG herunterladen",
        data=fig_to_pdf_bytes(fig),
        file_name="marktstruktur.png",
        mime="image/png",
        key="download_marktstruktur"
    )

    # --- STATISTICS ---
    st.subheader("Statistical Impact")

    normal_data = combined[~combined['Panic']]
    panic_data = combined[combined['Panic']]

    col1, col2, col3 = st.columns(3)

    normal_move = 0
    if not normal_data.empty:
        normal_move = normal_data['Returns'].mean()
        col1.metric("Avg. Return (Normal)", f"{normal_move:.2%}")

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

    st.markdown("""
### What Does This Analysis Show?

This page examines how Apple and NVIDIA stock prices behave during periods of elevated market volatility, measured by the VIX index.

The VIX is often referred to as the fear index - when it rises above a certain threshold, it indicates increased uncertainty and stress in financial markets. In the charts above, these high-volatility periods are highlighted in red.

A key feature of this analysis is the interactive VIX threshold slider, which allows you to define what level of volatility should be considered a panic state. By adjusting this threshold, you can explore how stock behavior changes under different levels of market stress.

### Method

We use historical daily data for both stocks and the VIX index.

The VIX panic threshold (controlled by the slider) determines when the market is classified as being in a high-volatility state.

All days where the VIX exceeds this threshold are marked as panic periods and highlighted in red.

We then compare:

- Average returns during normal conditions
- Average returns during high-volatility periods

By adjusting the threshold, you can analyze how stock performance responds to mild vs. extreme market stress.

### Analysis and Interpretation

The results show a clear difference in stock behavior between normal and high-volatility environments.

During normal market conditions, both Apple and NVIDIA tend to generate stable or slightly positive returns. However, during periods of elevated volatility, returns typically decline.

Apple shows a moderate decrease in performance during high-volatility periods, indicating some sensitivity to market stress but relatively stable behavior overall.

NVIDIA, in contrast, exhibits a stronger negative reaction. Its returns tend to decrease more significantly when volatility increases, suggesting a higher sensitivity to changes in market sentiment.

The extent of these effects depends on the selected threshold:

- A lower threshold captures more frequent, moderate volatility periods
- A higher threshold isolates fewer but more extreme market stress events

This allows for a more nuanced analysis of how each stock behaves under different market conditions.

### Key Insights

- Market Stress Impact: Both stocks tend to perform worse during periods of elevated volatility.
- Threshold Sensitivity: The definition of a panic state matters - changing the VIX threshold can significantly affect the results and interpretation.
- Stronger Reaction of NVIDIA: NVIDIA generally reacts more strongly to volatility spikes, showing larger performance declines.
- Stability of Apple: Apple tends to be more resilient, with smaller changes in performance during stressful market periods.

### Why does this matter?

Financial markets do not react the same way to all levels of volatility.

By adjusting the VIX threshold, investors can:

- distinguish between normal fluctuations and true crisis periods
- better understand how assets behave under different stress levels
- make more informed decisions about diversification and risk exposure

In simple terms:
The definition of market stress is flexible - and different stocks react differently depending on how severe that stress is.
""")

    st.markdown(
        """
        <section class="research-header">
            <p class="research-header__eyebrow">Answer to the Research Question</p>
            <p class="research-header__question">
                Both Apple and NVIDIA show weaker performance during periods of elevated market volatility, with the effect becoming more pronounced as the VIX threshold increases. NVIDIA reacts more strongly to these conditions, indicating higher sensitivity to market stress, while Apple remains comparatively more stable.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Data sources: Alpha Vantage (Stock Prices) and FRED (CBOE Volatility Index - VIX).")
else:
    st.info("Please wait while the local data is being loaded.")