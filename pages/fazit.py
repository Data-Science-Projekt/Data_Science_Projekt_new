import streamlit as st

st.title("Conclusion & Interpretation")
st.markdown("Summary of results and their significance")

st.divider()

st.header("Summary of Results")
st.markdown("""
1. **Return distributions** deviate significantly from the normal distribution — fat tails and negative skewness are the norm.
2. **Volatility** occurs in clusters and can be well described by GARCH models.
3. **Correlations** between stocks are dynamic and increase sharply during crises.
4. **Market phases** can be systematically identified using Hidden Markov Models.
5. **Technical indicators** provide useful signals in trending markets but fail in sideways phases.
6. **Diversification** effectively reduces unsystematic risk but offers no protection against systematic risks.
7. **Consumer sentiment** correlates with stock returns, with sector-specific differences between tech and financial stocks.
""")

st.header("Implications")

col1, col2 = st.columns(2)

with col1:
    st.subheader("For Investors")
    st.markdown("""
    - Risk models based on the normal distribution underestimate actual risk
    - Diversification is essential but insufficient during crises
    - Technical analysis can be used as a supplement but not as the sole decision criterion
    """)

with col2:
    st.subheader("For Research")
    st.markdown("""
    - Non-linear models capture market behavior more accurately
    - Regime-switching models capture structural breaks
    - Machine learning offers potential for improved forecasts
    """)

st.header("Limitations")
st.markdown("""
- Historical data does not guarantee future performance
- Transaction costs and slippage were simplified
- The analysis is limited to a specific time period and market
- Macroeconomic factors were not explicitly modeled
""")

st.header("Outlook")
st.markdown("""
Possible extensions of this project include:

- Integration of sentiment analysis (news, social media)
- Expansion to international markets
- Deep learning models for price forecasting
- Real-time dashboard with automatic alerts
""")
