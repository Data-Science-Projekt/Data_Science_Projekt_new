import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import pearsonr, spearmanr
import os

# --- KONFIGURATION ---
# Pfad zur statischen Datendatei im data-Ordner
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

@st.cache_data(show_spinner="Lade fundamentale Daten...")
def load_iphone_sales():
    """Liest die manuell gepflegten iPhone-Verkaufszahlen ein."""
    # Pfad-Anpassung, falls das Skript im Unterordner 'pages' liegt
    path = os.path.join("data", "iphone_sales.csv")
    
    if not os.path.exists(path):
        return pd.DataFrame()
        
    try:
        df = pd.read_csv(path, parse_dates=["earnings_date"])
        df = df.sort_values("earnings_date").reset_index(drop=True)
        
        # Berechnung der Kursreaktion (30 Tage nach Earnings vs. Earnings-Tag)
        if "price_on_earnings" in df.columns and "price_30d_after" in df.columns:
            df["price_change_pct"] = (
                (df["price_30d_after"] - df["price_on_earnings"]) / df["price_on_earnings"] * 100
            )
        
        # Berechnung der Wachstumsraten
        df["revenue_growth"] = df["iphone_revenue_billion"].pct_change() * 100
        df["units_growth"] = df["iphone_units_million"].pct_change() * 100
        return df
    except Exception:
        return pd.DataFrame()

# --- HAUPTSEITE ---
st.title("Forschungsfrage 9: Unternehmens-Fundamentaldaten")
st.markdown("""
**Forschungsfrage:** Wie beeinflussen die iPhone-Verkaufszahlen die langfristige Aktienperformance von Apple? 
Treiben Quartals-Ueberraschungen im iPhone-Segment die Kursbewegungen nach den Earnings?
""")

st.markdown("""
#### Methodik
- **iPhone-Absatz und Umsatz:** Daten aus den Quartalsberichten von Apple.
- **Aktienkurs-Reaktion:** Vergleich des Kurses am Tag der Bekanntgabe vs. 30 Tage danach.
- **Korrelationsanalyse:** Zusammenhang zwischen Umsatz/Stueckzahlen und Kursreaktion.
- **Saisonalitaet:** Identifikation von Mustern ueber die Fiskalquartale hinweg.
""")

df = load_iphone_sales()

if df.empty:
    st.error("Die Datei data/iphone_sales.csv wurde nicht gefunden oder ist leer. Bitte Daten manuell pflegen.")
    st.stop()

st.write(f"**Analyse-Zeitraum:** {df['quarter'].iloc[0]} bis {df['quarter'].iloc[-1]} ({len(df)} Quartale)")

# --- 1. UMSATZ & STUECKZAHLEN ---
st.subheader("1. iPhone-Umsatz und Absatzzahlen im Zeitverlauf")

fig_sales = make_subplots(specs=[[{"secondary_y": True}]])
fig_sales.add_trace(
    go.Bar(
        x=df["quarter"],
        y=df["iphone_revenue_billion"],
        name="Umsatz ($ Mrd.)",
        marker_color="#1f77b4",
        opacity=0.7,
    ),
    secondary_y=False,
)
fig_sales.add_trace(
    go.Scatter(
        x=df["quarter"],
        y=df["iphone_units_million"],
        name="Einheiten (Mio.)",
        mode="lines+markers",
        line=dict(color="#e94560", width=2),
        marker=dict(size=6),
    ),
    secondary_y=True,
)
fig_sales.update_layout(template="plotly_white", height=450)
fig_sales.update_yaxes(title_text="Umsatz ($ Mrd.)", secondary_y=False)
fig_sales.update_yaxes(title_text="Verkaufte Einheiten (Mio.)", secondary_y=True)
st.plotly_chart(fig_sales, use_container_width=True)

# --- 2. KURSREAKTION ---
st.subheader("2. Aktienkurs-Bewegung nach Earnings (30 Tage)")

if "price_change_pct" in df.columns:
    colors = ["#2ca02c" if x >= 0 else "#d62728" for x in df["price_change_pct"]]
    fig_reaction = go.Figure()
    fig_reaction.add_trace(
        go.Bar(
            x=df["quarter"],
            y=df["price_change_pct"],
            marker_color=colors,
            text=[f"{v:+.1f}%" for v in df["price_change_pct"]],
            textposition="outside",
        )
    )
    fig_reaction.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_reaction.update_layout(
        yaxis_title="Kursveraenderung (%)",
        template="plotly_white",
        height=400,
    )
    st.plotly_chart(fig_reaction, use_container_width=True)

# --- 3. KORRELATION ---
st.subheader("3. Korrelations-Analyse")

clean = df[["iphone_revenue_billion", "iphone_units_million", "price_change_pct"]].dropna()

if len(clean) >= 3:
    rev_pearson_r, rev_pearson_p = pearsonr(clean["iphone_revenue_billion"], clean["price_change_pct"])
    unit_pearson_r, unit_pearson_p = pearsonr(clean["iphone_units_million"], clean["price_change_pct"])

    corr_table = pd.DataFrame([
        {
            "Metrik": "iPhone-Umsatz",
            "Pearson r": f"{rev_pearson_r:.4f}",
            "P-Wert": f"{rev_pearson_p:.4f}",
        },
        {
            "Metrik": "iPhone-Einheiten",
            "Pearson r": f"{unit_pearson_r:.4f}",
            "P-Wert": f"{unit_pearson_p:.4f}",
        },
    ])
    st.table(corr_table)

# --- 4. SAISONALITAET ---
st.subheader("4. Saisonale Muster nach Fiskalquartal")

df["fiscal_q"] = df["quarter"].str[:2]
seasonal = df.groupby("fiscal_q").agg(
    avg_revenue=("iphone_revenue_billion", "mean"),
    avg_price_change=("price_change_pct", "mean"),
).reset_index()

fig_seasonal = make_subplots(specs=[[{"secondary_y": True}]])
fig_seasonal.add_trace(
    go.Bar(
        x=seasonal["fiscal_q"],
        y=seasonal["avg_revenue"],
        name="Durchschn. Umsatz ($ Mrd.)",
        marker_color="#1f77b4",
        opacity=0.7,
    ),
    secondary_y=False,
)
fig_seasonal.add_trace(
    go.Scatter(
        x=seasonal["fiscal_q"],
        y=seasonal["avg_price_change"],
        name="Durchschn. Kursreaktion (%)",
        mode="lines+markers",
        line=dict(color="#e94560", width=2),
    ),
    secondary_y=True,
)
fig_seasonal.update_layout(template="plotly_white", height=400)
st.plotly_chart(fig_seasonal, use_container_width=True)

# --- 5. ZENTRALE ERKENNTNISSE ---
st.subheader("5. Zentrale Erkenntnisse")

positive_rate = (df["price_change_pct"] >= 0).mean() * 100
summary = f"""
**Analyse von {len(df)} Quartalen:**

- **Erfolgsquote:** In {positive_rate:.0f}% der Quartale reagierte die Aktie 30 Tage nach den Earnings positiv.
- **Saisonalitaet:** Das Quartal Q1 (Feiertagsquartal) liefert konsistent die hoechsten Umsaetze.
- **Statistische Signifikanz:** """

if len(clean) >= 3 and rev_pearson_p < 0.05:
    summary += "Es besteht ein statistisch signifikanter Zusammenhang zwischen dem iPhone-Umsatz und der Kursreaktion."
else:
    summary += "Der Zusammenhang ist statistisch nicht signifikant. Dies deutet darauf hin, dass der Markt Erwartungen bereits einpreist und nur Abweichungen von diesen Erwartungen den Kurs treiben."

st.markdown(summary)
st.caption("Datenquelle: Apple Investor Relations / Statista. Manuelle Pflege in data/iphone_sales.csv erforderlich.")
