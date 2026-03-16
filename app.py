import streamlit as st
import os

# Seite konfigurieren
st.set_page_config(
    page_title="Financial Dashboard", 
    page_icon="📈", 
    layout="wide"
)

# API Keys
AV_API_KEY = st.secrets.get("AV_API_KEY", "")
FRED_API_KEY = st.secrets.get("FRED_API_KEY", "")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Auswahl:",
    ["Home", "Renditeanalyse", "Marktphasen", "Marktstruktur", "Range Analysis", "Risikomanagement", "Technische Analyse", "Sentiment Correlation"]
)

# Routing
if page == "Home":
    st.title("Finanzmarktanalyse Dashboard")
    st.markdown("---")
    st.write("Die Anwendung wurde erfolgreich geladen.")
    st.info("Bitte waehlen Sie eine Analyse in der linken Sidebar aus.")

elif page == "Renditeanalyse":
    import return_analysis

elif page == "Marktphasen":
    import marktphasen

elif page == "Marktstruktur":
    import marktstruktur

elif page == "Range Analysis":
    import range_analysis

elif page == "Risikomanagement":
    import risikomanagement

elif page == "Technische Analyse":
    import technische_analyse

elif page == "Sentiment Correlation":
    import sentiment_correlation
