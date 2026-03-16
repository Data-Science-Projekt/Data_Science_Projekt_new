import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import time
from .utils import get_stock_data_compact

import os
AV_API_KEY = os.environ.get("AV_API_KEY", "")

# Stocks for range analysis
TECH_STOCKS = {"Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA"}
FINANCIAL_STOCKS = {"J.P. Morgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC"}


def build_range_analysis(days=100):
    """Run the full range analysis for tech and financial stocks and return results as a dict."""
    all_stocks = {**TECH_STOCKS, **FINANCIAL_STOCKS}
    stock_data = {}
    errors = []

    # Fetch data for all stocks
    for name, symbol in all_stocks.items():
        df, error = get_stock_data_compact(symbol, AV_API_KEY, throttle_seconds=0.1)
        if df is None:
            errors.append(f"{name} ({symbol}): {error}")
            continue
        df = df.tail(days)
        df["absolute_range"] = df["2. high"] - df["3. low"]
        df["relative_range_pct"] = (df["absolute_range"] / df["4. close"]) * 100
        stock_data[name] = df

    if not stock_data:
        return {"error": "No data could be fetched for any stock. Errors: " + "; ".join(errors)}

    # Determine common date range
    min_date = max(df.index.min() for df in stock_data.values())
    max_date = min(df.index.max() for df in stock_data.values())
    for name in stock_data:
        stock_data[name] = stock_data[name][(stock_data[name].index >= min_date) & (stock_data[name].index <= max_date)]

    # --- Box plot chart ---
    fig_box = go.Figure()
    for name, df in stock_data.items():
        fig_box.add_trace(go.Box(
            y=df["relative_range_pct"],
            name=name,
            boxmean=True,
        ))
    fig_box.update_layout(
        title="Distribution of Daily Range Percentages: Tech vs Financial Stocks",
        yaxis_title="Relative Daily Range (%)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    boxplot_html = fig_box.to_html(full_html=False, include_plotlyjs=False)

    # --- Time series chart ---
    fig_ts = go.Figure()
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    for i, (name, df) in enumerate(stock_data.items()):
        fig_ts.add_trace(go.Scatter(
            x=df.index,
            y=df["relative_range_pct"],
            mode="lines",
            name=name,
            line=dict(color=colors[i % len(colors)], width=1),
        ))
    fig_ts.update_layout(
        title="Daily Range Percentages Over Time",
        xaxis_title="Date",
        yaxis_title="Relative Daily Range (%)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
    )
    timeseries_html = fig_ts.to_html(full_html=False, include_plotlyjs=False)

    # --- Summary statistics per stock ---
    stats = {}
    for name, df in stock_data.items():
        ranges = df["relative_range_pct"]
        stats[name] = {
            "mean": f"{ranges.mean():.2f}",
            "median": f"{ranges.median():.2f}",
            "std": f"{ranges.std():.2f}",
            "min": f"{ranges.min():.2f}",
            "max": f"{ranges.max():.2f}",
        }

    # --- Sector comparison ---
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

    sector_comparison = {
        "tech_avg_range_pct": f"{tech_avg:.2f}",
        "financial_avg_range_pct": f"{financial_avg:.2f}",
        "difference": f"{diff:.2f}",
    }

    # --- Generate summary ---
    summary = (
        f"Analysis of daily trading ranges for the last {len(stock_data[list(stock_data.keys())[0]])} trading days "
        f"from {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}. "
        f"Tech stocks (Apple, Microsoft, NVIDIA) show an average daily range of {tech_avg:.2f}%, "
        f"while financial stocks (J.P. Morgan, Goldman Sachs, Bank of America) average {financial_avg:.2f}%. "
        f"The difference is {diff:.2f}%. "
        f"{'Tech stocks exhibit higher volatility in daily ranges.' if diff > 0 else 'Financial stocks exhibit higher volatility in daily ranges.' if diff < 0 else 'Both sectors show similar daily range volatility.'}"
    )

    return {
        "error": None,
        "days": len(stock_data[list(stock_data.keys())[0]]),
        "date_from": min_date.strftime("%Y-%m-%d"),
        "date_to": max_date.strftime("%Y-%m-%d"),
        "boxplot_html": boxplot_html,
        "timeseries_html": timeseries_html,
        "per_stock_stats": stats,
        "sector_comparison": sector_comparison,
        "summary": summary,
    }