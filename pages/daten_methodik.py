import streamlit as st
import pandas as pd

st.title("Data & Methodology")
st.markdown("Data sources, preparation, and applied methods")

st.divider()

st.header("Data Sources")
st.markdown("""
Our analysis is based on historical stock price data obtained through publicly available financial APIs.

- **Daily price data:** Open, High, Low, Close, Volume
- **Time period:** Last 100 trading days (Alpha Vantage compact) + monthly history
- **Stocks analyzed:** Apple (AAPL), Microsoft (MSFT), NVIDIA (NVDA), J.P. Morgan (JPM), Goldman Sachs (GS), Bank of America (BAC)
- **Sources:** Alpha Vantage (stock data), FRED (S&P 500, Consumer Sentiment), NewsAPI (news articles)
""")

st.header("Data Preparation")
st.markdown("""
The raw data was processed in several steps:

1. Cleaning of missing values and outliers
2. Calculation of logarithmic returns
3. Normalization and standardization for comparability
4. Feature engineering for technical indicators
""")

st.header("Methods")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Statistical Analysis")
    st.markdown("Descriptive statistics, distribution analysis, hypothesis testing")

    st.subheader("Time Series Analysis")
    st.markdown("ARIMA, GARCH models, stationarity tests")

with col2:
    st.subheader("Machine Learning")
    st.markdown("Clustering, classification, dimensionality reduction")

    st.subheader("Visualization")
    st.markdown("Matplotlib, Seaborn, Plotly for interactive charts")

st.header("Technologies Used")
st.table(pd.DataFrame({
    "Technology": ["Python", "Pandas / NumPy", "Scikit-learn", "Matplotlib / Plotly", "Streamlit"],
    "Purpose": ["Programming language", "Data processing", "Machine Learning", "Visualization", "Web framework & deployment"],
}))
