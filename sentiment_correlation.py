import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import os
import time
from scipy.stats import pearsonr, spearmanr
from scipy import stats as scipy_stats

# --- CONFIGURATION ---
AV_API_KEY = st.secrets["AV_API_KEY"]
FRED_API_KEY = st.secrets["FRED_API_KEY"]
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}

# --- FILE-BASED CACHE ---
CACHE_DIR = os.path.join(os.path.dirname(__file__), "data", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(key):
    return os.path.join(CACHE_DIR, f"{key}.csv")


def _save_to_disk(key, df):
    try:
        df.to_csv(_cache_path(key))
    except Exception:
        pass


def _load_from_disk(key):
    path = _cache_path(key)
    if os.path.exists(path):
        try:
            return pd.read_csv(path, index_col=0, parse_dates=True)
        except Exception:
            pass
    return None



# --- FETCH STOCK DATA ---
_av_last_call = [0.0]


@st.cache_data(show_spinner="Loading stock data...")
def get_stock_monthly_returns(symbol):
    """Fetch monthly data from Alpha Vantage (or disk cache). Falls back to daily cache."""
    # Try disk cache first
    cached = _load_from_disk(f"monthly_{symbol}")
    if cached is not None:
        return cached

    # Fetch monthly time series from API (1 call = full history)
    elapsed = time.time() - _av_last_call[0]
    if elapsed < 15:
        time.sleep(15 - elapsed)
    _av_last_call[0] = time.time()

    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY&symbol={symbol}&apikey={AV_API_KEY}"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()

        if "Monthly Time Series" in data:
            df = pd.DataFrame.from_dict(data["Monthly Time Series"], orient="index")
            df.index = pd.to_datetime(df.index)
            df = df.astype(float).sort_index()
            # Align to month-start to match FRED dates
            df.index = df.index.to_period("M").to_timestamp("MS")
            df["monthly_return"] = df["4. close"].pct_change()
            _save_to_disk(f"monthly_{symbol}", df)
            return df
    except Exception:
        pass

    # Fallback: aggregate daily cache to monthly
    daily = _load_from_disk(f"stock_{symbol}")
    if daily is not None:
        daily.index = pd.to_datetime(daily.index)
        monthly = daily[["4. close"]].resample("MS").last()
        monthly["monthly_return"] = monthly["4. close"].pct_change()
        return monthly

    st.error(f"No data available for {symbol}.")
    return None


# --- FETCH CONSUMER SENTIMENT (University of Michigan via FRED) ---
@st.cache_data(show_spinner="Fetching Consumer Sentiment Index...")
def get_consumer_sentiment():
    cached = _load_from_disk("consumer_sentiment")

    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id=UMCSENT&api_key={FRED_API_KEY}&file_type=json"
        f"&observation_start=2020-01-01"
    )
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        obs = data.get("observations", [])
        if not obs:
            if cached is not None:
                st.warning("No FRED data. Using cached sentiment.")
                return cached
            return None

        records = []
        for o in obs:
            if o["value"] == ".":
                continue
            records.append({"date": pd.to_datetime(o["date"]), "sentiment": float(o["value"])})

        df = pd.DataFrame(records).set_index("date").sort_index()
        _save_to_disk("consumer_sentiment", df)
        return df
    except Exception:
        if cached is not None:
            st.warning("FRED connection error. Using cached sentiment.")
            return cached
        return None


# --- MAIN APP ---
st.title("Research Question 8: Sentiment Correlation")
st.markdown("""
**Research Question:** How does the broader Consumer Sentiment Index (University of Michigan)
correlate with selected tech stocks (Apple, Microsoft, NVIDIA) and selected financial stocks
(J.P. Morgan, Goldman Sachs, Bank of America)?
""")

st.markdown("""
#### Methodology
- **Consumer Sentiment Index** from the University of Michigan (via FRED API) — a monthly survey
  measuring consumer confidence about the economy
- **Monthly stock returns** from Alpha Vantage for 6 stocks across two sectors
- **Pearson & Spearman correlations** to quantify linear and rank-based relationships
- **Rolling correlation** to examine how the relationship evolves over time
""")

# Sidebar
st.sidebar.header("Analysis Parameters")
lookback_years = st.sidebar.slider("Lookback Period (years)", 1, 5, 3)
rolling_window = st.sidebar.slider("Rolling Correlation Window (months)", 3, 24, 12)

# Fetch data
sentiment_df = get_consumer_sentiment()
if sentiment_df is None:
    st.error("Could not load Consumer Sentiment data.")
    st.stop()

all_stocks = {**TECH_STOCKS, **FINANCIAL_STOCKS}
stock_returns = {}

with st.spinner("Loading stock data..."):
    for name, symbol in all_stocks.items():
        df = get_stock_monthly_returns(symbol)
        if df is not None:
            stock_returns[name] = df[["monthly_return"]].rename(columns={"monthly_return": name})

if not stock_returns:
    st.error("No stock data could be loaded.")
    st.stop()

# Merge all data
merged = sentiment_df.copy()
for name, ret_df in stock_returns.items():
    merged = merged.join(ret_df, how="inner")

# Filter by lookback period
cutoff = merged.index.max() - pd.DateOffset(years=lookback_years)
merged = merged[merged.index >= cutoff].dropna()

if len(merged) < 3:
    st.warning(f"Only {len(merged)} months of overlapping data. Need at least 3.")
    st.stop()

st.write(f"**Period:** {merged.index.min().strftime('%Y-%m')} to {merged.index.max().strftime('%Y-%m')} ({len(merged)} months)")

# --- 1. Sentiment Index Over Time ---
st.subheader("1. Consumer Sentiment Index Over Time")
fig_sent = go.Figure()
fig_sent.add_trace(go.Scatter(
    x=merged.index, y=merged["sentiment"],
    mode="lines+markers", name="Consumer Sentiment",
    line=dict(color="#1f77b4", width=2),
    marker=dict(size=4),
))
fig_sent.update_layout(
    yaxis_title="Sentiment Index",
    xaxis_title="Date",
    template="plotly_white", height=400,
)
st.plotly_chart(fig_sent, use_container_width=True)

# --- 2. Correlation Heatmap ---
st.subheader("2. Correlation Matrix: Sentiment vs Stock Returns")

stock_names = [n for n in all_stocks.keys() if n in merged.columns]
corr_data = []
for name in stock_names:
    pearson_r, pearson_p = pearsonr(merged["sentiment"], merged[name])
    spearman_r, spearman_p = spearmanr(merged["sentiment"], merged[name])
    sector = "Tech" if name in TECH_STOCKS else "Financial"
    corr_data.append({
        "Stock": name,
        "Sector": sector,
        "Pearson r": pearson_r,
        "Pearson p-value": pearson_p,
        "Spearman r": spearman_r,
        "Spearman p-value": spearman_p,
    })

corr_df = pd.DataFrame(corr_data)

# Heatmap
corr_matrix = merged[["sentiment"] + stock_names].corr()
fig_heatmap = go.Figure(data=go.Heatmap(
    z=corr_matrix.values,
    x=corr_matrix.columns,
    y=corr_matrix.index,
    colorscale="RdBu_r",
    zmid=0,
    text=np.round(corr_matrix.values, 3),
    texttemplate="%{text}",
    textfont={"size": 12},
))
fig_heatmap.update_layout(template="plotly_white", height=500)
st.plotly_chart(fig_heatmap, use_container_width=True)

# Correlation table
st.subheader("3. Detailed Correlation Statistics")
display_df = corr_df.copy()
for col in ["Pearson r", "Spearman r"]:
    display_df[col] = display_df[col].map("{:.4f}".format)
for col in ["Pearson p-value", "Spearman p-value"]:
    display_df[col] = display_df[col].map("{:.4f}".format)
st.table(display_df)

# --- 4. Scatter Plots ---
st.subheader("4. Scatter Plots: Sentiment vs Monthly Returns")

tech_names = [n for n in TECH_STOCKS.keys() if n in merged.columns]
fin_names = [n for n in FINANCIAL_STOCKS.keys() if n in merged.columns]

colors_tech = ["#1f77b4", "#ff7f0e", "#2ca02c"]
colors_fin = ["#d62728", "#9467bd", "#8c564b"]

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Tech Stocks**")
    fig_tech = go.Figure()
    for i, name in enumerate(tech_names):
        fig_tech.add_trace(go.Scatter(
            x=merged["sentiment"], y=merged[name] * 100,
            mode="markers", name=name,
            marker=dict(size=8, color=colors_tech[i], opacity=0.7),
        ))
    fig_tech.update_layout(
        xaxis_title="Consumer Sentiment Index",
        yaxis_title="Monthly Return (%)",
        template="plotly_white", height=400,
    )
    st.plotly_chart(fig_tech, use_container_width=True)

with col2:
    st.markdown("**Financial Stocks**")
    fig_fin = go.Figure()
    for i, name in enumerate(fin_names):
        fig_fin.add_trace(go.Scatter(
            x=merged["sentiment"], y=merged[name] * 100,
            mode="markers", name=name,
            marker=dict(size=8, color=colors_fin[i], opacity=0.7),
        ))
    fig_fin.update_layout(
        xaxis_title="Consumer Sentiment Index",
        yaxis_title="Monthly Return (%)",
        template="plotly_white", height=400,
    )
    st.plotly_chart(fig_fin, use_container_width=True)

# --- 5. Rolling Correlation ---
st.subheader("5. Rolling Correlation Over Time")

fig_rolling = go.Figure()
all_colors = colors_tech + colors_fin
for i, name in enumerate(stock_names):
    rolling_corr = merged["sentiment"].rolling(rolling_window).corr(merged[name])
    fig_rolling.add_trace(go.Scatter(
        x=merged.index, y=rolling_corr,
        mode="lines", name=name,
        line=dict(color=all_colors[i % len(all_colors)], width=1.5),
    ))

fig_rolling.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
fig_rolling.update_layout(
    xaxis_title="Date",
    yaxis_title=f"Rolling {rolling_window}-Month Pearson Correlation",
    template="plotly_white", height=500,
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
)
st.plotly_chart(fig_rolling, use_container_width=True)

# --- 6. Sector Comparison ---
st.subheader("6. Sector Comparison")

tech_corrs = [c["Pearson r"] for c in corr_data if c["Sector"] == "Tech"]
fin_corrs = [c["Pearson r"] for c in corr_data if c["Sector"] == "Financial"]
tech_avg = np.mean(tech_corrs) if tech_corrs else 0
fin_avg = np.mean(fin_corrs) if fin_corrs else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Avg Tech Correlation", f"{tech_avg:.4f}")
with col2:
    st.metric("Avg Financial Correlation", f"{fin_avg:.4f}")
with col3:
    st.metric("Difference (Tech - Fin)", f"{tech_avg - fin_avg:.4f}")

fig_sector = go.Figure()
fig_sector.add_trace(go.Bar(
    x=[c["Stock"] for c in corr_data],
    y=[c["Pearson r"] for c in corr_data],
    marker_color=["#1f77b4" if c["Sector"] == "Tech" else "#d62728" for c in corr_data],
    text=[f"{c['Pearson r']:.3f}" for c in corr_data],
    textposition="outside",
))
fig_sector.add_hline(y=0, line_dash="dash", line_color="gray")
fig_sector.update_layout(
    yaxis_title="Pearson Correlation with Consumer Sentiment",
    template="plotly_white", height=400,
)
st.plotly_chart(fig_sector, use_container_width=True)

# --- 7. Key Insights ---
st.subheader("7. Key Insights")

sig_stocks = [c["Stock"] for c in corr_data if c["Pearson p-value"] < 0.05]
nonsig_stocks = [c["Stock"] for c in corr_data if c["Pearson p-value"] >= 0.05]

strongest = max(corr_data, key=lambda c: abs(c["Pearson r"]))
weakest = min(corr_data, key=lambda c: abs(c["Pearson r"]))

summary = f"""
**Analysis of {len(merged)} months** from {merged.index.min().strftime('%Y-%m')} to {merged.index.max().strftime('%Y-%m')}:

- **Strongest correlation:** {strongest['Stock']} (r = {strongest['Pearson r']:.4f}, p = {strongest['Pearson p-value']:.4f})
- **Weakest correlation:** {weakest['Stock']} (r = {weakest['Pearson r']:.4f}, p = {weakest['Pearson p-value']:.4f})
- **Tech sector avg correlation:** {tech_avg:.4f}
- **Financial sector avg correlation:** {fin_avg:.4f}
"""

if sig_stocks:
    summary += f"\n- **Statistically significant (p < 0.05):** {', '.join(sig_stocks)}"
if nonsig_stocks:
    summary += f"\n- **Not significant (p >= 0.05):** {', '.join(nonsig_stocks)}"

if abs(fin_avg) > abs(tech_avg):
    summary += "\n\nFinancial stocks show a stronger sensitivity to consumer sentiment, consistent with their direct exposure to consumer spending and credit conditions."
elif abs(tech_avg) > abs(fin_avg):
    summary += "\n\nTech stocks show a stronger sensitivity to consumer sentiment, possibly reflecting their dependence on consumer demand for devices and services."
else:
    summary += "\n\nBoth sectors show similar sensitivity to consumer sentiment."

st.markdown(summary)
