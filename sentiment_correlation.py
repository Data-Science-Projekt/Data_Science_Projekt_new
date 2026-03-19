import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from scipy.stats import pearsonr, spearmanr
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

# --- CONFIGURATION ---
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
ALL_STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

# --- DATA LOADING (LOCAL) ---
@st.cache_data(show_spinner="Loading local market data...")
def get_monthly_data_local(symbol):
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True).sort_index()
        monthly = df[["4. close"]].resample("MS").last()
        monthly["monthly_return"] = monthly["4. close"].pct_change()
        return monthly[["monthly_return"]].dropna()
    except Exception:
        return None

@st.cache_data(show_spinner="Loading consumer sentiment...")
def get_sentiment_local():
    file_path = "data/consumer_sentiment.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].dt.to_period("M").dt.to_timestamp()
        df = df.rename(columns={"value": "sentiment"})
        df['sentiment'] = pd.to_numeric(df['sentiment'], errors='coerce')
        return df.set_index('date')[['sentiment']].dropna()
    except Exception:
        return None

# --- UI ---
render_page_header(
    "Sentiment Correlation",
    "How does the broader Consumer Sentiment Index (University of Michigan) correlate with selected tech stocks (Apple, Microsoft, NVIDIA) and selected financial stocks (J.P. Morgan, Goldman Sachs, Bank of America)?",
)

st.markdown("""
#### Methodology
- **Consumer Sentiment Index** from the University of Michigan (via FRED API) — a monthly survey
  measuring consumer confidence about the economy
- **Monthly stock returns** from Alpha Vantage for 6 stocks across two sectors
- **Pearson & Spearman correlations** to quantify linear and rank-based relationships
- **Rolling correlation** to examine how the relationship evolves over time
""")

# Load data
sentiment_df = get_sentiment_local()
stock_returns = {}

if sentiment_df is not None:
    for name, symbol in ALL_STOCKS.items():
        data = get_monthly_data_local(symbol)
        if data is not None:
            stock_returns[name] = data.rename(columns={"monthly_return": name})

if sentiment_df is None or not stock_returns:
    st.error("Data files not found in /data folder. Please ensure the bot has run successfully.")
    st.stop()

# Merge all data
merged = sentiment_df.copy()
for name, ret_df in stock_returns.items():
    merged = merged.join(ret_df, how="inner")
merged = merged.dropna()

if len(merged) < 3:
    st.warning(f"Only {len(merged)} months of overlapping data. Need at least 3.")
    st.stop()

# Sidebar
st.sidebar.header("Analysis Parameters")
if len(merged) > 3:
    rolling_window = st.sidebar.slider("Rolling Correlation Window (months)", 3, len(merged), min(12, len(merged)))
else:
    rolling_window = 3
st.sidebar.info(f"Analysis is based on {len(merged)} months of available data.")

st.write(f"**Period:** {merged.index.min().strftime('%Y-%m')} to {merged.index.max().strftime('%Y-%m')} ({len(merged)} months)")

# --- Stock names for iteration ---
stock_names = [n for n in ALL_STOCKS.keys() if n in merged.columns]

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

st.download_button(
    label="📥 Graph als PNG herunterladen",
    data=fig_to_pdf_bytes(fig_sent),
    file_name="sentiment_index.png",
    mime="image/png",
    key="download_sentiment_index"
)

# --- 2. Correlation Heatmap ---
st.subheader("2. Correlation Matrix: Sentiment vs Stock Returns")

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

st.download_button(
    label="📥 Graph als PNG herunterladen",
    data=fig_to_pdf_bytes(fig_heatmap),
    file_name="sentiment_correlation.png",
    mime="image/png",
    key="download_sentiment_heatmap"
)

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

    st.download_button(
        label="📥 Graph als PNG herunterladen",
        data=fig_to_pdf_bytes(fig_tech),
        file_name="sentiment_scatter_tech.png",
        mime="image/png",
        key="download_scatter_tech"
    )

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

    st.download_button(
        label="📥 Graph als PNG herunterladen",
        data=fig_to_pdf_bytes(fig_fin),
        file_name="sentiment_scatter_financial.png",
        mime="image/png",
        key="download_scatter_fin"
    )

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

st.download_button(
    label="📥 Graph als PNG herunterladen",
    data=fig_to_pdf_bytes(fig_rolling),
    file_name="sentiment_rolling_correlation.png",
    mime="image/png",
    key="download_rolling_corr"
)

# --- 6. Sector Comparison ---
st.subheader("6. Sector Comparison")

tech_corrs = [c["Pearson r"] for c in corr_data if c["Sector"] == "Tech"]
fin_corrs = [c["Pearson r"] for c in corr_data if c["Sector"] == "Financial"]
tech_avg = np.mean(tech_corrs) if tech_corrs else 0
fin_avg = np.mean(fin_corrs) if fin_corrs else 0

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Avg Tech Correlation", f"{tech_avg:.4f}")
with c2:
    st.metric("Avg Financial Correlation", f"{fin_avg:.4f}")
with c3:
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

st.download_button(
    label="📥 Graph als PNG herunterladen",
    data=fig_to_pdf_bytes(fig_sector),
    file_name="sentiment_sector_comparison.png",
    mime="image/png",
    key="download_sector_comparison"
)

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
st.caption("Data source: Local files (data/). Sentiment: Univ. of Michigan (FRED). Stocks: Alpha Vantage.")
