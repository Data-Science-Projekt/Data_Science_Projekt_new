import pandas as pd
import requests
import os
import time

# Hier werden die Keys sicher aus der Umgebung geladen (nicht im Code gespeichert!)
AV_API_KEY = os.getenv("AV_API_KEY")
FRED_API_KEY = os.getenv("FRED_API_KEY")

def fetch_stock_data(symbol):
    """Holt die letzten 100 Tage fuer eine Aktie."""
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={AV_API_KEY}'
    try:
        r = requests.get(url, timeout=15).json()
        if "Time Series (Daily)" in r:
            df = pd.DataFrame.from_dict(r['Time Series (Daily)'], orient='index').astype(float)
            df.to_csv(f"data/stock_{symbol}.csv")
            print(f"Update Erfolg: {symbol}")
        else:
            print(f"Fehler bei {symbol}: {r.get('Note', 'Unbekannter Fehler')}")
    except Exception as e:
        print(f"Verbindungsfehler bei {symbol}: {e}")

def fetch_fred_data(series_id, filename):
    """Holt Makro-Daten von FRED."""
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json"
    try:
        r = requests.get(url, timeout=15).json()
        if 'observations' in r:
            df = pd.DataFrame(r['observations'])
            df.to_csv(f"data/{filename}.csv", index=False)
            print(f"Update Erfolg: {filename}")
    except Exception as e:
        print(f"Fehler bei {series_id}: {e}")

if __name__ == "__main__":
    # Liste aller Aktien aus euren Forschungsfragen
    symbols = ["AAPL", "NVDA", "MSFT", "JPM", "GS", "BAC"]
    
    for s in symbols:
        fetch_stock_data(s)
        time.sleep(15) # Wichtig: Pause für den Free-Key!

    # Makro-Daten fuer VIX (Frage 3) und Sentiment (Frage 9)
    fetch_fred_data("VIXCLS", "macro_vix")
    fetch_fred_data("UMCSENT", "consumer_sentiment")
