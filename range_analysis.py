import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

# --- CONFIGURATION ---
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
ALL_STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

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

# --- FUNCTION: LOAD DATA (LOCAL) ---
@st.cache_data(show_spinner="Loading historical trading data...")
def get_stock_data_local(symbol):
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        df = df.astype(float).sort_index()
        df["absolute_range"] = df["2. high"] - df["3. low"]
        df["relative_range_pct"] = (df["absolute_range"] / df["4. close"]) * 100
        return df
    except Exception:
        return None

# --- MAIN APP ---
render_page_header(
    "Volatility",
    "What are the differences in the daily trading range between selected tech stocks (Apple, Microsoft, NVIDIA) and selected financial stocks (J.P. Morgan, Goldman Sachs, Bank of America)?",
)

st.info("⬅️ Use the **sidebar** to adjust trading days and select stocks.")

# Sidebar for controls
st.sidebar.header("Analysis Parameters")
days = st.sidebar.slider("Number of Trading Days", min_value=10, max_value=100, value=100, step=10)
selected_tech = st.sidebar.multiselect("Select Tech Stocks", list(TECH_STOCKS.keys()), default=list(TECH_STOCKS.keys()))
selected_financial = st.sidebar.multiselect("Select Financial Stocks", list(FINANCIAL_STOCKS.keys()), default=list(FINANCIAL_STOCKS.keys()))

if not selected_tech and not selected_financial:
    st.warning("Please select at least one stock.")
    st.stop()

selected_stocks = {**{k: TECH_STOCKS[k] for k in selected_tech}, **{k: FINANCIAL_STOCKS[k] for k in selected_financial}}

# Load data
stock_data = {}
with st.spinner("Loading data..."):
    for name, symbol in selected_stocks.items():
        df = get_stock_data_local(symbol)
        if df is not None:
            stock_data[name] = df.tail(days)

if not stock_data:
    st.error("No data could be loaded. Please check the bot status.")
    st.stop()

# Determine common date range
min_date = max(df.index.min() for df in stock_data.values())
max_date = min(df.index.max() for df in stock_data.values())
for name in stock_data:
    stock_data[name] = stock_data[name][(stock_data[name].index >= min_date) & (stock_data[name].index <= max_date)]

# --- DISPLAY RESULTS ---
st.subheader("Analysis Summary")
st.write(f"**Period:** {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')} ({len(stock_data[list(stock_data.keys())[0]])} trading days)")

# Boxplot
st.subheader("Distribution of Daily Trading Ranges (Percent)")
fig_box = go.Figure()
for name, df in stock_data.items():
    fig_box.add_trace(go.Box(y=df["relative_range_pct"], name=name, boxmean=True))
fig_box.update_layout(
    yaxis_title="Relative Trading Range (%)",
    template="plotly_white",
    **CHART_STYLE
)
st.plotly_chart(fig_box, use_container_width=True)

st.download_button(
    label="📥 Graph als PNG herunterladen",
    data=fig_to_pdf_bytes(fig_box),
    file_name="volatility_boxplot.png",
    mime="image/png",
    key="download_volatility_box"
)

# --- Area Chart: Tech vs. Financial sector average ---
st.subheader("Sector Volatility Trend Over Time")

# Build a shared date index
all_dates = stock_data[list(stock_data.keys())[0]].index

tech_dfs    = [stock_data[n]["relative_range_pct"] for n in selected_tech      if n in stock_data]
fin_dfs     = [stock_data[n]["relative_range_pct"] for n in selected_financial if n in stock_data]

tech_avg = pd.concat(tech_dfs,  axis=1).mean(axis=1).rolling(5).mean() if tech_dfs else None
fin_avg  = pd.concat(fin_dfs,   axis=1).mean(axis=1).rolling(5).mean() if fin_dfs  else None

fig_area = go.Figure()

if tech_avg is not None:
    fig_area.add_trace(go.Scatter(
        x=tech_avg.index,
        y=tech_avg.values,
        name="Tech (avg)",
        mode="lines",
        line=dict(color="#2563eb", width=2),
        fill="tozeroy",
        fillcolor="rgba(37,99,235,0.12)",
    ))

if fin_avg is not None:
    fig_area.add_trace(go.Scatter(
        x=fin_avg.index,
        y=fin_avg.values,
        name="Financial (avg)",
        mode="lines",
        line=dict(color="#16a34a", width=2),
        fill="tozeroy",
        fillcolor="rgba(22,163,74,0.12)",
    ))

fig_area.update_layout(
    xaxis_title="Date",
    yaxis_title="Avg. Relative Trading Range (%, 5-day smoothed)",
    template="plotly_white",
    hovermode="x unified",
    **CHART_STYLE
)
st.plotly_chart(fig_area, use_container_width=True)

st.download_button(
    label="📥 Graph als PNG herunterladen",
    data=fig_to_pdf_bytes(fig_area),
    file_name="volatility_area.png",
    mime="image/png",
    key="download_volatility_area"
)

# Statistics Table
st.subheader("Statistical Metrics per Stock")
stats_data = []
for name, df in stock_data.items():
    ranges = df["relative_range_pct"]
    stats_data.append({
        "Stock": name,
        "Sector": "Tech" if name in TECH_STOCKS else "Financial",
        "Mean (%)": f"{ranges.mean():.2f}",
        "Median (%)": f"{ranges.median():.2f}",
        "Std. Dev. (%)": f"{ranges.std():.2f}",
        "Min (%)": f"{ranges.min():.2f}",
        "Max (%)": f"{ranges.max():.2f}",
    })
st.table(pd.DataFrame(stats_data))

# Sector Comparison
st.subheader("Sector Comparison")
tech_ranges = []
financial_ranges = []
for name, df in stock_data.items():
    if name in TECH_STOCKS:
        tech_ranges.extend(df["relative_range_pct"].tolist())
    elif name in FINANCIAL_STOCKS:
        financial_ranges.extend(df["relative_range_pct"].tolist())

tech_avg_val     = np.mean(tech_ranges)     if tech_ranges     else 0
financial_avg_val = np.mean(financial_ranges) if financial_ranges else 0
diff = tech_avg_val - financial_avg_val

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Tech Avg. Range (%)", f"{tech_avg_val:.2f}")
with col2:
    st.metric("Financial Avg. Range (%)", f"{financial_avg_val:.2f}")
with col3:
    st.metric("Difference (Tech - Fin)", f"{diff:.2f}")

# Conclusion Text
st.subheader("Key Findings")
summary_logic = "Tech stocks show higher volatility in daily ranges." if diff > 0 else "Financial stocks show higher volatility." if diff < 0 else "Both sectors show similar trading ranges."
summary = f"""
The analysis of the last {len(stock_data[list(stock_data.keys())[0]])} trading days shows:
Tech stocks have an average range of {tech_avg_val:.2f}%, while Financial stocks average {financial_avg_val:.2f}%.
The difference is {diff:.2f} percentage points.
{summary_logic}
"""
st.write(summary)