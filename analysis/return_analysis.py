import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from scipy.stats import norm, kurtosis, skew
from .utils import get_stock_data_compact

import os
AV_API_KEY = os.environ.get("AV_API_KEY", "")
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}


def get_fred_benchmark(series_id="SP500"):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
    }
    try:
        r = requests.get(url, params=params)
        data = r.json()
        df = pd.DataFrame(data["observations"])
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.set_index("date").dropna()
        df["log_return"] = np.log(df["value"] / df["value"].shift(1))
        return df.dropna()
    except Exception:
        return None


def build_return_analysis(stock_name="Apple", days=100, show_benchmark=True):
    """Run the full return analysis and return results as a dict."""
    symbol = STOCKS.get(stock_name, "AAPL")
    df_raw, error = get_stock_data_compact(symbol, AV_API_KEY, throttle_seconds=0.1)

    if df_raw is None:
        return {"error": error}

    df = df_raw.tail(days)
    returns = df["log_return"]

    # --- Histogram chart ---
    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=returns, nbinsx=30, name=stock_name,
        histnorm="probability density",
        marker_color="#1f77b4", opacity=0.6,
    ))

    if show_benchmark:
        df_fred = get_fred_benchmark()
        if df_fred is not None:
            df_fred = df_fred[df_fred.index >= df.index.min()]
            fig.add_trace(go.Histogram(
                x=df_fred["log_return"], nbinsx=30, name="S&P 500",
                histnorm="probability density",
                marker_color="#ff7f0e", opacity=0.4,
            ))

    mu, std = norm.fit(returns)
    x_range = np.linspace(returns.min(), returns.max(), 100)
    y_norm = norm.pdf(x_range, mu, std)
    fig.add_trace(go.Scatter(
        x=x_range, y=y_norm, mode="lines", name="Normal Dist.",
        line=dict(color="red", dash="dash"),
    ))

    fig.update_layout(
        title=f"Distribution of Log-Returns: {stock_name} ({symbol})",
        barmode="overlay",
        template="plotly_white",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    histogram_html = fig.to_html(full_html=False, include_plotlyjs=False)

    # --- Time series chart ---
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df.index, y=returns, mode="lines",
        name=f"{stock_name} Log-Returns",
        line=dict(color="#1f77b4", width=1),
    ))
    fig2.update_layout(
        title=f"Daily Log-Returns Over Time: {stock_name}",
        template="plotly_white",
        xaxis_title="Date",
        yaxis_title="Log-Return",
        margin=dict(l=40, r=40, t=60, b=40),
    )

    timeseries_html = fig2.to_html(full_html=False, include_plotlyjs=False)

    # --- Metrics ---
    k_val = float(kurtosis(returns))
    s_val = float(skew(returns))

    if k_val > 0.5:
        summary = (
            f"Even within the last {len(df)} trading days, {stock_name} shows signs of "
            f"leptokurtosis (excess kurtosis = {k_val:.2f} > 0), indicating heavier tails "
            f"than a normal distribution. This means extreme price movements occur more "
            f"frequently than a Gaussian model would predict."
        )
    else:
        summary = (
            f"Over this short-term period of {len(df)} trading days, the distribution of "
            f"{stock_name} remains relatively close to the normal model "
            f"(excess kurtosis = {k_val:.2f})."
        )

    return {
        "error": None,
        "stock_name": stock_name,
        "symbol": symbol,
        "days": len(df),
        "date_from": df.index.min().strftime("%Y-%m-%d"),
        "date_to": df.index.max().strftime("%Y-%m-%d"),
        "histogram_html": histogram_html,
        "timeseries_html": timeseries_html,
        "mean": f"{mu:.5f}",
        "std": f"{std:.4f}",
        "skewness": f"{s_val:.2f}",
        "kurtosis": f"{k_val:.2f}",
        "summary": summary,
    }
