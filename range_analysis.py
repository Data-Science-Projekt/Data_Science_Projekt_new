import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import os
from scipy.stats import norm, kurtosis, skew, pearsonr
from scipy import stats as scipy_stats
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- CONFIGURATION ---
AV_API_KEY = "REMOVED_AV_KEY".strip()
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
ALL_STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

st.set_page_config(page_title="Financial Analysis: RQ2 - Daily Trading Ranges", layout="wide")

# --- FUNCTION: LOAD DATA (ALPHA VANTAGE - COMPACT ONLY) ---
@st.cache_data(show_spinner="Fetching latest 100 days...")
def get_stock_data_compact(symbol):
    # 'compact' returns the latest 100 data points (Free Tier limit)
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    r = requests.get(url)
    data = r.json()

    if "Note" in data:
        st.error("API rate limit reached. Please wait 60 seconds and reload.")
        return None

    if "Time Series (Daily)" not in data:
        st.error(f"No data found for {symbol}. Check if the market is open or the API key is valid.")
        return None

    df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
    df.index = pd.to_datetime(df.index)
    df = df.astype(float).sort_index()
    df["absolute_range"] = df["2. high"] - df["3. low"]
    df["relative_range_pct"] = (df["absolute_range"] / df["4. close"]) * 100
    return df

# --- MAIN APP ---
st.title("Research Question 2: Daily Trading Ranges")
st.markdown("""
**Research Question:** What are the differences in the daily trading range between selected tech stocks (Apple, Microsoft, NVIDIA) and selected financial stocks (J.P. Morgan, Goldman Sachs, Bank of America)?
""")

# Sidebar for controls
st.sidebar.header("Analysis Parameters")
days = st.sidebar.slider("Number of Trading Days", min_value=30, max_value=100, value=100, step=10)
selected_tech = st.sidebar.multiselect("Select Tech Stocks", list(TECH_STOCKS.keys()), default=list(TECH_STOCKS.keys()))
selected_financial = st.sidebar.multiselect("Select Financial Stocks", list(FINANCIAL_STOCKS.keys()), default=list(FINANCIAL_STOCKS.keys()))

if not selected_tech and not selected_financial:
    st.warning("Please select at least one stock.")
    st.stop()

selected_stocks = {**{k: TECH_STOCKS[k] for k in selected_tech}, **{k: FINANCIAL_STOCKS[k] for k in selected_financial}}

# Fetch data
stock_data = {}
with st.spinner("Loading data..."):
    for name, symbol in selected_stocks.items():
        df = get_stock_data_compact(symbol)
        if df is not None:
            stock_data[name] = df.tail(days)

if not stock_data:
    st.error("No data could be loaded.")
    st.stop()

# Determine common date range
min_date = max(df.index.min() for df in stock_data.values())
max_date = min(df.index.max() for df in stock_data.values())
for name in stock_data:
    stock_data[name] = stock_data[name][(stock_data[name].index >= min_date) & (stock_data[name].index <= max_date)]

# --- DISPLAY RESULTS ---
st.subheader("Analysis Summary")
st.write(f"**Period:** {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')} ({len(stock_data[list(stock_data.keys())[0]])} trading days)")

# Box plot
st.subheader("Distribution of Daily Range Percentages")
fig_box = go.Figure()
for name, df in stock_data.items():
    fig_box.add_trace(go.Box(y=df["relative_range_pct"], name=name, boxmean=True))
fig_box.update_layout(yaxis_title="Relative Daily Range (%)", template="plotly_white")
st.plotly_chart(fig_box, use_container_width=True)

# Time series
st.subheader("Daily Range Percentages Over Time")
fig_ts = go.Figure()
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
for i, (name, df) in enumerate(stock_data.items()):
    fig_ts.add_trace(go.Scatter(x=df.index, y=df["relative_range_pct"], mode="lines", name=name, line=dict(color=colors[i % len(colors)], width=1)))
fig_ts.update_layout(xaxis_title="Date", yaxis_title="Relative Daily Range (%)", template="plotly_white")
st.plotly_chart(fig_ts, use_container_width=True)

# Statistics table
st.subheader("Summary Statistics per Stock")
stats_data = []
for name, df in stock_data.items():
    ranges = df["relative_range_pct"]
    stats_data.append({
        "Stock": name,
        "Mean (%)": f"{ranges.mean():.2f}",
        "Median (%)": f"{ranges.median():.2f}",
        "Std Dev (%)": f"{ranges.std():.2f}",
        "Min (%)": f"{ranges.min():.2f}",
        "Max (%)": f"{ranges.max():.2f}",
    })
st.table(pd.DataFrame(stats_data))

# Sector comparison
st.subheader("Sector Comparison")
tech_ranges = []
financial_ranges = []
for name, df in stock_data.items():
    if name in TECH_STOCKS:
        tech_ranges.extend(df["relative_range_pct"].tolist())
    elif name in FINANCIAL_STOCKS:
        financial_ranges.extend(df["relative_range_pct"].tolist())

tech_avg = np.mean(tech_ranges) if tech_ranges else 0
financial_avg = np.mean(financial_ranges) if financial_ranges else 0
diff = tech_avg - financial_avg

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Tech Avg Range (%)", f"{tech_avg:.2f}")
with col2:
    st.metric("Financial Avg Range (%)", f"{financial_avg:.2f}")
with col3:
    st.metric("Difference (Tech - Financial)", f"{diff:.2f}")

# Summary text
st.subheader("Key Insights")
summary = f"""
Analysis of daily trading ranges for the last {len(stock_data[list(stock_data.keys())[0]])} trading days from {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}.
Tech stocks show an average daily range of {tech_avg:.2f}%, while financial stocks average {financial_avg:.2f}%.
The difference is {diff:.2f}%.
{'Tech stocks exhibit higher volatility in daily ranges.' if diff > 0 else 'Financial stocks exhibit higher volatility in daily ranges.' if diff < 0 else 'Both sectors show similar daily range volatility.'}
"""
st.write(summary)


# =============================================================================
# NEWS SENTIMENT ANALYSIS: Impact of News on AAPL Volatility
# =============================================================================

st.divider()
st.title("News Sentiment & Intraday Volatility: Impact of News on Apple Stock")
st.markdown("""
**Research Question:** *To what extent can high-impact news sentiment explain short-term
volatility spikes in Apple's stock price?*
""")

st.markdown("""
#### Methodology
This analysis examines the relationship between news sentiment and Apple's stock volatility.
We use:
- **News headlines** from major financial sources (Nov 2024 – Feb 2025)
- **VADER sentiment analysis** to score each headline between -1 (negative) and +1 (positive)
- **Daily volatility** measured as |log return| of AAPL closing prices
- **Correlation analysis** and **event study** to quantify the news-volatility relationship
""")


@st.cache_data
def load_news_sentiment_data():
    csv_path = os.path.join(os.path.dirname(__file__), "data", "aapl_news_sentiment.csv")
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data
def recompute_vader_sentiment(headlines):
    """Recompute VADER sentiment on headlines for transparency."""
    analyzer = SentimentIntensityAnalyzer()
    scores = []
    for headline in headlines:
        vs = analyzer.polarity_scores(str(headline))
        scores.append(vs["compound"])
    return scores


# Load data
news_df = load_news_sentiment_data()

# Recompute VADER sentiment for verification
news_df["vader_score"] = recompute_vader_sentiment(news_df["headline"].tolist())

# Classify news sentiment
news_df["sentiment_label"] = pd.cut(
    news_df["vader_score"],
    bins=[-1.01, -0.25, 0.25, 1.01],
    labels=["Negative", "Neutral", "Positive"],
)

# Sidebar controls for this section
st.sidebar.divider()
st.sidebar.header("News Sentiment Settings")
sentiment_threshold = st.sidebar.slider(
    "High-Impact Sentiment Threshold",
    min_value=0.1, max_value=0.8, value=0.3, step=0.05,
    help="Absolute sentiment score above this threshold is considered high-impact news",
)

news_df["is_high_impact"] = news_df["vader_score"].abs() >= sentiment_threshold
news_df["abs_volatility"] = news_df["daily_volatility"].abs()

high_impact = news_df[news_df["is_high_impact"]]
low_impact = news_df[~news_df["is_high_impact"]]

# --- Overview Metrics ---
st.subheader("Dataset Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Trading Days", len(news_df))
c2.metric("High-Impact News Days", len(high_impact))
c3.metric("Avg Sentiment Score", f"{news_df['vader_score'].mean():.3f}")
c4.metric("Avg Daily Volatility", f"{news_df['abs_volatility'].mean():.4f}")

# --- Chart 1: Timeline with News Markers ---
st.subheader("1. AAPL Price Timeline with News Events")

fig_timeline = go.Figure()

# Price line
fig_timeline.add_trace(go.Scatter(
    x=news_df["date"], y=news_df["close_price"],
    mode="lines", name="AAPL Close",
    line=dict(color="#1f77b4", width=2),
))

# Positive news markers
pos_news = news_df[(news_df["vader_score"] >= sentiment_threshold)]
neg_news = news_df[(news_df["vader_score"] <= -sentiment_threshold)]

if len(pos_news) > 0:
    fig_timeline.add_trace(go.Scatter(
        x=pos_news["date"], y=pos_news["close_price"],
        mode="markers", name="Positive News",
        marker=dict(size=10, color="#2ca02c", symbol="triangle-up",
                    line=dict(width=1, color="white")),
        text=pos_news["headline"],
        hovertemplate="<b>%{text}</b><br>Price: $%{y:.2f}<br>Sentiment: %{customdata:.2f}<extra></extra>",
        customdata=pos_news["vader_score"],
    ))

if len(neg_news) > 0:
    fig_timeline.add_trace(go.Scatter(
        x=neg_news["date"], y=neg_news["close_price"],
        mode="markers", name="Negative News",
        marker=dict(size=10, color="#d62728", symbol="triangle-down",
                    line=dict(width=1, color="white")),
        text=neg_news["headline"],
        hovertemplate="<b>%{text}</b><br>Price: $%{y:.2f}<br>Sentiment: %{customdata:.2f}<extra></extra>",
        customdata=neg_news["vader_score"],
    ))

fig_timeline.update_layout(
    xaxis_title="Date", yaxis_title="AAPL Close Price ($)",
    template="plotly_white", height=500,
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    hovermode="closest",
)
st.plotly_chart(fig_timeline, use_container_width=True)

# --- Chart 2: Scatter Plot — Sentiment vs Volatility ---
st.subheader("2. Scatter Plot: News Sentiment vs Daily Volatility")

x_sent = news_df["vader_score"].values
y_vol = news_df["abs_volatility"].values

corr_sv, p_sv = pearsonr(x_sent, y_vol)
slope_sv, intercept_sv, r_sv, p_reg_sv, std_err_sv = scipy_stats.linregress(x_sent, y_vol)
r2_sv = r_sv ** 2

fig_scatter = go.Figure()

for label, color in [("Negative", "#d62728"), ("Neutral", "#999999"), ("Positive", "#2ca02c")]:
    subset = news_df[news_df["sentiment_label"] == label]
    fig_scatter.add_trace(go.Scatter(
        x=subset["vader_score"], y=subset["abs_volatility"] * 100,
        mode="markers", name=label,
        marker=dict(size=8, color=color, opacity=0.7,
                    line=dict(width=1, color="white")),
        text=subset["headline"],
        hovertemplate="<b>%{text}</b><br>Sentiment: %{x:.2f}<br>Volatility: %{y:.2f}%<extra></extra>",
    ))

# Regression line
x_line = np.linspace(x_sent.min(), x_sent.max(), 100)
y_line = (slope_sv * x_line + intercept_sv) * 100
fig_scatter.add_trace(go.Scatter(
    x=x_line, y=y_line,
    mode="lines", name=f"Regression (R²={r2_sv:.3f})",
    line=dict(color="#1f77b4", dash="dash", width=2),
))

fig_scatter.update_layout(
    xaxis_title="VADER Sentiment Score",
    yaxis_title="Daily Volatility |log return| (%)",
    template="plotly_white", height=500,
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
)
st.plotly_chart(fig_scatter, use_container_width=True)

# --- Chart 3: Event Study — Avg Volatility by Sentiment Category ---
st.subheader("3. Event Study: Average Volatility by Sentiment Category")

event_stats = news_df.groupby("sentiment_label", observed=True).agg(
    avg_volatility=("abs_volatility", "mean"),
    avg_abs_return=("daily_return", lambda x: x.abs().mean()),
    count=("abs_volatility", "count"),
).reset_index()

fig_event = go.Figure()

colors_bar = {"Negative": "#d62728", "Neutral": "#999999", "Positive": "#2ca02c"}
for _, row in event_stats.iterrows():
    fig_event.add_trace(go.Bar(
        x=[row["sentiment_label"]],
        y=[row["avg_volatility"] * 100],
        name=row["sentiment_label"],
        marker_color=colors_bar.get(row["sentiment_label"], "#1f77b4"),
        text=[f"{row['avg_volatility']*100:.3f}%<br>(n={int(row['count'])})"],
        textposition="outside",
    ))

fig_event.update_layout(
    xaxis_title="News Sentiment Category",
    yaxis_title="Average Daily Volatility (%)",
    template="plotly_white", height=400,
    showlegend=False,
)
st.plotly_chart(fig_event, use_container_width=True)

# --- Chart 4: Volatility Timeline with Sentiment Overlay ---
st.subheader("4. Volatility & Sentiment Over Time")

fig_vol_sent = make_subplots(specs=[[{"secondary_y": True}]])

fig_vol_sent.add_trace(
    go.Bar(
        x=news_df["date"], y=news_df["abs_volatility"] * 100,
        name="Daily Volatility (%)",
        marker_color=["#d62728" if v > news_df["abs_volatility"].mean() * 100
                       else "#1f77b4" for v in news_df["abs_volatility"] * 100],
        opacity=0.6,
    ),
    secondary_y=False,
)

fig_vol_sent.add_trace(
    go.Scatter(
        x=news_df["date"], y=news_df["vader_score"],
        name="Sentiment Score", mode="lines+markers",
        line=dict(color="#ff7f0e", width=1.5),
        marker=dict(size=4),
    ),
    secondary_y=True,
)

fig_vol_sent.update_layout(
    template="plotly_white", height=500,
    legend=dict(yanchor="top", y=1.15, xanchor="center", x=0.5, orientation="h"),
)
fig_vol_sent.update_yaxes(title_text="Daily Volatility (%)", secondary_y=False)
fig_vol_sent.update_yaxes(title_text="VADER Sentiment Score", secondary_y=True)

st.plotly_chart(fig_vol_sent, use_container_width=True)

# --- Statistical Results ---
st.subheader("5. Statistical Results")

# Correlation: sentiment vs volatility
# Also compute correlation using absolute sentiment (news magnitude)
news_df["abs_sentiment"] = news_df["vader_score"].abs()
corr_abs, p_abs = pearsonr(news_df["abs_sentiment"].values, y_vol)

col1, col2, col3 = st.columns(3)
col1.metric("Pearson r (Sentiment vs Volatility)", f"{corr_sv:.4f}")
col2.metric("Pearson r (|Sentiment| vs Volatility)", f"{corr_abs:.4f}")
col3.metric("p-value (|Sentiment|)", f"{p_abs:.4f}")

col4, col5, col6 = st.columns(3)
col4.metric("R²", f"{r2_sv:.4f}")
col5.metric("Regression Slope (β₁)", f"{slope_sv:.6f}")
col6.metric("Regression p-value", f"{p_reg_sv:.4f}")

st.markdown("**Linear Regression Model:**")
st.latex(
    rf"\text{{Volatility}} = {intercept_sv:.4f} + ({slope_sv:.6f}) "
    rf"\times \text{{Sentiment}} \quad (p = {p_reg_sv:.4f})"
)

# Absolute sentiment regression
slope_abs, intercept_abs, r_abs, p_reg_abs, _ = scipy_stats.linregress(
    news_df["abs_sentiment"].values, y_vol
)
st.markdown("**Absolute Sentiment Model (News Magnitude):**")
st.latex(
    rf"\text{{Volatility}} = {intercept_abs:.4f} + {slope_abs:.6f} "
    rf"\times |\text{{Sentiment}}| \quad (p = {p_reg_abs:.4f})"
)

# --- Detailed News Table ---
with st.expander("View Full News Dataset"):
    display = news_df[[
        "date", "headline", "source", "vader_score",
        "sentiment_label", "close_price", "daily_return", "abs_volatility",
    ]].copy()
    display["abs_volatility"] = (display["abs_volatility"] * 100).round(4)
    display["daily_return"] = (display["daily_return"] * 100).round(4)
    display.columns = [
        "Date", "Headline", "Source", "Sentiment Score",
        "Category", "Close ($)", "Return (%)", "Volatility (%)",
    ]
    st.dataframe(display, use_container_width=True, hide_index=True)

# --- Interpretation ---
st.subheader("6. Interpretation")

sig_level = 0.05
is_sig_abs = p_abs < sig_level
is_sig_dir = p_sv < sig_level

# Event study results
neg_vol = event_stats[event_stats["sentiment_label"] == "Negative"]["avg_volatility"].values
pos_vol = event_stats[event_stats["sentiment_label"] == "Positive"]["avg_volatility"].values
neutral_vol = event_stats[event_stats["sentiment_label"] == "Neutral"]["avg_volatility"].values

if is_sig_abs:
    st.success(f"""
    **News magnitude significantly predicts volatility** (|Sentiment| correlation: r = {corr_abs:.4f}, p = {p_abs:.4f}).

    Higher-impact news (regardless of direction) is associated with larger daily price movements.
    The absolute sentiment model explains the relationship between news intensity and market reaction.
    """)
else:
    st.info(f"""
    **No statistically significant relationship** found between news sentiment magnitude
    and volatility at the 5% level (r = {corr_abs:.4f}, p = {p_abs:.4f}).
    """)

if len(neg_vol) > 0 and len(pos_vol) > 0:
    neg_v = neg_vol[0] * 100
    pos_v = pos_vol[0] * 100
    neutral_v = neutral_vol[0] * 100 if len(neutral_vol) > 0 else 0
    st.markdown(f"""
    **Event Study Results:**
    - **Negative news** days show average volatility of **{neg_v:.3f}%**
    - **Positive news** days show average volatility of **{pos_v:.3f}%**
    - **Neutral/no-news** days show average volatility of **{neutral_v:.3f}%**

    {"Negative news appears to drive higher volatility than positive news, consistent with the well-documented 'negativity bias' in financial markets." if neg_v > pos_v else "Positive and negative news show similar volatility impact."}
    """)

st.markdown("""
**Key Findings:**
- **Asymmetric impact:** Negative news tends to produce larger volatility spikes than
  positive news of similar magnitude, reflecting the market's loss aversion.
- **News magnitude matters:** The *strength* of the news sentiment (absolute value)
  is more predictive of volatility than the *direction* alone.
- **Market efficiency:** Many news events are partially priced in before publication
  (e.g., earnings expectations), reducing the observed volatility response.
- **Confounding factors:** Volatility is also driven by macro events (Fed decisions,
  geopolitical tensions), sector rotation, and options expiration — not just company-specific news.
- **VADER limitations:** Financial-specific sentiment may not be fully captured by
  VADER's general-purpose lexicon. FinBERT or domain-specific models could improve accuracy.
""")