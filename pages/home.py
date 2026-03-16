import streamlit as st

st.title("StockInsight")
st.markdown("A data science project for systematic stock market analysis — from returns and volatility to market phases and risk management.")

st.divider()

st.header("Project Summary")
st.markdown("""
This project applies modern data science methods to investigate key research questions about stock market behavior.
Using live data from Alpha Vantage, NewsAPI, and FRED, we analyze six tech and financial stocks
(Apple, Microsoft, NVIDIA, J.P. Morgan, Goldman Sachs, Bank of America) across multiple dimensions:
return distributions, trading ranges, market structure, regime detection, technical indicators, and risk management.
""")

st.header("Key Findings")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Return Analysis")
    st.markdown("""
    Daily log-returns deviate significantly from a normal distribution,
    exhibiting fat tails (leptokurtosis) and negative skewness —
    extreme events occur more frequently than standard models predict.
    """)

    st.subheader("Market Phases")
    st.markdown("""
    Bull and bear markets can be systematically identified.
    Bull markets last significantly longer on average, but bear markets
    exhibit stronger and faster price movements.
    """)

with col2:
    st.subheader("Volatility & Trading Ranges")
    st.markdown("""
    Tech stocks show higher average daily trading ranges than financial stocks.
    News sentiment magnitude is a stronger predictor of volatility spikes
    than sentiment direction alone.
    """)

    st.subheader("Technical Analysis")
    st.markdown("""
    Technical indicators (moving averages, RSI, MACD) provide useful signals
    in trending markets but frequently generate false signals in sideways phases.
    """)

with col3:
    st.subheader("Market Structure")
    st.markdown("""
    Correlations between stocks are dynamic, not static. During crises,
    correlations increase sharply, making diversification more difficult
    precisely when it is needed most.
    """)

    st.subheader("Risk Management")
    st.markdown("""
    With as few as 15–20 stocks, unsystematic risk can be largely eliminated
    through diversification. However, systematic market risk remains
    and must be managed separately.
    """)
