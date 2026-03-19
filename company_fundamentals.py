import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import pearsonr, spearmanr
import os
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

# --- CONFIGURATION ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

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

@st.cache_data(show_spinner="Loading fundamental data...")
def load_iphone_sales():
    path = os.path.join("data", "iphone_sales.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, parse_dates=["earnings_date"])
        df = df.sort_values("earnings_date").reset_index(drop=True)
        if "price_on_earnings" in df.columns and "price_30d_after" in df.columns:
            df["price_change_pct"] = (
                (df["price_30d_after"] - df["price_on_earnings"]) / df["price_on_earnings"] * 100
            )
        df["revenue_growth"] = df["iphone_revenue_billion"].pct_change() * 100
        df["units_growth"] = df["iphone_units_million"].pct_change() * 100
        return df
    except Exception:
        return pd.DataFrame()


# --- MAIN PAGE ---
render_page_header(
    "Company Fundamentals",
    "How does the quarterly sales volume of iPhone units statistically correlate with Apple's stock price returns in the month following the earnings release?",
)

st.markdown("""
#### Methodology
- **iPhone Volume and Revenue:** Data sourced from Apple's quarterly reports.
- **Stock Price Reaction:** Comparison of the price on the announcement day vs. 30 days later.
- **Correlation Analysis:** Relationship between revenue/unit numbers and price reaction.
- **Seasonality:** Identification of patterns across fiscal quarters.
""")

df = load_iphone_sales()

if df.empty:
    st.error("The file data/iphone_sales.csv was not found or is empty. Please maintain data manually.")
    st.stop()

st.write(f"**Analysis Period:** {df['quarter'].iloc[0]} to {df['quarter'].iloc[-1]} ({len(df)} quarters)")

# --- 1. REVENUE & UNIT SALES ---
st.subheader("1. iPhone Revenue and Unit Sales Over Time")

fig_sales = make_subplots(specs=[[{"secondary_y": True}]])
fig_sales.add_trace(
    go.Bar(
        x=df["quarter"],
        y=df["iphone_revenue_billion"],
        name="Revenue ($ bn)",
        marker_color="#1f77b4",
        opacity=0.7,
    ),
    secondary_y=False,
)
fig_sales.add_trace(
    go.Scatter(
        x=df["quarter"],
        y=df["iphone_units_million"],
        name="Units (Millions)",
        mode="lines+markers",
        line=dict(color="#e94560", width=2),
        marker=dict(size=6),
    ),
    secondary_y=True,
)
fig_sales.update_layout(
    template="plotly_white",
    height=450,
    **CHART_STYLE
)
fig_sales.update_yaxes(
    title_text="Revenue ($ Billion)",
    title_font=dict(color="#718096", size=15),
    tickfont=dict(color="#718096", size=13),
    secondary_y=False
)
fig_sales.update_yaxes(
    title_text="Units Sold (Millions)",
    title_font=dict(color="#718096", size=15),
    tickfont=dict(color="#718096", size=13),
    secondary_y=True
)
st.plotly_chart(fig_sales, use_container_width=True)

# --- 2. PRICE REACTION ---
st.subheader("2. Stock Price Movement Post-Earnings (30 Days)")

if "price_change_pct" in df.columns:
    colors = ["#2ca02c" if x >= 0 else "#d62728" for x in df["price_change_pct"]]
    fig_reaction = go.Figure()
    fig_reaction.add_trace(
        go.Bar(
            x=df["quarter"],
            y=df["price_change_pct"],
            marker_color=colors,
            text=[f"{v:+.1f}%" for v in df["price_change_pct"]],
            textposition="outside",
        )
    )
    fig_reaction.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_reaction.update_layout(
        yaxis_title="Price Change (%)",
        template="plotly_white",
        height=400,
        **CHART_STYLE
    )
    st.plotly_chart(fig_reaction, use_container_width=True)


# --- 3. CORRELATION ---
st.subheader("3. Correlation Analysis")

clean = df[["iphone_revenue_billion", "iphone_units_million", "price_change_pct"]].dropna()

if len(clean) >= 3:
    rev_pearson_r, rev_pearson_p = pearsonr(clean["iphone_revenue_billion"], clean["price_change_pct"])
    unit_pearson_r, unit_pearson_p = pearsonr(clean["iphone_units_million"], clean["price_change_pct"])

    corr_table = pd.DataFrame([
        {
            "Metric": "iPhone Revenue",
            "Pearson r": f"{rev_pearson_r:.4f}",
            "P-Value": f"{rev_pearson_p:.4f}",
        },
        {
            "Metric": "iPhone Units",
            "Pearson r": f"{unit_pearson_r:.4f}",
            "P-Value": f"{unit_pearson_p:.4f}",
        },
    ])
    st.table(corr_table)

# --- 4. SEASONALITY ---
st.subheader("4. Seasonal Patterns by Fiscal Quarter")

df["fiscal_q"] = df["quarter"].str[:2]
seasonal = df.groupby("fiscal_q").agg(
    avg_revenue=("iphone_revenue_billion", "mean"),
    avg_price_change=("price_change_pct", "mean"),
).reset_index()

fig_seasonal = make_subplots(specs=[[{"secondary_y": True}]])
fig_seasonal.add_trace(
    go.Bar(
        x=seasonal["fiscal_q"],
        y=seasonal["avg_revenue"],
        name="Avg. Revenue ($ bn)",
        marker_color="#1f77b4",
        opacity=0.7,
    ),
    secondary_y=False,
)
fig_seasonal.add_trace(
    go.Scatter(
        x=seasonal["fiscal_q"],
        y=seasonal["avg_price_change"],
        name="Avg. Price Reaction (%)",
        mode="lines+markers",
        line=dict(color="#e94560", width=2),
    ),
    secondary_y=True,
)
fig_seasonal.update_layout(
    template="plotly_white",
    height=400,
    **CHART_STYLE
)
fig_seasonal.update_yaxes(
    title_text="Avg. Revenue ($ Billion)",
    title_font=dict(color="#718096", size=15),
    tickfont=dict(color="#718096", size=13),
    secondary_y=False
)
fig_seasonal.update_yaxes(
    title_text="Avg. Price Reaction (%)",
    title_font=dict(color="#718096", size=15),
    tickfont=dict(color="#718096", size=13),
    secondary_y=True
)
st.plotly_chart(fig_seasonal, use_container_width=True)

# --- 5. KEY FINDINGS ---
st.subheader("5. Key Insights")

positive_rate = (df["price_change_pct"] >= 0).mean() * 100
summary = f"""
**Analysis of {len(df)} Quarters:**

- **Success Rate:** In {positive_rate:.0f}% of quarters, the stock responded positively 30 days after earnings.
- **Seasonality:** Fiscal Q1 (Holiday Quarter) consistently delivers the highest revenues.
- **Statistical Significance:** """

if len(clean) >= 3 and rev_pearson_p < 0.05:
    summary += "There is a statistically significant correlation between iPhone revenue and stock price reaction."
else:
    summary += "The correlation is not statistically significant. This suggests that the market already prices in expectations, and only deviations from these expectations drive the price."

st.markdown(summary)
st.caption("Data source: Apple Investor Relations / Statista. Manual updates required in data/iphone_sales.csv.")