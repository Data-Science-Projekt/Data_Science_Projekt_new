import pandas as pd
import requests
import time
import numpy as np
import streamlit as st
from functools import wraps

# Simple in-memory cache with TTL
_cache = {}
CACHE_TTL_SECONDS = 3600  # 1 hour


def render_page_header(title, research_question):
    st.title(title)

    st.markdown(
        """
        <style>
        .research-header {
            margin: 0.35rem 0 1.5rem;
            padding: 0.95rem 1.15rem;
            border-left: 4px solid #2563eb;
            border-radius: 12px;
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.10);
        }
        .research-header__eyebrow {
            margin: 0 0 0.3rem;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #1d4ed8;
        }
        .research-header__question {
            margin: 0;
            font-size: 0.98rem;
            line-height: 1.5;
            font-weight: 500;
            color: #1e3a8a;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <section class="research-header">
            <p class="research-header__eyebrow">Research Question</p>
            <p class="research-header__question">{research_question}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # Auto-scroll past header so interactive content is immediately visible
    st.components.v1.html("""
    <script>
        const main = window.parent.document.querySelector('section.main');
        if (main) {
            main.scrollTo({ top: 300, behavior: 'smooth' });
        }
    </script>
    """, height=0)

    st.info("⬅️ Use the **sidebar** to adjust settings and interact with the analysis.")

def simple_cache(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(sorted(kwargs.items()))
        now = time.time()
        if key in _cache and now - _cache[key]['timestamp'] < CACHE_TTL_SECONDS:
            return _cache[key]['data']
        result = func(*args, **kwargs)
        _cache[key] = {'data': result, 'timestamp': now}
        return result
    return wrapper

@simple_cache
def get_stock_data_compact(symbol, api_key, throttle_seconds=0, timeout=10):
    """
    Fetch daily stock data from Alpha Vantage TIME_SERIES_DAILY.

    Args:
        symbol (str): Stock symbol (e.g., 'AAPL')
        api_key (str): Alpha Vantage API key
        throttle_seconds (float): Optional delay between requests to avoid rate limits
        timeout (int): Request timeout in seconds

    Returns:
        tuple: (DataFrame or None, error_message or None)
    """
    if throttle_seconds > 0:
        time.sleep(throttle_seconds)

    url = (
        f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY"
        f"&symbol={symbol}&outputsize=compact&apikey={api_key}"
    )

    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()  # Raise for HTTP errors
        data = r.json()
    except requests.exceptions.Timeout:
        return None, f"Request timed out for {symbol} after {timeout} seconds."
    except requests.exceptions.RequestException as e:
        return None, f"Network error for {symbol}: {str(e)}"
    except ValueError:
        return None, f"Invalid JSON response for {symbol}."

    # Check for API-specific errors
    if "Error Message" in data:
        return None, f"API Error for {symbol}: {data['Error Message']}"

    if "Information" in data:
        return None, f"API Information for {symbol}: {data['Information']}"

    if "Note" in data:
        return None, f"API Rate Limit for {symbol}: {data['Note']}"

    if "Time Series (Daily)" not in data:
        return None, f"No 'Time Series (Daily)' data found for {symbol}. Check symbol or API key."

    try:
        df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
        df.index = pd.to_datetime(df.index)
        df = df.astype(float).sort_index()
        df["log_return"] = np.log(df["4. close"] / df["4. close"].shift(1))
        return df.dropna(), None
    except Exception as e:
        return None, f"Data processing error for {symbol}: {str(e)}"