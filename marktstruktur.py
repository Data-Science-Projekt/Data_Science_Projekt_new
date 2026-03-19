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
    legend=dict(font=dict(color="#718096", size=13)),
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

st.info("Use the sidebar to select a stock and adjust the VIX panic threshold.")

with st.sidebar:
    st.header("Settings")
    selected_stock = st.selectbox("Select Stock:", list(STOCKS.keys()))
    vix_threshold = st.sidebar.slider("VIX Panic Threshold:", 10.0, 40.0, 20.0, step=0.5)
    st.info("The red shaded areas represent days when the VIX exceeds the threshold.")

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
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(color="#718096", size=13)
        ),
        font=dict(color="#718096", size=14),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.download_button(
        label="Graph als PNG herunterladen",
        data=fig_to_pdf_bytes(fig),
        file_name="marktstruktur.png",
        mime="image/png",
        key="download_marktstruktur"
    )

    # --- STATISTICS ---
    st.subheader("Statistical Impact")

    normal_data = combined[~combined['Panic']]
    panic_data  = combined[combined['Panic']]

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
        st.warning(f"No days found where the VIX was above {vix_threshold}. Please lower the threshold.")

    # --- INTERPRETATION ---
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
    .section-banner {
        display: flex; align-items: center; gap: 14px;
        padding: 14px 22px; border-radius: 10px;
        margin-bottom: 20px; margin-top: 24px;
    }
    .section-banner-blue   { background: linear-gradient(90deg, rgba(37,99,235,0.08), rgba(37,99,235,0.01)); border-left: 3px solid #2563eb; }
    .section-banner-green  { background: linear-gradient(90deg, rgba(22,163,74,0.08), rgba(22,163,74,0.01)); border-left: 3px solid #16a34a; }
    .section-banner-purple { background: linear-gradient(90deg, rgba(124,58,237,0.08), rgba(124,58,237,0.01)); border-left: 3px solid #7c3aed; }
    .section-banner-orange { background: linear-gradient(90deg, rgba(217,119,6,0.08), rgba(217,119,6,0.01)); border-left: 3px solid #d97706; }
    .section-title { font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700; margin: 0; }
    .info-box {
        background: rgba(37,99,235,0.04); border: 1px solid rgba(37,99,235,0.15);
        border-radius: 12px; padding: 24px 28px; margin-bottom: 16px;
        line-height: 1.75; font-size: 1.05rem;
    }
    .info-box .hl { color: #2563eb; font-weight: 600; }
    .step-card {
        background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.08);
        border-radius: 12px; padding: 18px 20px; margin-bottom: 12px;
        display: flex; gap: 16px; align-items: flex-start;
        transition: border-color 0.2s, transform 0.2s;
    }
    .step-card:hover { border-color: #2563eb; transform: translateX(3px); }
    .step-number {
        font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 800;
        color: #2563eb; opacity: 0.35; min-width: 32px; line-height: 1.3;
    }
    .step-title { font-family: 'Syne', sans-serif; font-size: 1.05rem; font-weight: 700; margin: 0 0 3px 0; }
    .step-desc  { font-size: 0.98rem; line-height: 1.55; margin: 0; opacity: 0.7; }
    .insight-card {
        background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.1);
        border-radius: 12px; padding: 22px 22px 20px; margin-bottom: 16px;
        transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
    }
    .insight-card:hover { border-color: #2563eb; transform: translateY(-2px); box-shadow: 0 4px 16px rgba(37,99,235,0.1); }
    .card-icon-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
    .card-icon {
        font-size: 1.4rem; width: 40px; height: 40px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 8px; flex-shrink: 0;
    }
    .icon-blue   { background: rgba(37,99,235,0.12); }
    .icon-green  { background: rgba(22,163,74,0.12); }
    .icon-orange { background: rgba(217,119,6,0.12); }
    .icon-purple { background: rgba(124,58,237,0.12); }
    .icon-red    { background: rgba(220,38,38,0.12); }
    .card-title { font-family: 'Syne', sans-serif; font-size: 1.08rem; font-weight: 700; margin: 0; }
    .card-body  { font-size: 1rem; line-height: 1.65; margin: 0; opacity: 0.75; }
    </style>
    """, unsafe_allow_html=True)

    # 01. What does this analysis show?
    st.markdown("""
    <div class="section-banner section-banner-blue">
        <p class="section-title">01. What Does This Analysis Show?</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="info-box">
        This page examines how <span class="hl">Apple</span> and <span class="hl">NVIDIA</span> stock
        prices behave during periods of elevated market volatility, measured by the
        <span class="hl">VIX index</span>. The VIX is often referred to as the fear index. When it rises
        above a certain threshold, it signals increased uncertainty and stress in financial markets.
        In the chart above, these high-volatility periods are highlighted in red.
        <br><br>
        A key feature of this analysis is the interactive <span class="hl">VIX threshold slider</span>,
        which allows you to define what level of volatility should be considered a panic state.
        By adjusting this threshold, you can explore how stock behavior changes under different
        levels of market stress.
    </div>
    """, unsafe_allow_html=True)

    # 02. Method
    st.markdown("""
    <div class="section-banner section-banner-purple">
        <p class="section-title">02. Method</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    .method-cols { display: flex; gap: 16px; margin-bottom: 16px; }
    .method-col {
        flex: 1; background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.08);
        border-radius: 12px; padding: 22px 20px;
        transition: border-color 0.2s, transform 0.2s;
    }
    .method-col:hover { border-color: #2563eb; transform: translateY(-2px); }
    .method-col-num {
        font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 800;
        color: #2563eb; opacity: 0.25; line-height: 1; margin-bottom: 10px;
    }
    .method-col-title {
        font-family: 'Syne', sans-serif; font-size: 1.0rem; font-weight: 700;
        margin: 0 0 8px 0;
    }
    .method-col-desc { font-size: 0.92rem; line-height: 1.6; margin: 0; opacity: 0.7; }
    </style>
    <div class="method-cols">
        <div class="method-col">
            <div class="method-col-num">01</div>
            <p class="method-col-title">Define the Panic Threshold</p>
            <p class="method-col-desc">The VIX panic threshold is set via the sidebar slider. All days where the VIX exceeds this value are classified as high-volatility periods and highlighted in red.</p>
        </div>
        <div class="method-col">
            <div class="method-col-num">02</div>
            <p class="method-col-title">Split into Normal and Panic Periods</p>
            <p class="method-col-desc">Daily returns are divided into two groups: normal market conditions (VIX below threshold) and panic state (VIX above threshold).</p>
        </div>
        <div class="method-col">
            <div class="method-col-num">03</div>
            <p class="method-col-title">Compare Average Returns</p>
            <p class="method-col-desc">Average log-returns are compared across both groups to quantify how much market stress affects the performance of each stock.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 03. Analysis and Interpretation
    st.markdown("""
    <div class="section-banner section-banner-green">
        <p class="section-title">03. Analysis and Interpretation</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="info-box">
        The results show a clear difference in stock behavior between normal and high-volatility environments.
        During normal market conditions, both Apple and NVIDIA tend to generate stable or slightly positive returns.
        During periods of elevated volatility, however, returns typically decline.
        <br><br>
        <span class="hl">Apple</span> shows a moderate decrease in performance during high-volatility periods,
        indicating some sensitivity to market stress but relatively stable behavior overall.
        <br><br>
        <span class="hl">NVIDIA</span>, in contrast, exhibits a stronger negative reaction. Its returns tend to
        decrease more significantly when volatility increases, suggesting a higher sensitivity to changes
        in market sentiment.
        <br><br>
        The extent of these effects depends on the selected threshold. A lower threshold captures more frequent,
        moderate volatility periods, while a higher threshold isolates fewer but more extreme market stress events.
        This allows for a more nuanced analysis of how each stock behaves under different market conditions.
    </div>
    """, unsafe_allow_html=True)

    # 04. Key Insights
    st.markdown("""
    <div class="section-banner section-banner-orange">
        <p class="section-title">04. Key Insights</p>
    </div>
    """, unsafe_allow_html=True)

    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.markdown(f"""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-red">📉</div>
                <p class="card-title">Market Stress Hurts Both Stocks</p>
            </div>
            <p class="card-body">
                Both Apple and NVIDIA tend to perform worse during periods of elevated volatility.
                A VIX above {vix_threshold:.0f} is associated with below-average returns for both stocks.
            </p>
        </div>
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-orange">⚡</div>
                <p class="card-title">NVIDIA Reacts More Strongly</p>
            </div>
            <p class="card-body">
                NVIDIA generally reacts more strongly to volatility spikes, showing larger performance
                declines. Its higher sensitivity to market sentiment makes it more vulnerable during
                periods of uncertainty.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_i2:
        st.markdown(f"""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-green">🛡️</div>
                <p class="card-title">Apple Is More Resilient</p>
            </div>
            <p class="card-body">
                Apple tends to be more resilient, with smaller changes in performance during stressful
                market periods. Its diversified revenue base and strong balance sheet provide a buffer
                against short-term sentiment shifts.
            </p>
        </div>
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-blue">🎚️</div>
                <p class="card-title">Threshold Sensitivity Matters</p>
            </div>
            <p class="card-body">
                The definition of a panic state matters. Changing the VIX threshold can significantly
                affect the results and interpretation. Try adjusting it in the sidebar to explore
                mild versus extreme market stress scenarios.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.caption("Data sources: Alpha Vantage (Stock Prices) and FRED (CBOE Volatility Index - VIX).")

else:
    st.info("Please wait while the local data is being loaded.")