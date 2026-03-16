import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from scipy.stats import norm, kurtosis, skew, pearsonr
from scipy import stats as scipy_stats
import os

# --- CONFIGURATION ---
AV_API_KEY = st.secrets.get("AV_API_KEY", "")
FRED_API_KEY = st.secrets["FRED_API_KEY"]
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}



# --- FUNCTION: LOAD DATA (ALPHA VANTAGE - COMPACT ONLY) ---
@st.cache_data(show_spinner="Fetching latest 100 days...")
def get_stock_data_compact(symbol):
    # 'compact' returns the latest 100 data points (Free Tier limit)
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
            # Calculate log returns
            df['log_return'] = np.log(df['4. close'] / df['4. close'].shift(1))
            return df.dropna()
        else:
            st.warning("No data found. Check if the market is open or API key is valid.")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None


# --- FUNCTION: FRED BENCHMARK ---
@st.cache_data
def get_fred_benchmark(series_id="SP500"):
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
    except:
        return None


# --- UI LAYOUT ---
st.title("Return Distribution Analysis (Latest 100 Days)")
st.markdown("**Research Question 1:** How do recent daily log-returns deviate from a normal distribution?")

with st.sidebar:
    st.header("Settings")
    selected_stock = st.selectbox("Select stock:", list(STOCKS.keys()))

    # Slider restricted to 100 days due to API limitations
    days_to_show = st.slider("Lookback Period (last X trading days):",
                             min_value=5,
                             max_value=100,
                             value=100)

    show_benchmark = st.checkbox("Show S&P 500 (FRED)", value=True)
    st.divider()
    st.info("Note: Alpha Vantage Free Tier is limited to the most recent 100 days.")

# Fetch data
df_stock_raw = get_stock_data_compact(STOCKS[selected_stock])

if df_stock_raw is not None:
    # Slice the data based on slider
    df_filtered = df_stock_raw.tail(days_to_show)
    returns = df_filtered['log_return']

    # Date Info
    st.caption(
        f"Showing last {len(df_filtered)} days from {df_filtered.index.min().date()} to {df_filtered.index.max().date()}")

    # Plotting
    fig = go.Figure()

    # 1. Stock Histogram
    fig.add_trace(go.Histogram(
        x=returns, nbinsx=30, name=f'{selected_stock}',
        histnorm='probability density', marker_color='#1f77b4', opacity=0.6
    ))

    # 2. FRED Benchmark
    if show_benchmark:
        df_fred_all = get_fred_benchmark()
        if df_fred_all is not None:
            df_fred = df_fred_all[df_fred_all.index >= df_filtered.index.min()]
            fig.add_trace(go.Histogram(
                x=df_fred['log_return'], nbinsx=30, name='S&P 500',
                histnorm='probability density', marker_color='#ff7f0e', opacity=0.4
            ))

    # 3. Normal Distribution Reference
    mu, std = norm.fit(returns)
    x_range = np.linspace(returns.min(), returns.max(), 100)
    y_norm = norm.pdf(x_range, mu, std)
    fig.add_trace(
        go.Scatter(x=x_range, y=y_norm, mode='lines', name='Normal Dist.', line=dict(color='red', dash='dash')))

    fig.update_layout(
        title=f"Distribution of Log-Returns: {selected_stock}",
        barmode='overlay',
        template="plotly_white",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Metrics Board
    k_val = kurtosis(returns)  # Excess Kurtosis
    s_val = skew(returns)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Excess Kurtosis", f"{k_val:.2f}")
    c2.metric("Skewness", f"{s_val:.2f}")
    c3.metric("Volatility", f"{std:.4f}")
    c4.metric("Mean", f"{mu:.5f}")

    # Short Analysis
    st.subheader("Analysis Summary")
    if k_val > 0.5:
        st.write(
            f"Even within the last 100 days, {selected_stock} shows signs of **Leptokurtosis** (Kurtosis > 0), indicating 'fatter tails' than a normal distribution.")
    else:
        st.write("Over this short-term period, the distribution remains relatively close to the normal model.")


# =============================================================================
# RESEARCH QUESTION 7: iPhone Sales vs Post-Earnings Stock Returns
# =============================================================================

st.divider()
st.title("Product-to-Stock Interdependence: iPhone Sales vs Post-Earnings Returns")
st.markdown("""
**Research Question 7:** *How does the quarterly sales volume of iPhone units statistically
correlate with Apple's stock price returns in the month following the earnings release?*
""")

st.markdown("""
#### Methodology
This analysis examines the relationship between quarterly iPhone sales and Apple's stock
performance in the 30 calendar days following each earnings announcement. We use:
- **iPhone unit sales data** from quarterly earnings reports (Q1 2019 – Q1 2025)
- **Apple stock prices** at earnings date and 30 days after (historical data)
- **Pearson correlation** and **OLS linear regression** to quantify the relationship
""")


# --- Load iPhone Sales Data (includes pre-collected price data) ---
@st.cache_data
def load_earnings_dataset():
    csv_path = os.path.join(os.path.dirname(__file__), "data", "iphone_sales.csv")
    df = pd.read_csv(csv_path)
    df["earnings_date"] = pd.to_datetime(df["earnings_date"])
    df["return_30d"] = (df["price_30d_after"] - df["price_on_earnings"]) / df["price_on_earnings"]
    df["return_30d_pct"] = (df["return_30d"] * 100).round(2)
    df["iphone_sales_growth"] = df["iphone_units_million"].pct_change()
    return df


# --- Main RQ7 Section ---
merged = load_earnings_dataset()

if len(merged) >= 3:
    # --- Statistical Analysis ---
    x = merged["iphone_units_million"].values
    y = merged["return_30d"].values

    corr, p_corr = pearsonr(x, y)
    slope, intercept, r_value, p_reg, std_err = scipy_stats.linregress(x, y)
    r_squared = r_value ** 2

    # --- Scatter Plot with Regression Line ---
    st.subheader("1. Scatter Plot: iPhone Sales vs 30-Day Post-Earnings Return")

    fig_scatter = go.Figure()

    fig_scatter.add_trace(go.Scatter(
        x=x, y=y * 100,
        mode="markers+text",
        text=merged["quarter"],
        textposition="top center",
        textfont=dict(size=9),
        marker=dict(size=10, color="#e94560", line=dict(width=1, color="white")),
        name="Quarters",
    ))

    # Regression line
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = (slope * x_line + intercept) * 100
    fig_scatter.add_trace(go.Scatter(
        x=x_line, y=y_line,
        mode="lines",
        name=f"Regression (R²={r_squared:.3f})",
        line=dict(color="#1f77b4", dash="dash", width=2),
    ))

    fig_scatter.update_layout(
        xaxis_title="iPhone Units Sold (millions)",
        yaxis_title="30-Day Post-Earnings Return (%)",
        template="plotly_white",
        height=500,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # --- Time Series Chart ---
    st.subheader("2. Time Series: iPhone Sales & Post-Earnings Returns by Quarter")

    fig_ts = make_subplots(specs=[[{"secondary_y": True}]])

    fig_ts.add_trace(
        go.Bar(
            x=merged["quarter"], y=merged["iphone_units_million"],
            name="iPhone Units (M)", marker_color="#1f77b4", opacity=0.7,
        ),
        secondary_y=False,
    )

    fig_ts.add_trace(
        go.Scatter(
            x=merged["quarter"], y=merged["return_30d_pct"],
            name="30-Day Return (%)", mode="lines+markers",
            line=dict(color="#e94560", width=2),
            marker=dict(size=7),
        ),
        secondary_y=True,
    )

    fig_ts.update_layout(
        template="plotly_white", height=500,
        legend=dict(yanchor="top", y=1.15, xanchor="center", x=0.5, orientation="h"),
    )
    fig_ts.update_yaxes(title_text="iPhone Units Sold (millions)", secondary_y=False)
    fig_ts.update_yaxes(title_text="30-Day Post-Earnings Return (%)", secondary_y=True)

    st.plotly_chart(fig_ts, use_container_width=True)

    # --- Statistical Results Table ---
    st.subheader("3. Statistical Results")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pearson r", f"{corr:.4f}")
    col2.metric("R²", f"{r_squared:.4f}")
    col3.metric("p-value", f"{p_corr:.4f}")
    col4.metric("Slope (β₁)", f"{slope:.6f}")

    st.markdown("**Linear Regression Model:**")
    st.latex(
        rf"\text{{Return}}_{{30d}} = {intercept:.4f} + {slope:.6f} "
        rf"\times \text{{iPhone\_Sales}} \quad (p = {p_reg:.4f})"
    )

    # --- Data Table ---
    with st.expander("View Full Dataset"):
        display_cols = [
            "quarter", "earnings_date", "iphone_units_million",
            "iphone_revenue_billion", "price_on_earnings",
            "price_30d_after", "return_30d_pct",
        ]
        st.dataframe(
            merged[display_cols].rename(columns={
                "quarter": "Quarter",
                "earnings_date": "Earnings Date",
                "iphone_units_million": "iPhone Units (M)",
                "iphone_revenue_billion": "iPhone Revenue ($B)",
                "price_on_earnings": "Price at Earnings ($)",
                "price_30d_after": "Price 30d After ($)",
                "return_30d_pct": "30-Day Return (%)",
            }),
            use_container_width=True,
            hide_index=True,
        )

    # --- Interpretation ---
    st.subheader("4. Interpretation")

    sig_level = 0.05
    is_significant = p_corr < sig_level
    direction = "positive" if corr > 0 else "negative"

    if is_significant:
        st.success(f"""
        **Statistically significant {direction} correlation found** (p = {p_corr:.4f} < {sig_level}).

        The Pearson correlation of **r = {corr:.4f}** indicates a {direction} linear relationship
        between quarterly iPhone unit sales and Apple's 30-day post-earnings stock returns.
        The regression model explains **{r_squared*100:.1f}%** of the variance in post-earnings returns.
        """)
    else:
        st.info(f"""
        **No statistically significant correlation found** (p = {p_corr:.4f} > {sig_level}).

        The Pearson correlation of **r = {corr:.4f}** does not reach statistical significance
        at the 5% level. The regression model explains only **{r_squared*100:.1f}%** of the variance,
        suggesting that iPhone unit sales alone are not a reliable predictor of post-earnings returns.
        """)

    st.markdown("""
    **Possible explanations:**
    - **Market expectations matter more than absolute sales:** If the market already prices in
      expected iPhone sales, only *surprises* (beats or misses vs. consensus) drive returns.
    - **Earnings are multi-dimensional:** Apple's stock reacts to guidance, services revenue,
      margins, and macroeconomic outlook — not just iPhone units.
    - **Product cycle effects:** Launch quarters (Q4/Q1) naturally have higher sales, but the
      market anticipates this seasonality, dampening the return signal.
    - **Sample size:** With ~25 quarterly observations, detecting moderate effects requires
      a fairly strong true correlation.
    """)
else:
    st.warning("Not enough data points to perform a meaningful analysis.")
