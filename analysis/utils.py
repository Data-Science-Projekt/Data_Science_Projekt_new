import pandas as pd
import requests
import time
import numpy as np
from functools import wraps

# Simple in-memory cache with TTL
_cache = {}
CACHE_TTL_SECONDS = 3600  # 1 hour

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