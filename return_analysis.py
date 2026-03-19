import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from scipy.stats import norm, kurtosis, skew
import os
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

# --- CONFIGURATION ---
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}


# --- FUNCTION: LOAD DATA (LOCAL CSV) ---
@st.cache_data(show_spinner="Loading stock data...")
def get_stock_data_local(symbol):
    file_path = os.path.join(os.path.dirname(__file__), "data", f"stock_{symbol}.csv")
    if not os.path.exists(file_path):
        st.warning(f"No data file found for {symbol}.")
        return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        df = df.astype(float).sort_index()
        df['log_return'] = np.log(df['4. close'] / df['4. close'].shift(1))
        return df.dropna()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


# --- FUNCTION: FRED BENCHMARK ---
@st.cache_data
def get_fred_benchmark(series_id="SP500"):
    if not FRED_API_KEY:
        return None
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json"}
    try:
        r = requests.get(url, params=params)
        data = r.json()
        df = pd.DataFrame(data['observations'])
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df.set_index('date').dropna()
        df['log_return'] = np.log(df['value'] / df['value'].shift(1))
        return df.dropna()
    except Exception:
        return None


# --- UI LAYOUT ---
render_page_header(
    "Return Analysis",
    "To what extent do the daily log returns of Apple and NVIDIA deviate from a normal distribution?",
)

st.info("⬅️ Use the **sidebar** to select a stock, adjust the lookback period, and toggle the S&P 500 benchmark.")

with st.sidebar:
    st.header("Settings")
    selected_stock = st.selectbox("Select stock:", list(STOCKS.keys()))
    days_to_show = st.slider("Lookback Period (last X trading days):", min_value=5, max_value=100, value=100)
    show_benchmark = st.checkbox("Show S&P 500 (FRED)", value=True)

# Fetch data
df_stock_raw = get_stock_data_local(STOCKS[selected_stock])

if df_stock_raw is not None:
    df_filtered = df_stock_raw.tail(days_to_show)
    returns = df_filtered['log_return']

    st.caption(f"Showing last {len(df_filtered)} days from {df_filtered.index.min().date()} to {df_filtered.index.max().date()}")

    # Plotting
    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=returns, nbinsx=30, name=f'{selected_stock}',
        histnorm='probability density', marker_color='#1f77b4', opacity=0.6
    ))

    if show_benchmark:
        df_fred_all = get_fred_benchmark()
        if df_fred_all is not None:
            df_fred = df_fred_all[df_fred_all.index >= df_filtered.index.min()]
            fig.add_trace(go.Histogram(
                x=df_fred['log_return'], nbinsx=30, name='S&P 500',
                histnorm='probability density', marker_color='#ff7f0e', opacity=0.4
            ))

    mu, std = norm.fit(returns)
    x_range = np.linspace(returns.min(), returns.max(), 100)
    y_norm = norm.pdf(x_range, mu, std)
    fig.add_trace(go.Scatter(
        x=x_range, y=y_norm, mode='lines', name='Normal Dist.',
        line=dict(color='red', dash='dash')
    ))

    fig.update_layout(
        title=f"Distribution of Log-Returns: {selected_stock}",
        barmode='overlay', template="plotly_white",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.download_button(
        label="Graph als PNG herunterladen",
        data=fig_to_pdf_bytes(fig),
        file_name="return_analysis.png",
        mime="image/png",
    )

    # Metrics
    k_val = kurtosis(returns)
    s_val = skew(returns)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Excess Kurtosis", f"{k_val:.2f}")
    c2.metric("Skewness", f"{s_val:.2f}")
    c3.metric("Volatility", f"{std:.4f}")
    c4.metric("Mean", f"{mu:.5f}")

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
        font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 800;
        color: #2563eb; opacity: 1; min-width: 44px; line-height: 1.2;
        background: rgba(37,99,235,0.1); border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        padding: 4px 8px; flex-shrink: 0;
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

    # 01
    st.markdown("""
    <div class="section-banner section-banner-blue">
        <p class="section-title">01. What Does This Analysis Show?</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        This page examines how the daily price changes (<span class="hl">log returns</span>) of Apple and
        NVIDIA are distributed and whether they follow a <span class="hl">normal (Gaussian) distribution</span>,
        a common assumption in many financial models.
        <br><br>
        A normal distribution implies that most price changes are small and extreme movements are very rare.
        The dashed red line in the chart represents this idealized normal distribution, while the histogram
        shows the actual observed daily returns. By comparing both, we can assess whether real-world stock
        returns behave as theory would suggest, or whether they exhibit different, more complex patterns.
    </div>
    """, unsafe_allow_html=True)

    # 02
    st.markdown("""
    <div class="section-banner section-banner-purple">
        <p class="section-title">02. Method</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="step-card">
        <div class="step-number">01</div>
        <div>
            <p class="step-title">Log-Return Calculation</p>
            <p class="step-desc">Daily log-returns are computed as the natural logarithm of the ratio between consecutive closing prices. This ensures returns are additive over time and symmetric around zero.</p>
        </div>
    </div>
    <div class="step-card">
        <div class="step-number">02</div>
        <div>
            <p class="step-title">Distribution Fitting</p>
            <p class="step-desc">A normal distribution is fitted to the observed returns using maximum likelihood estimation. The resulting curve (red dashed line) serves as the theoretical benchmark for comparison.</p>
        </div>
    </div>
    <div class="step-card">
        <div class="step-number">03</div>
        <div>
            <p class="step-title">Statistical Measures</p>
            <p class="step-desc">Excess kurtosis quantifies how heavy the tails are. Skewness measures asymmetry. Volatility captures the overall spread of returns. Together they describe how far the distribution deviates from normality.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 03
    st.markdown("""
    <div class="section-banner section-banner-green">
        <p class="section-title">03. Analysis and Interpretation</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="info-box">
        The results show that the return distributions of both Apple and NVIDIA differ from the normal
        distribution. In both cases, the histograms display <span class="hl">fatter tails</span> than
        the normal curve, meaning that large price movements occur more frequently than expected under
        a Gaussian model. This is a well-known feature of financial markets.
        <br><br>
        <span class="hl">Apple</span> tends to have a more concentrated distribution, with most daily
        returns clustered around the center. It still shows occasional extreme movements, indicating
        the presence of tail risk even in a relatively stable stock.
        <br><br>
        <span class="hl">NVIDIA</span> exhibits a wider spread of returns with a volatility of
        <span class="hl">{std:.4f}</span> and excess kurtosis of <span class="hl">{k_val:.2f}</span>,
        meaning that daily price changes are generally larger and more extreme days occur more frequently.
        <br><br>
        The skewness of <span class="hl">{s_val:.2f}</span> indicates that the distribution is not
        perfectly symmetric, suggesting that {"negative" if s_val < 0 else "positive"} movements
        tend to be {"more frequent or more extreme" if abs(s_val) > 0.3 else "slightly more pronounced"}.
    </div>
    """, unsafe_allow_html=True)

    # 04
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
                <p class="card-title">Non-Normality of Returns</p>
            </div>
            <p class="card-body">
                Both Apple and NVIDIA clearly deviate from the normal distribution. Real-world stock
                returns show more extreme values than expected, making standard Gaussian models
                insufficient for risk assessment.
            </p>
        </div>
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-orange">⚡</div>
                <p class="card-title">Fat Tails Imply Higher Risk</p>
            </div>
            <p class="card-body">
                With an excess kurtosis of {k_val:.2f}, the tails are {"significantly" if abs(k_val) > 1 else "moderately"}
                heavier than normal. Large price movements occur more often than a Gaussian model predicts,
                implying that real-world risk is underestimated by standard models.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_i2:
        st.markdown(f"""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-blue">📊</div>
                <p class="card-title">NVIDIA Is More Volatile</p>
            </div>
            <p class="card-body">
                NVIDIA shows a broader return distribution (volatility: {std:.4f}), indicating higher
                day-to-day price variability compared to Apple. This makes it more sensitive to market
                events and sentiment shifts.
            </p>
        </div>
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-purple">📐</div>
                <p class="card-title">Asymmetry in Returns</p>
            </div>
            <p class="card-body">
                With a skewness of {s_val:.2f}, the return distribution is not symmetric.
                {"Negative movements tend to be more extreme, a common feature of equity markets during stress periods." if s_val < 0 else "Positive movements tend to be slightly more pronounced during this period."}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        """
        <section class="research-header">
            <p class="research-header__eyebrow">Answer to the Research Question</p>
            <p class="research-header__question">
                Both Apple and NVIDIA deviate significantly from a normal distribution, exhibiting fat tails
                and non-Gaussian characteristics. While Apple shows occasional extreme movements with a
                relatively concentrated distribution, NVIDIA displays a broader and more volatile distribution,
                indicating stronger overall deviations from normality and higher sensitivity to market events.
                These findings confirm that standard Gaussian models underestimate the true risk of both stocks.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Data sources: Alpha Vantage (Stock Prices) and FRED (S&P 500 Index).")