import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import pearsonr, spearmanr
import os

# --- LOAD DATA ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@st.cache_data
def load_iphone_sales():
    path = os.path.join(DATA_DIR, "iphone_sales.csv")
    df = pd.read_csv(path, parse_dates=["earnings_date"])
    df = df.sort_values("earnings_date").reset_index(drop=True)
    df["price_change_pct"] = (
        (df["price_30d_after"] - df["price_on_earnings"]) / df["price_on_earnings"] * 100
    )
    df["revenue_growth"] = df["iphone_revenue_billion"].pct_change() * 100
    df["units_growth"] = df["iphone_units_million"].pct_change() * 100
    return df


# --- MAIN PAGE ---
st.title("Research Question 9: Company Fundamentals")
st.markdown("""
**Research Question:** How do iPhone sales figures impact Apple's long-term stock performance?
Do quarterly earnings surprises in the iPhone segment drive post-earnings price movements?
""")

st.markdown("""
#### Methodology
- **iPhone unit sales & revenue** from Apple's quarterly earnings reports (Q1 2019 – present)
- **Stock price** on earnings day vs. 30 days after earnings
- **Correlation analysis** between iPhone revenue/units and stock price reactions
- **Trend analysis** across fiscal quarters to identify seasonal patterns
""")

df = load_iphone_sales()

if df.empty:
    st.error("Could not load iPhone sales data.")
    st.stop()

st.write(f"**Period:** {df['quarter'].iloc[0]} to {df['quarter'].iloc[-1]} ({len(df)} quarters)")

# --- 1. iPhone Revenue & Units Over Time ---
st.subheader("1. iPhone Revenue & Unit Sales Over Time")

fig_sales = make_subplots(specs=[[{"secondary_y": True}]])
fig_sales.add_trace(
    go.Bar(
        x=df["quarter"],
        y=df["iphone_revenue_billion"],
        name="Revenue ($B)",
        marker_color="#1f77b4",
        opacity=0.7,
    ),
    secondary_y=False,
)
fig_sales.add_trace(
    go.Scatter(
        x=df["quarter"],
        y=df["iphone_units_million"],
        name="Units (M)",
        mode="lines+markers",
        line=dict(color="#e94560", width=2),
        marker=dict(size=6),
    ),
    secondary_y=True,
)
fig_sales.update_layout(template="plotly_white", height=450)
fig_sales.update_yaxes(title_text="Revenue ($B)", secondary_y=False)
fig_sales.update_yaxes(title_text="Units Sold (M)", secondary_y=True)
st.plotly_chart(fig_sales, use_container_width=True)

# --- 2. Stock Price Reaction to Earnings ---
st.subheader("2. Post-Earnings Stock Price Movement (30-Day)")

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
)
st.plotly_chart(fig_reaction, use_container_width=True)

# --- 3. Revenue vs Price Change Scatter ---
st.subheader("3. iPhone Revenue vs Post-Earnings Price Change")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Revenue vs Price Reaction**")
    fig_scatter1 = go.Figure()
    fig_scatter1.add_trace(
        go.Scatter(
            x=df["iphone_revenue_billion"],
            y=df["price_change_pct"],
            mode="markers+text",
            text=df["quarter"],
            textposition="top center",
            textfont=dict(size=8),
            marker=dict(size=10, color="#1f77b4", opacity=0.7),
        )
    )
    # Trendline
    mask = df[["iphone_revenue_billion", "price_change_pct"]].dropna()
    if len(mask) > 2:
        z = np.polyfit(mask["iphone_revenue_billion"], mask["price_change_pct"], 1)
        p = np.poly1d(z)
        x_range = np.linspace(mask["iphone_revenue_billion"].min(), mask["iphone_revenue_billion"].max(), 50)
        fig_scatter1.add_trace(
            go.Scatter(
                x=x_range, y=p(x_range),
                mode="lines", name="Trendline",
                line=dict(color="gray", dash="dash"),
            )
        )
    fig_scatter1.update_layout(
        xaxis_title="iPhone Revenue ($B)",
        yaxis_title="30-Day Price Change (%)",
        template="plotly_white",
        height=400,
        showlegend=False,
    )
    st.plotly_chart(fig_scatter1, use_container_width=True)

with col2:
    st.markdown("**Unit Sales vs Price Reaction**")
    fig_scatter2 = go.Figure()
    fig_scatter2.add_trace(
        go.Scatter(
            x=df["iphone_units_million"],
            y=df["price_change_pct"],
            mode="markers+text",
            text=df["quarter"],
            textposition="top center",
            textfont=dict(size=8),
            marker=dict(size=10, color="#e94560", opacity=0.7),
        )
    )
    mask2 = df[["iphone_units_million", "price_change_pct"]].dropna()
    if len(mask2) > 2:
        z2 = np.polyfit(mask2["iphone_units_million"], mask2["price_change_pct"], 1)
        p2 = np.poly1d(z2)
        x_range2 = np.linspace(mask2["iphone_units_million"].min(), mask2["iphone_units_million"].max(), 50)
        fig_scatter2.add_trace(
            go.Scatter(
                x=x_range2, y=p2(x_range2),
                mode="lines", name="Trendline",
                line=dict(color="gray", dash="dash"),
            )
        )
    fig_scatter2.update_layout(
        xaxis_title="iPhone Units Sold (M)",
        yaxis_title="30-Day Price Change (%)",
        template="plotly_white",
        height=400,
        showlegend=False,
    )
    st.plotly_chart(fig_scatter2, use_container_width=True)

# --- 4. Correlation Statistics ---
st.subheader("4. Correlation Analysis")

clean = df[["iphone_revenue_billion", "iphone_units_million", "price_change_pct"]].dropna()

if len(clean) >= 3:
    rev_pearson_r, rev_pearson_p = pearsonr(clean["iphone_revenue_billion"], clean["price_change_pct"])
    rev_spearman_r, rev_spearman_p = spearmanr(clean["iphone_revenue_billion"], clean["price_change_pct"])
    unit_pearson_r, unit_pearson_p = pearsonr(clean["iphone_units_million"], clean["price_change_pct"])
    unit_spearman_r, unit_spearman_p = spearmanr(clean["iphone_units_million"], clean["price_change_pct"])

    corr_table = pd.DataFrame([
        {
            "Metric": "iPhone Revenue",
            "Pearson r": f"{rev_pearson_r:.4f}",
            "Pearson p-value": f"{rev_pearson_p:.4f}",
            "Spearman r": f"{rev_spearman_r:.4f}",
            "Spearman p-value": f"{rev_spearman_p:.4f}",
        },
        {
            "Metric": "iPhone Units",
            "Pearson r": f"{unit_pearson_r:.4f}",
            "Pearson p-value": f"{unit_pearson_p:.4f}",
            "Spearman r": f"{unit_spearman_r:.4f}",
            "Spearman p-value": f"{unit_spearman_p:.4f}",
        },
    ])
    st.table(corr_table)

# --- 5. Seasonal Pattern ---
st.subheader("5. Seasonal Pattern by Fiscal Quarter")

df["fiscal_q"] = df["quarter"].str[:2]
seasonal = df.groupby("fiscal_q").agg(
    avg_revenue=("iphone_revenue_billion", "mean"),
    avg_units=("iphone_units_million", "mean"),
    avg_price_change=("price_change_pct", "mean"),
).reset_index()

fig_seasonal = make_subplots(specs=[[{"secondary_y": True}]])
fig_seasonal.add_trace(
    go.Bar(
        x=seasonal["fiscal_q"],
        y=seasonal["avg_revenue"],
        name="Avg Revenue ($B)",
        marker_color="#1f77b4",
        opacity=0.7,
    ),
    secondary_y=False,
)
fig_seasonal.add_trace(
    go.Scatter(
        x=seasonal["fiscal_q"],
        y=seasonal["avg_price_change"],
        name="Avg 30-Day Price Change (%)",
        mode="lines+markers",
        line=dict(color="#e94560", width=2),
        marker=dict(size=10),
    ),
    secondary_y=True,
)
fig_seasonal.update_layout(template="plotly_white", height=400)
fig_seasonal.update_yaxes(title_text="Avg Revenue ($B)", secondary_y=False)
fig_seasonal.update_yaxes(title_text="Avg Price Change (%)", secondary_y=True)
st.plotly_chart(fig_seasonal, use_container_width=True)

# --- 6. Key Insights ---
st.subheader("6. Key Insights")

avg_positive = df[df["price_change_pct"] >= 0]["price_change_pct"].mean()
avg_negative = df[df["price_change_pct"] < 0]["price_change_pct"].mean()
positive_pct = (df["price_change_pct"] >= 0).mean() * 100

best_q = seasonal.loc[seasonal["avg_revenue"].idxmax(), "fiscal_q"]
best_q_rev = seasonal.loc[seasonal["avg_revenue"].idxmax(), "avg_revenue"]

summary = f"""
**Analysis of {len(df)} quarters** from {df['quarter'].iloc[0]} to {df['quarter'].iloc[-1]}:

- **Post-earnings positive rate:** {positive_pct:.0f}% of quarters saw a positive 30-day price move
- **Avg positive move:** +{avg_positive:.1f}% | **Avg negative move:** {avg_negative:.1f}%
- **Strongest quarter:** {best_q} (avg revenue ${best_q_rev:.1f}B) — typically the holiday quarter
"""

if len(clean) >= 3:
    summary += f"\n- **Revenue ↔ Price correlation:** Pearson r = {rev_pearson_r:.4f} (p = {rev_pearson_p:.4f})"
    summary += f"\n- **Units ↔ Price correlation:** Pearson r = {unit_pearson_r:.4f} (p = {unit_pearson_p:.4f})"

    if rev_pearson_p < 0.05:
        summary += "\n\nThere is a **statistically significant** relationship between iPhone revenue and Apple's post-earnings stock movement."
    else:
        summary += "\n\nThe relationship between iPhone revenue and stock price reaction is **not statistically significant** — suggesting that the market prices in expected sales beforehand, and only surprises vs. expectations drive the stock."

st.markdown(summary)
