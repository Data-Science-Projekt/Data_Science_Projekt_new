import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests

AV_API_KEY = st.secrets.get("AV_API_KEY", "")
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA", "S&P 500": "SPY"}

@st.cache_data(show_spinner="Loading data...")
def get_stock_data(symbol):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url)
        data = r.json()
        if "Time Series (Daily)" in data:
            df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.astype(float).sort_index()
            df.rename(columns={"4. close": "close"}, inplace=True)
            return df[["close"]]
        return None
    except:
        return None

def identify_phases(close_values, index_values):
    df = pd.DataFrame({'close': close_values}, index=pd.to_datetime(index_values))
    df['rolling_max'] = df['close'].rolling(window=20, min_periods=1).max()
    df['rolling_min'] = df['close'].rolling(window=20, min_periods=1).min()

    df['phase'] = np.select(
        [
            (df['close'] - df['rolling_max']) / df['rolling_max'] <= -0.2,
            (df['close'] - df['rolling_min']) / df['rolling_min'] >= 0.2
        ],
        ['Bear', 'Bull'],
        default='Neutral'
    )
    return df

# --- UI ---
st.title("Market Phase Analysis")
st.write("Identify Bull, Bear, and Neutral market conditions using a rolling window approach.")

selected_stock = st.sidebar.selectbox("Select Asset:", list(STOCKS.keys()))
df_raw = get_stock_data(STOCKS[selected_stock])

if df_raw is not None:
    df_view = identify_phases(df_raw['close'], df_raw.index)

    # Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_view.index, y=df_view['close'], name='Price'))
    fig.update_layout(template="plotly_dark", xaxis_title="Date", yaxis_title="Price")
    st.plotly_chart(fig, use_container_width=True)

    # Phase distribution
    st.subheader("Phase Distribution")
    counts = df_view['phase'].value_counts()
    percentages = (counts / len(df_view) * 100).round(2)

    dist_df = pd.DataFrame({
        "Days": counts,
        "Percentage (%)": percentages
    })
    st.table(dist_df)

    # --- Interpretation ---
    st.markdown("---")
    st.subheader("Interpretation & Insights")

    bull_pct = percentages.get("Bull", 0)
    bear_pct = percentages.get("Bear", 0)
    neutral_pct = percentages.get("Neutral", 0)

    st.markdown(f"""
### Key Insights

**1. Market Regime Overview**
- The asset spent **{bull_pct}%** of the time in a Bull phase  
- **{bear_pct}%** in a Bear phase  
- **{neutral_pct}%** in a Neutral phase  

👉 This gives a quick understanding of the dominant market environment.

---

**2. Trend Strength**
- A **high Bull percentage** suggests strong upward momentum and growth phases  
- A **high Bear percentage** indicates prolonged downturns or corrections  
- A **high Neutral percentage** signals sideways movement or consolidation  

---

**3. Volatility & Behavior**
- Stocks like NVIDIA often switch phases more frequently due to higher volatility  
- Broad indices like the S&P 500 typically show smoother, longer trends  

---

**4. Strategy Implications**
- **Bull phases**: Favor trend-following or long strategies  
- **Bear phases**: Risk management becomes crucial (hedging, defensive assets)  
- **Neutral phases**: Range trading or waiting for breakouts can be more effective  

---

**5. Methodology Note**
This model uses a **20-day rolling window**:
- A **20% drop from recent highs → Bear**
- A **20% rise from recent lows → Bull**

This is a simplified but widely used definition of market cycles.
""")

    st.caption("Methodology: Rolling 20-day window analysis of price movements.")

else:
    st.error("Data could not be retrieved. Please check your API key or try again later.")
