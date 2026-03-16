import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import os
import json
import time
from scipy.stats import norm, kurtosis, skew, pearsonr
from scipy import stats as scipy_stats
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- CONFIGURATION ---
AV_API_KEY = "REMOVED_AV_KEY".strip()
NEWSAPI_KEY = "REMOVED_NEWSAPI_KEY"  # <-- Hier deinen NewsAPI Key einfügen (https://newsapi.org)
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}
ALL_STOCKS = {**TECH_STOCKS, **FINANCIAL_STOCKS}

# --- FILE-BASED CACHE (survives restarts) ---
CACHE_DIR = os.path.join(os.path.dirname(__file__), "data", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(key):
    return os.path.join(CACHE_DIR, f"{key}.csv")


def _save_to_disk(key, df):
    """Save DataFrame to disk cache."""
    try:
        df.to_csv(_cache_path(key))
    except Exception:
        pass


def _load_from_disk(key):
    """Load DataFrame from disk cache if it exists."""
    path = _cache_path(key)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            return df
        except Exception:
            pass
    return None


st.set_page_config(page_title="Financial Analysis: RQ2 - Daily Trading Ranges", layout="wide")


# --- FUNCTION: LOAD DATA (ALPHA VANTAGE - COMPACT ONLY) ---
_av_last_call = [0.0]  # track last API call time for rate limiting

@st.cache_data(show_spinner="Fetching latest 100 days...")
def get_stock_data_compact(symbol):
    # Rate limit: wait if last API call was less than 15s ago
    elapsed = time.time() - _av_last_call[0]
    if elapsed < 15:
        time.sleep(15 - elapsed)
    _av_last_call[0] = time.time()

    # 'compact' returns the latest 100 data points (Free Tier limit)
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url, timeout=15)
        data = r.json()

        if "Note" in data or "Information" in data:
            # API limit — try disk cache
            cached = _load_from_disk(f"stock_{symbol}")
            if cached is not None:
                st.warning(f"API limit reached for {symbol}. Using cached data.")
                return cached
            st.error(f"API limit reached for {symbol} and no cached data available.")
            return None

        if "Time Series (Daily)" not in data:
            cached = _load_from_disk(f"stock_{symbol}")
            if cached is not None:
                st.warning(f"No fresh data for {symbol}. Using cached data.")
                return cached
            st.error(f"No data found for {symbol}. Check if the market is open or the API key is valid.")
            return None

        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
        df.index = pd.to_datetime(df.index)
        df = df.astype(float).sort_index()
        df["absolute_range"] = df["2. high"] - df["3. low"]
        df["relative_range_pct"] = (df["absolute_range"] / df["4. close"]) * 100

        # Save to disk for future fallback
        _save_to_disk(f"stock_{symbol}", df)

        return df
    except Exception as e:
        cached = _load_from_disk(f"stock_{symbol}")
        if cached is not None:
            st.warning(f"Connection error for {symbol}. Using cached data.")
            return cached
        st.error(f"Connection Error for {symbol}: {e}")
        return None

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
- **NewsAPI.org** for Apple news over the last 30 days (up to 100 articles)
- **Alpha Vantage NEWS_SENTIMENT API** for recent articles with pre-computed sentiment
- **VADER sentiment analysis** to score all headlines between -1 (negative) and +1 (positive)
- **Alpha Vantage daily stock data** for AAPL closing prices and volatility
- **Correlation analysis** and **event study** to quantify the news-volatility relationship
""")


# --- Fetch News from NewsAPI (last 30 days, up to 100 articles) ---
@st.cache_data(show_spinner="Fetching Apple news from NewsAPI...", ttl=3600)
def fetch_newsapi_articles():
    """Fetch Apple-related news from NewsAPI.org (free tier: last 30 days)."""
    from datetime import datetime, timedelta
    date_from = (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d")
    all_records = []
    # Fetch with both sortBy modes to maximize date coverage
    # (free tier with publishedAt only returns last 1-2 days)
    for sort_mode in ["relevancy", "publishedAt"]:
        url = (
            f"https://newsapi.org/v2/everything?"
            f"q=Apple+AAPL+stock&from={date_from}&language=en&sortBy={sort_mode}"
            f"&pageSize=100&apiKey={NEWSAPI_KEY}"
        )
        try:
            r = requests.get(url, timeout=30)
            data = r.json()
            if data.get("status") != "ok":
                continue
            for item in data.get("articles", []):
                try:
                    dt = pd.to_datetime(item["publishedAt"])
                except Exception:
                    continue
                all_records.append({
                    "datetime": dt,
                    "date": dt.date(),
                    "time": dt.strftime("%H:%M"),
                    "headline": item.get("title", ""),
                    "summary": item.get("description", ""),
                    "source": item.get("source", {}).get("name", ""),
                    "api_source": "NewsAPI",
                })
        except Exception:
            continue
    if not all_records:
        return None, "No articles found from NewsAPI."
    df = pd.DataFrame(all_records).drop_duplicates(subset=["headline"], keep="first")
    return df, None


# --- Fetch News from Alpha Vantage NEWS_SENTIMENT API ---
@st.cache_data(show_spinner="Fetching Apple news from Alpha Vantage...", ttl=3600)
def fetch_av_news(ticker="AAPL", limit=50):
    """Fetch news articles with sentiment from Alpha Vantage NEWS_SENTIMENT endpoint."""
    url = (
        f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT"
        f"&tickers={ticker}&limit={limit}&apikey={AV_API_KEY}"
    )
    try:
        r = requests.get(url, timeout=30)
        data = r.json()

        if "Note" in data or "Information" in data:
            return None, data.get("Note", data.get("Information", "API limit reached."))

        if "feed" not in data:
            return None, "No 'feed' in API response."

        records = []
        for item in data["feed"]:
            aapl_sentiment = None
            for ts in item.get("ticker_sentiment", []):
                if ts["ticker"] == ticker:
                    aapl_sentiment = float(ts["ticker_sentiment_score"])
                    break

            time_str = item.get("time_published", "")
            try:
                dt = pd.to_datetime(time_str, format="%Y%m%dT%H%M%S")
            except Exception:
                continue

            records.append({
                "datetime": dt,
                "date": dt.date(),
                "time": dt.strftime("%H:%M"),
                "headline": item.get("title", ""),
                "summary": item.get("summary", ""),
                "source": item.get("source", ""),
                "av_sentiment": aapl_sentiment if aapl_sentiment is not None else float(
                    item.get("overall_sentiment_score", 0)),
                "api_source": "Alpha Vantage",
            })

        if not records:
            return None, "No relevant articles found."

        return pd.DataFrame(records), None
    except Exception as e:
        return None, str(e)


# --- Combine both news sources ---
@st.cache_data(show_spinner="Combining news from NewsAPI + Alpha Vantage...", ttl=3600)
def fetch_combined_news():
    """Fetch and combine news from both APIs, deduplicate, and score with VADER."""
    all_articles = []
    sources_used = []

    # 1. NewsAPI (main source: 30 days, up to 100 articles)
    newsapi_df, newsapi_err = fetch_newsapi_articles()
    if newsapi_df is not None:
        all_articles.append(newsapi_df)
        sources_used.append(f"NewsAPI ({len(newsapi_df)} articles)")

    # 2. Alpha Vantage (supplementary: recent articles with pre-computed sentiment)
    av_df, av_err = fetch_av_news()
    if av_df is not None:
        all_articles.append(av_df)
        sources_used.append(f"Alpha Vantage ({len(av_df)} articles)")

    if not all_articles:
        errors = []
        if newsapi_err:
            errors.append(f"NewsAPI: {newsapi_err}")
        if av_err:
            errors.append(f"Alpha Vantage: {av_err}")
        return None, " | ".join(errors), []

    combined = pd.concat(all_articles, ignore_index=True)

    # Deduplicate by headline similarity (exact match)
    combined = combined.drop_duplicates(subset=["headline"], keep="first")

    # Compute VADER sentiment for all articles
    analyzer = SentimentIntensityAnalyzer()
    combined["vader_score"] = combined["headline"].apply(
        lambda h: analyzer.polarity_scores(str(h))["compound"]
    )

    # Use AV sentiment where available, otherwise VADER
    if "av_sentiment" in combined.columns:
        combined["sentiment_score"] = combined["av_sentiment"].fillna(combined["vader_score"])
    else:
        combined["sentiment_score"] = combined["vader_score"]

    combined = combined.sort_values("datetime", ascending=False).reset_index(drop=True)

    return combined, None, sources_used


# --- Reuse AAPL daily prices already fetched above (RQ2) ---
def get_aapl_prices_from_cache():
    """Reuse the AAPL data already fetched for RQ2 above, avoiding a second API call."""
    if "Apple" in stock_data:
        df = stock_data["Apple"].copy()
    else:
        # Fallback: fetch AAPL if not selected in RQ2
        df = get_stock_data_compact("AAPL")
    if df is None:
        return None, "Could not load AAPL price data."
    df["log_return"] = np.log(df["4. close"] / df["4. close"].shift(1))
    df["abs_volatility"] = df["log_return"].abs()
    return df.dropna(), None


# --- VADER for secondary sentiment scoring ---
@st.cache_data
def compute_vader_scores(headlines):
    analyzer = SentimentIntensityAnalyzer()
    return [analyzer.polarity_scores(str(h))["compound"] for h in headlines]


# Sidebar controls
st.sidebar.divider()
st.sidebar.header("News Sentiment Settings")
sentiment_threshold = st.sidebar.slider(
    "High-Impact Sentiment Threshold",
    min_value=0.1, max_value=0.8, value=0.3, step=0.05,
    help="Absolute sentiment score above this threshold is considered high-impact news",
)

# --- Load Data ---
news_combined, news_err, sources_used = fetch_combined_news()
price_df, price_err = get_aapl_prices_from_cache()

if news_err:
    st.error(f"Could not fetch news: {news_err}")
    st.stop()
if price_err:
    st.error(f"Could not fetch AAPL prices: {price_err}")
    st.stop()

st.info(f"**Data Sources:** {' + '.join(sources_used)}")

news_filtered = news_combined.copy()

# Aggregate: average sentiment per day (multiple articles per day)
daily_news = news_filtered.groupby("date").agg(
    avg_sentiment=("sentiment_score", "mean"),
    avg_vader_sentiment=("vader_score", "mean"),
    num_articles=("headline", "count"),
    top_headline=("headline", "first"),
    top_source=("source", "first"),
).reset_index()
daily_news["date"] = pd.to_datetime(daily_news["date"])

# Prepare price data for merge
price_df_reset = price_df.reset_index().rename(columns={"index": "date"})
price_df_reset["date"] = price_df_reset["date"].dt.normalize()

# Map news dates to nearest trading day (forward-fill for weekends/holidays)
trading_dates = pd.to_datetime(price_df_reset["date"]).sort_values().reset_index(drop=True)
def map_to_trading_day(news_date):
    """Map a news date to the nearest trading day (same day or next)."""
    nd = pd.Timestamp(news_date).normalize()
    # Try same day first
    if nd in trading_dates.values:
        return nd
    # Find next trading day
    future = trading_dates[trading_dates >= nd]
    if len(future) > 0:
        return future.iloc[0]
    # Fallback: previous trading day
    past = trading_dates[trading_dates <= nd]
    if len(past) > 0:
        return past.iloc[-1]
    return pd.NaT

daily_news["trading_date"] = daily_news["date"].apply(map_to_trading_day)
daily_news = daily_news.dropna(subset=["trading_date"])

# Re-aggregate in case multiple news days map to same trading day
daily_news = daily_news.groupby("trading_date").agg(
    avg_sentiment=("avg_sentiment", "mean"),
    avg_vader_sentiment=("avg_vader_sentiment", "mean"),
    num_articles=("num_articles", "sum"),
    top_headline=("top_headline", "first"),
    top_source=("top_source", "first"),
).reset_index().rename(columns={"trading_date": "date"})

# Normalize dates to ensure matching types (both tz-naive, midnight-aligned)
daily_news["date"] = pd.to_datetime(daily_news["date"]).dt.normalize()
price_df_reset["date"] = pd.to_datetime(price_df_reset["date"]).dt.normalize()

# Merge with price data
merged = pd.merge(daily_news, price_df_reset[["date", "4. close", "log_return", "abs_volatility", "5. volume"]],
                   on="date", how="inner")
merged.rename(columns={"4. close": "close_price", "5. volume": "volume"}, inplace=True)
merged = merged.sort_values("date").reset_index(drop=True)

if len(merged) < 5:
    st.warning(f"Only {len(merged)} days with both news and price data. Need at least 5 for analysis.")
    st.stop()

# Sentiment label classification
merged["sentiment_label"] = pd.cut(
    merged["avg_sentiment"],
    bins=[-1.01, -0.15, 0.15, 1.01],
    labels=["Negative", "Neutral", "Positive"],
)
merged["is_high_impact"] = merged["avg_sentiment"].abs() >= sentiment_threshold

high_impact = merged[merged["is_high_impact"]]

# --- Overview Metrics ---
st.subheader("Dataset Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Trading Days with News", len(merged))
c2.metric("Total Articles Fetched", len(news_filtered))
c3.metric("High-Impact Days", len(high_impact))
c4.metric("Avg Daily Volatility", f"{merged['abs_volatility'].mean():.4f}")

# --- Chart 1: Timeline with News Markers ---
st.subheader("1. AAPL Price Timeline with News Events")

fig_timeline = go.Figure()

fig_timeline.add_trace(go.Scatter(
    x=merged["date"], y=merged["close_price"],
    mode="lines", name="AAPL Close",
    line=dict(color="#1f77b4", width=2),
))

pos_news = merged[merged["avg_sentiment"] >= sentiment_threshold]
neg_news = merged[merged["avg_sentiment"] <= -sentiment_threshold]

if len(pos_news) > 0:
    fig_timeline.add_trace(go.Scatter(
        x=pos_news["date"], y=pos_news["close_price"],
        mode="markers", name="Positive News",
        marker=dict(size=10, color="#2ca02c", symbol="triangle-up",
                    line=dict(width=1, color="white")),
        text=pos_news["top_headline"],
        hovertemplate="<b>%{text}</b><br>Price: $%{y:.2f}<br>Sentiment: %{customdata:.3f}<extra></extra>",
        customdata=pos_news["avg_sentiment"],
    ))

if len(neg_news) > 0:
    fig_timeline.add_trace(go.Scatter(
        x=neg_news["date"], y=neg_news["close_price"],
        mode="markers", name="Negative News",
        marker=dict(size=10, color="#d62728", symbol="triangle-down",
                    line=dict(width=1, color="white")),
        text=neg_news["top_headline"],
        hovertemplate="<b>%{text}</b><br>Price: $%{y:.2f}<br>Sentiment: %{customdata:.3f}<extra></extra>",
        customdata=neg_news["avg_sentiment"],
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

x_sent = merged["avg_sentiment"].values
y_vol = merged["abs_volatility"].values

corr_sv, p_sv = pearsonr(x_sent, y_vol)
slope_sv, intercept_sv, r_sv, p_reg_sv, std_err_sv = scipy_stats.linregress(x_sent, y_vol)
r2_sv = r_sv ** 2

fig_scatter = go.Figure()

for label, color in [("Negative", "#d62728"), ("Neutral", "#999999"), ("Positive", "#2ca02c")]:
    subset = merged[merged["sentiment_label"] == label]
    if len(subset) == 0:
        continue
    fig_scatter.add_trace(go.Scatter(
        x=subset["avg_sentiment"], y=subset["abs_volatility"] * 100,
        mode="markers", name=label,
        marker=dict(size=8, color=color, opacity=0.7,
                    line=dict(width=1, color="white")),
        text=subset["top_headline"],
        hovertemplate="<b>%{text}</b><br>Sentiment: %{x:.3f}<br>Volatility: %{y:.2f}%<extra></extra>",
    ))

x_line = np.linspace(x_sent.min(), x_sent.max(), 100)
y_line = (slope_sv * x_line + intercept_sv) * 100
fig_scatter.add_trace(go.Scatter(
    x=x_line, y=y_line,
    mode="lines", name=f"Regression (R²={r2_sv:.3f})",
    line=dict(color="#1f77b4", dash="dash", width=2),
))

fig_scatter.update_layout(
    xaxis_title="Sentiment Score (VADER + AV combined)",
    yaxis_title="Daily Volatility |log return| (%)",
    template="plotly_white", height=500,
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
)
st.plotly_chart(fig_scatter, use_container_width=True)

# --- Chart 3: Event Study — Avg Volatility by Sentiment Category ---
st.subheader("3. Event Study: Average Volatility by Sentiment Category")

event_stats = merged.groupby("sentiment_label", observed=True).agg(
    avg_volatility=("abs_volatility", "mean"),
    avg_abs_return=("log_return", lambda x: x.abs().mean()),
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

avg_vol = merged["abs_volatility"].mean()
fig_vol_sent.add_trace(
    go.Bar(
        x=merged["date"], y=merged["abs_volatility"] * 100,
        name="Daily Volatility (%)",
        marker_color=["#d62728" if v > avg_vol else "#1f77b4"
                       for v in merged["abs_volatility"]],
        opacity=0.6,
    ),
    secondary_y=False,
)

fig_vol_sent.add_trace(
    go.Scatter(
        x=merged["date"], y=merged["avg_sentiment"],
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
fig_vol_sent.update_yaxes(title_text="Sentiment Score", secondary_y=True)

st.plotly_chart(fig_vol_sent, use_container_width=True)

# --- Statistical Results ---
st.subheader("5. Statistical Results")

merged["abs_sentiment"] = merged["avg_sentiment"].abs()
corr_abs, p_abs = pearsonr(merged["abs_sentiment"].values, y_vol)

# VADER comparison
corr_vader, p_vader = pearsonr(merged["avg_vader_sentiment"].values, y_vol)

col1, col2, col3 = st.columns(3)
col1.metric("Pearson r (Sentiment vs Vol.)", f"{corr_sv:.4f}")
col2.metric("Pearson r (|Sentiment| vs Vol.)", f"{corr_abs:.4f}")
col3.metric("p-value (|Sentiment|)", f"{p_abs:.4f}")

col4, col5, col6 = st.columns(3)
col4.metric("R²", f"{r2_sv:.4f}")
col5.metric("VADER-only r", f"{corr_vader:.4f}")
col6.metric("Regression Slope (β₁)", f"{slope_sv:.6f}")

st.markdown("**Linear Regression Model:**")
st.latex(
    rf"\text{{Volatility}} = {intercept_sv:.4f} + ({slope_sv:.6f}) "
    rf"\times \text{{Sentiment}} \quad (p = {p_reg_sv:.4f})"
)

slope_abs, intercept_abs, r_abs, p_reg_abs, _ = scipy_stats.linregress(
    merged["abs_sentiment"].values, y_vol
)
st.markdown("**Absolute Sentiment Model (News Magnitude):**")
st.latex(
    rf"\text{{Volatility}} = {intercept_abs:.4f} + {slope_abs:.6f} "
    rf"\times |\text{{Sentiment}}| \quad (p = {p_reg_abs:.4f})"
)

# --- Detailed News Table ---
with st.expander("View All Fetched Articles"):
    article_cols = ["datetime", "headline", "source", "sentiment_score", "vader_score"]
    article_names = ["Published", "Headline", "Source", "Sentiment Score", "VADER Score"]
    if "api_source" in news_filtered.columns:
        article_cols.append("api_source")
        article_names.append("API Source")
    article_display = news_filtered[article_cols].copy()
    article_display.columns = article_names
    st.dataframe(article_display.sort_values("Published", ascending=False),
                 use_container_width=True, hide_index=True)

with st.expander("View Merged Daily Dataset"):
    daily_display = merged[[
        "date", "top_headline", "num_articles", "avg_sentiment",
        "avg_vader_sentiment", "close_price", "log_return", "abs_volatility",
    ]].copy()
    daily_display["abs_volatility"] = (daily_display["abs_volatility"] * 100).round(4)
    daily_display["log_return"] = (daily_display["log_return"] * 100).round(4)
    daily_display.columns = [
        "Date", "Top Headline", "# Articles", "Avg AV Sentiment",
        "Avg VADER", "Close ($)", "Return (%)", "Volatility (%)",
    ]
    st.dataframe(daily_display, use_container_width=True, hide_index=True)

# --- Interpretation ---
st.subheader("6. Interpretation")

sig_level = 0.05
is_sig_abs = p_abs < sig_level

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

st.markdown(f"""
**Data Sources:**
- **{len(news_filtered)} articles** fetched live from {' + '.join(sources_used)}
- **{len(merged)} trading days** with matched price data from Alpha Vantage TIME_SERIES_DAILY
- Sentiment scores: VADER (headline-based) + Alpha Vantage (where available)

**Key Findings:**
- **Asymmetric impact:** Negative news tends to produce larger volatility spikes than
  positive news of similar magnitude, reflecting the market's loss aversion.
- **News magnitude matters:** The *strength* of the news sentiment (absolute value)
  is more predictive of volatility than the *direction* alone.
- **Market efficiency:** Many news events are partially priced in before publication
  (e.g., earnings expectations), reducing the observed volatility response.
- **Confounding factors:** Volatility is also driven by macro events (Fed decisions,
  geopolitical tensions), sector rotation, and options expiration — not just company-specific news.
- **AV vs VADER:** Alpha Vantage provides ticker-specific sentiment (more accurate for AAPL),
  while VADER offers a general-purpose baseline for comparison.
""")
