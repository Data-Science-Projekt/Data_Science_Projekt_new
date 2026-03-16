import streamlit as st

st.set_page_config(page_title="StockInsight", layout="wide")

pages = [
    st.Page("pages/home.py", title="Home", default=True),
    st.Page("pages/daten_methodik.py", title="Data & Methodology"),
    st.Page("return_analysis.py", title="Return Analysis"),
    st.Page("range_analysis.py", title="Volatility"),
    st.Page("marktstruktur.py", title="Market Structure"),
    st.Page("marktphasen.py", title="Market Phases"),
    st.Page("technische_analyse.py", title="Technical Analysis"),
    st.Page("risikomanagement.py", title="Risk Management"),
    st.Page("sentiment_correlation.py", title="Sentiment Correlation"),
    st.Page("pages/fazit.py", title="Conclusion"),
    st.Page("pages/team.py", title="Team"),
]

nav = st.navigation(pages)
nav.run()
