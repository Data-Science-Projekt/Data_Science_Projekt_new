import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

# --- HILFSFUNKTIONEN ---
try:
    from analysis.utils import render_page_header
except ImportError:
    def render_page_header(title, subtitle):
        st.title(title)
        st.write(subtitle)

# --- CONFIG ---
STOCKS = {"Apple": "AAPL", "NVIDIA": "NVDA"}

@st.cache_data(show_spinner=False)
def get_local_stock_returns(symbol):
    """Liest lokale Aktiendaten und berechnet die taeglichen Renditen."""
    file_path = f"data/stock_{symbol}.csv"
    
    if not os.path.exists(file_path):
        return None
        
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        df = df.astype(float).sort_index()
        # Berechnung der prozentualen Veraenderung (Renditen)
        return df['4. close'].pct_change().dropna()
    except Exception:
        return None

# --- SIDEBAR ---
st.sidebar.header("Risk Settings")
conf_level = st.sidebar.slider("Confidence level (%)", 90.0, 99.0, 95.0, 0.5) / 100
st.sidebar.divider()
show_apple = st.sidebar.checkbox("Show Apple (AAPL)", value=True, key="risk_a")
show_nvidia = st.sidebar.checkbox("Show NVIDIA (NVDA)", value=True, key="risk_n")

render_page_header(
    "Risk Management",
    f"What is the maximum expected loss (at a {conf_level*100:.1f}% confidence level) for Apple compared to NVIDIA over a 1-day horizon?"
)

st.info("⬅️ Use the **sidebar** to adjust the confidence level and select stocks.")

# --- DATA LOADING ---
ret_a = None
ret_n = None

if show_apple:
    ret_a = get_local_stock_returns(STOCKS["Apple"])
if show_nvidia:
    ret_n = get_local_stock_returns(STOCKS["NVIDIA"])

# --- PLOTTING ---
if (show_apple and ret_a is not None) or (show_nvidia and ret_n is not None):
    fig = go.Figure()

    if show_apple and ret_a is not None:
        # Historische Simulation des VaR
        v_a = np.percentile(ret_a, (1 - conf_level) * 100)
        # Expected Shortfall
        e_a = ret_a[ret_a <= v_a].mean()
        
        fig.add_trace(go.Histogram(
            x=ret_a, 
            name="Apple", 
            marker_color='#1f77b4', 
            opacity=0.6, 
            nbinsx=50,
            hovertemplate="Avg Return: %{x:.2%}<br>Frequency: %{y:.0f}<extra></extra>"
        ))
        
        # Vertikale Linie fuer Apple
        fig.add_vline(x=v_a, line_dash="dash", line_color="#1f77b4")
        
        # TEXT-ANNOTATION APPLE (Fixierte Hoehe 95%)
        fig.add_annotation(
            x=v_a,               # Anker an der X-Position des VaR
            y=0.95,              # 95% der vertikalen Charthoehe
            yref="paper",        # Referenz auf das Chart-Fenster (0 bis 1)
            xref="x",            # Referenz auf die Daten-Achse
            text=f"VaR AAPL: {v_a:.2%}",
            showarrow=False,
            font=dict(color="#1f77b4", size=12),
            align="left",
            xanchor="left",      # Text fließt nach RECHTS weg
            xshift=5             # Kleiner horizontaler Abstand zur Linie
        )

    if show_nvidia and ret_n is not None:
        v_n = np.percentile(ret_n, (1 - conf_level) * 100)
        e_n = ret_n[ret_n <= v_n].mean()
        
        fig.add_trace(go.Histogram(
            x=ret_n, 
            name="NVIDIA", 
            marker_color='#ff7f0e', 
            opacity=0.6, 
            nbinsx=50,
            hovertemplate="Avg Return: %{x:.2%}<br>Frequency: %{y:.0f}<extra></extra>"
        ))
        
        # Vertikale Linie fuer NVIDIA
        fig.add_vline(x=v_n, line_dash="dash", line_color="#ff7f0e")
        
        # TEXT-ANNOTATION NVIDIA (Fixierte Hoehe 95%)
        fig.add_annotation(
            x=v_n,               # Anker an der X-Position des VaR
            y=0.95,              # EBENFALLS 95% der vertikalen Charthoehe
            yref="paper",        # Referenz auf das Chart-Fenster (0 bis 1)
            xref="x",            # Referenz auf die Daten-Achse
            text=f"VaR NVDA: {v_n:.2%}",
            showarrow=False,
            font=dict(color="#ff7f0e", size=12),
            align="right",
            xanchor="right",     # Text fließt nach LINKS weg
            xshift=-5            # Kleiner horizontaler Abstand zur Linie
        )

    # Layout-Anpassungen
    fig.update_layout(
        barmode='overlay',
        xaxis_title="Daily Return",
        yaxis_title="Frequency",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=80, b=50), 
        hovermode="closest"
    )

    # Chart ausgeben mit Streamlit-Theme fuer autom. Farbanpassung (Light/Dark)
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    st.download_button(
        label="📥 Graph als PNG herunterladen",
        data=fig_to_pdf_bytes(fig),
        file_name="technical_analysis.png",
        mime="image/png",
    )

    # Metrics unter dem Chart
    c1, c2 = st.columns(2)
    if show_apple and ret_a is not None:
        c1.subheader("Apple (AAPL)")
        c1.metric("Value-at-Risk", f"{v_a:.2%}")
        c1.metric("Expected Shortfall", f"{e_a:.2%}")
    if show_nvidia and ret_n is not None:
        c2.subheader("NVIDIA (NVDA)")
        c2.metric("Value-at-Risk", f"{v_n:.2%}")
        c2.metric("Expected Shortfall", f"{e_n:.2%}")

    # --- WHAT IS THIS? ---
    st.markdown("---")
    st.subheader("What Does This Analysis Show?")
    st.markdown(f"""
    This page measures **how much money you could lose on a single bad day** when investing in Apple or NVIDIA stock.
    We use two well-established risk metrics from financial risk management:

    - **Value-at-Risk (VaR)** answers the question: *"What is the worst daily loss I can expect
      under normal conditions?"* At a **{conf_level*100:.1f}% confidence level**, the VaR tells you
      that on {conf_level*100:.0f} out of 100 trading days, your loss will **not** exceed this value.
      Only on the remaining {(1-conf_level)*100:.0f} out of 100 days could losses be larger.
    - **Expected Shortfall (ES)**, also called Conditional VaR, goes one step further: *"If the worst
      case does happen — if the loss exceeds the VaR — how bad does it get on average?"*
      It is the average loss on those very worst days.

    **Method:** We use **Historical Simulation** — instead of assuming a mathematical distribution,
    we look at the actual historical daily returns and simply read off the worst percentiles.
    The histogram above shows every daily return that occurred in our dataset. The dashed vertical
    lines mark the VaR threshold for each stock.
    """)

    # --- ANALYSIS WITH ACTUAL NUMBERS ---
    st.subheader("Analysis and Interpretation")

    if show_apple and ret_a is not None and show_nvidia and ret_n is not None:
        riskier = "NVIDIA" if v_n < v_a else "Apple"
        safer = "Apple" if riskier == "NVIDIA" else "NVIDIA"
        riskier_var = v_n if riskier == "NVIDIA" else v_a
        safer_var = v_a if riskier == "NVIDIA" else v_n
        riskier_es = e_n if riskier == "NVIDIA" else e_a
        safer_es = e_a if riskier == "NVIDIA" else e_n

        st.markdown(f"""
    At the **{conf_level*100:.1f}% confidence level**, the results show:

    | Metric | Apple (AAPL) | NVIDIA (NVDA) |
    |--------|-------------|---------------|
    | **Value-at-Risk** | {v_a:.2%} | {v_n:.2%} |
    | **Expected Shortfall** | {e_a:.2%} | {e_n:.2%} |
    | **Volatility (Std. Dev.)** | {ret_a.std():.2%} | {ret_n.std():.2%} |
    | **Trading Days Analyzed** | {len(ret_a):,} | {len(ret_n):,} |

    **{riskier} carries significantly more risk than {safer}.** A VaR of **{riskier_var:.2%}** means
    that on the worst {(1-conf_level)*100:.0f}% of trading days, {riskier} loses more than
    {abs(riskier_var):.2%} of its value in a single day. For {safer}, this threshold is
    {abs(safer_var):.2%}.

    The Expected Shortfall paints an even clearer picture: when {riskier} does have a bad day
    beyond its VaR, the average loss is **{riskier_es:.2%}** — compared to **{safer_es:.2%}** for {safer}.

    **In practical terms:** If you invested **$10,000** in each stock, on a bad day
    (beyond the {conf_level*100:.0f}% threshold):
    - **{safer}** would lose on average **${abs(safer_es) * 10000:.0f}**
    - **{riskier}** would lose on average **${abs(riskier_es) * 10000:.0f}**
        """)

    elif show_apple and ret_a is not None:
        st.markdown(f"""
    At the **{conf_level*100:.1f}% confidence level**, Apple's results:

    | Metric | Apple (AAPL) |
    |--------|-------------|
    | **Value-at-Risk** | {v_a:.2%} |
    | **Expected Shortfall** | {e_a:.2%} |
    | **Volatility (Std. Dev.)** | {ret_a.std():.2%} |
    | **Trading Days Analyzed** | {len(ret_a):,} |

    On {(1-conf_level)*100:.0f} out of 100 trading days, Apple could lose more than **{abs(v_a):.2%}**
    of its value. When those worst days occur, the average loss is **{e_a:.2%}**.
    On a **$10,000 investment**, that translates to an average worst-case loss of **${abs(e_a) * 10000:.0f}**.
        """)

    elif show_nvidia and ret_n is not None:
        st.markdown(f"""
    At the **{conf_level*100:.1f}% confidence level**, NVIDIA's results:

    | Metric | NVIDIA (NVDA) |
    |--------|---------------|
    | **Value-at-Risk** | {v_n:.2%} |
    | **Expected Shortfall** | {e_n:.2%} |
    | **Volatility (Std. Dev.)** | {ret_n.std():.2%} |
    | **Trading Days Analyzed** | {len(ret_n):,} |

    On {(1-conf_level)*100:.0f} out of 100 trading days, NVIDIA could lose more than **{abs(v_n):.2%}**
    of its value. When those worst days occur, the average loss is **{e_n:.2%}**.
    On a **$10,000 investment**, that translates to an average worst-case loss of **${abs(e_n) * 10000:.0f}**.
        """)

    # --- KEY INSIGHTS ---
    st.subheader("Key Insights")

    insights = []

    if show_apple and ret_a is not None and show_nvidia and ret_n is not None:
        insights.append(
            f"**Risk Comparison:** {riskier} is the riskier asset — its VaR is "
            f"{abs(riskier_var/safer_var):.1f}x larger than {safer}'s, meaning the potential "
            f"for extreme daily losses is substantially higher."
        )
        insights.append(
            f"**Volatility Gap:** NVIDIA's daily volatility ({ret_n.std():.2%}) vs. Apple's "
            f"({ret_a.std():.2%}) reflects NVIDIA's nature as a high-growth semiconductor stock "
            f"with larger price swings driven by AI demand cycles, earnings surprises, and sector rotation."
        )
        insights.append(
            "**Tail Risk Matters:** The Expected Shortfall is always worse than the VaR. "
            "This means that when a truly bad day happens, losses don't just barely cross the "
            "VaR line — they tend to go significantly beyond it. Risk models that only look at "
            "VaR underestimate the true downside."
        )
        insights.append(
            f"**Confidence Level Sensitivity:** Try adjusting the confidence slider in the sidebar. "
            f"A higher confidence level (e.g. 99%) reveals more extreme tail risks, while a lower "
            f"level (e.g. 90%) shows more moderate, frequent losses."
        )
    elif show_apple and ret_a is not None:
        insights.append(
            f"**Apple's Risk Profile:** With a VaR of {v_a:.2%}, Apple shows the relatively "
            f"moderate risk profile typical of a mega-cap stock with diversified revenue streams."
        )
    elif show_nvidia and ret_n is not None:
        insights.append(
            f"**NVIDIA's Risk Profile:** With a VaR of {v_n:.2%}, NVIDIA carries the higher "
            f"volatility typical of a growth-oriented semiconductor company."
        )

    for i, insight in enumerate(insights, 1):
        st.markdown(f"{i}. {insight}")

    st.markdown("""
---
**Why does this matter?**
Understanding these risk metrics helps investors make informed decisions about portfolio
allocation. A risk-averse investor might prefer a larger allocation to lower-VaR stocks,
while a risk-tolerant investor might accept higher potential losses in exchange for
higher expected returns. Banks and funds are legally required to calculate VaR daily
to ensure they hold enough capital to survive worst-case scenarios.
    """)

else:
    st.info("Please select at least one asset in the sidebar.")
