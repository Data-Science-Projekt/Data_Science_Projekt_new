import streamlit as st
import pandas as pd

st.title("About the Project")
st.markdown("Goals, motivation, and scope of the StockInsight analysis")

st.divider()

st.header("Goals")
st.markdown("""
The goal of this project is to systematically investigate key research questions about stock market behavior
using modern data science methods. Specifically, we aim to:

- **Analyze return distributions** and test whether stock returns follow a normal distribution
- **Quantify volatility patterns** and identify drivers of trading range variation
- **Uncover market structure** through correlation dynamics and clustering
- **Detect market regimes** (bull/bear phases) using algorithmic approaches
- **Evaluate technical indicators** and their predictive power across market conditions
- **Assess diversification benefits** and quantify risk reduction through portfolio construction
- **Measure sentiment impact** by linking news sentiment to price movements
""")

st.header("Motivation")
st.markdown("""
Financial markets are complex systems where many assumptions from classical theory
(e.g., normally distributed returns, constant correlations) break down in practice.
This project was motivated by the desire to:

1. **Bridge theory and practice** — apply academic concepts to real market data and see where models hold up and where they fail
2. **Build an end-to-end data pipeline** — from API data ingestion through analysis to interactive visualization
3. **Create an accessible tool** — make quantitative analysis available through an interactive web application rather than static reports
4. **Explore cross-domain connections** — combine financial data, macroeconomic indicators, and news sentiment into a unified analysis framework
""")

st.header("Methodology")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Statistical Methods")
    st.markdown("""
    - Descriptive statistics & distribution fitting
    - Shapiro-Wilk and Jarque-Bera normality tests
    - Rolling correlations & covariance analysis
    - Value at Risk (VaR) and Expected Shortfall
    """)

    st.subheader("Time Series Analysis")
    st.markdown("""
    - Logarithmic return calculation
    - GARCH volatility modeling
    - Regime detection algorithms
    - Moving averages, RSI, MACD
    """)

with col2:
    st.subheader("Machine Learning")
    st.markdown("""
    - Hierarchical clustering of stock correlations
    - PCA for dimensionality reduction
    - Sentiment analysis of news data
    - Classification of market regimes
    """)

    st.subheader("Visualization & Deployment")
    st.markdown("""
    - Interactive charts with Plotly
    - Streamlit multipage web application
    - Live data integration via APIs
    - Cloud deployment for public access
    """)

st.header("Dataset Description")
st.markdown("""
The analysis covers **six major U.S. stocks** from two sectors, observed over the most recent trading period:
""")

st.table(pd.DataFrame({
    "Stock": ["Apple (AAPL)", "Microsoft (MSFT)", "NVIDIA (NVDA)", "J.P. Morgan (JPM)", "Goldman Sachs (GS)", "Bank of America (BAC)"],
    "Sector": ["Technology", "Technology", "Technology", "Financial", "Financial", "Financial"],
    "Why included": [
        "Largest company by market cap, benchmark for tech sector",
        "Enterprise & cloud leader, diversified revenue streams",
        "AI/GPU leader, highest volatility among the six",
        "Largest U.S. bank, financial sector bellwether",
        "Investment banking leader, sensitive to market conditions",
        "Consumer banking giant, interest rate sensitive",
    ],
}))

st.markdown("""
**Data fields per stock:**
- **OHLCV:** Open, High, Low, Close, Volume (daily)
- **Derived features:** Log-returns, rolling volatility, technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands)

**External data sources:**
""")

st.table(pd.DataFrame({
    "Source": ["Alpha Vantage", "FRED"],
    "Data": ["Daily & monthly stock prices", "S&P 500 index, Consumer Sentiment Index"],
    "Usage": ["Core price data for all analyses", "Market benchmark & macro context"],
}))
