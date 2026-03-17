import streamlit as st

st.set_page_config(page_title="StockInsight Dashboard", layout="wide", page_icon="📈")

# Navigation Definition
pages = {
    "": [
        st.Page("pages/home.py", title="Home", default=True),
        st.Page("pages/daten_methodik.py", title="Data & Methodology"),
    ],
    "Stock Behavior": [
        st.Page("return_analysis.py", title="Return Analysis"),
        st.Page("range_analysis.py", title="Volatility"),
        st.Page("technische_analyse.py", title="Technical Analysis"),
    ],
    "Market Environment": [
        st.Page("marktphasen.py", title="Market Phases"),
        st.Page("marktstruktur.py", title="Market Structure"),
    ],
    "Risk Analysis": [
        st.Page("risikomanagement.py", title="Risk Management"),
    ],
    "Sentiment & Macro": [
        st.Page("sentiment_correlation.py", title="Sentiment Correlation"),
    ],
    "About": [
        st.Page("pages/about_project.py", title="About the Project"),
        st.Page("pages/fazit.py", title="Conclusion"),
        st.Page("pages/team.py", title="Team"),
    ],
}

# Navigation ausführen
try:
    nav = st.navigation(pages)
    nav.run()
except Exception as e:
    st.error(f"Kritischer Fehler in der Navigation: {e}")
