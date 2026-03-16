import streamlit as st
import os

# Konfiguration der Seite - Dies darf NUR hier stehen
st.set_page_config(page_title="Financial Analysis Dashboard", layout="wide")

# API Keys sicher laden
AV_API_KEY = st.secrets.get("AV_API_KEY", "")
FRED_API_KEY = st.secrets.get("FRED_API_KEY", "")

# Sidebar Navigation
st.sidebar.title("Projekt Navigation")
page = st.sidebar.radio(
    "Gehe zu:",
    [
        "Home",
        "Renditeanalyse",
        "Marktphasen",
        "Marktstruktur",
        "Range Analysis",
        "Risikomanagement",
        "Technische Analyse",
        "Sentiment Correlation"
    ]
)

# Routing Logik
if page == "Home":
    st.title("Data Science Projekt: Finanzmarktanalyse")
    st.write("Willkommen! Waehle links eine Analyse aus.")

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
