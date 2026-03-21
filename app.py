import streamlit as st

st.set_page_config(page_title="StockInsight Dashboard", layout="wide", page_icon="📈")

# Navigation Definition
pages = {
    "": [
        st.Page("pages/home.py", title="Home", default=True),
    ],
    "Stock Behavior": [
        st.Page("analysis/return_analysis.py", title="Return Analysis"),
        st.Page("analysis/range_analysis.py", title="Volatility"),
        st.Page("analysis/technische_analyse.py", title="Technical Analysis"),
    ],
    "Market Environment": [
        st.Page("analysis/marktphasen.py", title="Market Phases"),
        st.Page("analysis/marktstruktur.py", title="Market Structure"),
    ],
    "Risk Analysis": [
        st.Page("analysis/risikomanagement.py", title="Risk Management"),
    ],
    "Sentiment & Macro": [
        st.Page("analysis/sentiment_correlation.py", title="Sentiment Correlation"),
    ],
    "Fundamentals": [
        st.Page("analysis/company_fundamentals.py", title="Company Fundamentals"),
    ],
    "About": [
        st.Page("pages/about_project.py", title="About the Project"),
        st.Page("pages/fazit.py", title="Conclusion"),
        st.Page("pages/team.py", title="Team"),
        st.Page("pages/imprint.py", title="Imprint"),
    ],
}

# Navigation ausführen
try:
    nav = st.navigation(pages)
    nav.run()
except Exception as e:
    st.error(f"Kritischer Fehler in der Navigation: {e}")
