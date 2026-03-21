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

    # --- Shared CSS for styled boxes ---
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
    .section-banner {
        display: flex; align-items: center; gap: 14px;
        padding: 14px 22px; border-radius: 10px;
        margin-bottom: 20px; margin-top: 10px;
    }
    .section-banner-blue  { background: linear-gradient(90deg, rgba(37,99,235,0.08), rgba(37,99,235,0.01)); border-left: 3px solid #2563eb; }
    .section-banner-green { background: linear-gradient(90deg, rgba(22,163,74,0.08), rgba(22,163,74,0.01)); border-left: 3px solid #16a34a; }
    .section-banner-purple { background: linear-gradient(90deg, rgba(124,58,237,0.08), rgba(124,58,237,0.01)); border-left: 3px solid #7c3aed; }
    .section-banner-orange { background: linear-gradient(90deg, rgba(217,119,6,0.08), rgba(217,119,6,0.01)); border-left: 3px solid #d97706; }
    .section-icon  { font-size: 1.5rem; line-height: 1; }
    .section-title { font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700; margin: 0; }
    .info-box {
        background: rgba(37,99,235,0.04); border: 1px solid rgba(37,99,235,0.15);
        border-radius: 12px; padding: 24px 28px; margin-bottom: 16px;
        line-height: 1.75; font-size: 1.08rem;
    }
    .info-box .hl { color: #2563eb; font-weight: 600; }
    .insight-card {
        background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.1);
        border-radius: 12px; padding: 22px 22px 20px; margin-bottom: 16px;
        transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
    }
    .insight-card:hover {
        border-color: #2563eb; transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(37,99,235,0.1);
    }
    .card-icon-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
    .card-icon {
        font-size: 1.4rem; width: 40px; height: 40px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 8px; flex-shrink: 0;
    }
    .icon-blue   { background: rgba(37,99,235,0.12); }
    .icon-green  { background: rgba(22,163,74,0.12); }
    .icon-orange { background: rgba(217,119,6,0.12); }
    .icon-purple { background: rgba(124,58,237,0.12); }
    .icon-red    { background: rgba(220,38,38,0.12); }
    .card-title { font-family: 'Syne', sans-serif; font-size: 1.08rem; font-weight: 700; margin: 0; }
    .card-body  { font-size: 1rem; line-height: 1.65; margin: 0; opacity: 0.75; }
    /* ── process flow ── */
    .process-flow {
        display: flex; gap: 0; margin-bottom: 24px;
        position: relative;
    }
    .process-step {
        flex: 1; text-align: center; padding: 24px 16px 20px;
        position: relative;
        background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.08);
        border-radius: 12px; margin: 0 6px;
        transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
    }
    .process-step:hover {
        border-color: #2563eb; transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(37,99,235,0.1);
    }
    .process-circle {
        width: 48px; height: 48px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 12px; font-size: 1.2rem;
        font-family: 'Syne', sans-serif; font-weight: 800;
        color: white;
    }
    .circle-1 { background: linear-gradient(135deg, #2563eb, #3b82f6); }
    .circle-2 { background: linear-gradient(135deg, #7c3aed, #8b5cf6); }
    .circle-3 { background: linear-gradient(135deg, #d97706, #f59e0b); }
    .circle-4 { background: linear-gradient(135deg, #16a34a, #22c55e); }
    .process-title {
        font-family: 'Syne', sans-serif; font-size: 0.95rem;
        font-weight: 700; margin: 0 0 6px 0;
    }
    .process-desc {
        font-size: 0.88rem; line-height: 1.5; margin: 0; opacity: 0.65;
    }
    .process-arrow {
        position: absolute; right: -14px; top: 50%; transform: translateY(-50%);
        font-size: 1.2rem; color: #cbd5e0; z-index: 2;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- WHAT IS THIS? ---
    st.markdown("""
    <div class="section-banner section-banner-blue">
        <span class="section-icon">📖</span>
        <p class="section-title">What Does This Analysis Show?</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="info-box">
        This page measures <span class="hl">how much money you could lose on a single bad day</span>
        when investing in Apple or NVIDIA stock. We use two well-established risk metrics from
        financial risk management:
        <br><br>
        <strong>Value-at-Risk (VaR)</strong> answers: <em>"What is the worst daily loss I can expect
        under normal conditions?"</em> At a <span class="hl">{conf_level*100:.1f}% confidence level</span>,
        the VaR tells you that on {conf_level*100:.0f} out of 100 trading days, your loss will
        <strong>not</strong> exceed this value. Only on the remaining {(1-conf_level)*100:.0f} out of
        100 days could losses be larger.
        <br><br>
        <strong>Expected Shortfall (ES)</strong>, also called Conditional VaR, goes one step further:
        <em>"If the worst case does happen, if the loss exceeds the VaR, how bad does it get on average?"</em>
        It is the average loss on those very worst days.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section-banner section-banner-purple">
        <span class="section-icon">⚙️</span>
        <p class="section-title">How It Works</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="process-flow">
        <div class="process-step">
            <div class="process-circle circle-1">01</div>
            <p class="process-title">Daily Returns</p>
            <p class="process-desc">Collect all historical daily percentage changes for each stock.</p>
            <span class="process-arrow">→</span>
        </div>
        <div class="process-step">
            <div class="process-circle circle-2">02</div>
            <p class="process-title">Historical Simulation</p>
            <p class="process-desc">Use actual past returns instead of assuming a mathematical distribution.</p>
            <span class="process-arrow">→</span>
        </div>
        <div class="process-step">
            <div class="process-circle circle-3">03</div>
            <p class="process-title">Worst Percentile</p>
            <p class="process-desc">Read off the VaR at the chosen confidence level, the dashed line in the chart.</p>
            <span class="process-arrow">→</span>
        </div>
        <div class="process-step">
            <div class="process-circle circle-4">04</div>
            <p class="process-title">Expected Shortfall</p>
            <p class="process-desc">Average all returns beyond the VaR threshold, the true worst-case average.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- ANALYSIS WITH ACTUAL NUMBERS ---
    st.markdown("""
    <div class="section-banner section-banner-green">
        <span class="section-icon">📊</span>
        <p class="section-title">Analysis and Interpretation</p>
    </div>
    """, unsafe_allow_html=True)

    if show_apple and ret_a is not None and show_nvidia and ret_n is not None:
        riskier = "NVIDIA" if v_n < v_a else "Apple"
        safer = "Apple" if riskier == "NVIDIA" else "NVIDIA"
        riskier_var = v_n if riskier == "NVIDIA" else v_a
        safer_var = v_a if riskier == "NVIDIA" else v_n
        riskier_es = e_n if riskier == "NVIDIA" else e_a
        safer_es = e_a if riskier == "NVIDIA" else e_n

        st.markdown(f"""
    <div class="info-box">
        At the <span class="hl">{conf_level*100:.1f}% confidence level</span>, the results show:
        <br><br>
        <strong>{riskier} carries significantly more risk than {safer}.</strong>
        A VaR of <span class="hl">{riskier_var:.2%}</span> means that on the worst
        {(1-conf_level)*100:.0f}% of trading days, {riskier} loses more than {abs(riskier_var):.2%}
        of its value in a single day. For {safer}, this threshold is {abs(safer_var):.2%}.
        <br><br>
        The Expected Shortfall paints an even clearer picture: when {riskier} does have a bad day
        beyond its VaR, the average loss is <span class="hl">{riskier_es:.2%}</span>, compared to
        <span class="hl">{safer_es:.2%}</span> for {safer}.
        <br><br>
        <strong>In practical terms:</strong> If you invested <span class="hl">$10,000</span> in each stock,
        on a bad day (beyond the {conf_level*100:.0f}% threshold):
        <br>• <strong>{safer}</strong> would lose on average <strong>${abs(safer_es) * 10000:.0f}</strong>
        <br>• <strong>{riskier}</strong> would lose on average <strong>${abs(riskier_es) * 10000:.0f}</strong>
    </div>
        """, unsafe_allow_html=True)

    elif show_apple and ret_a is not None:
        st.markdown(f"""
    <div class="info-box">
        At the <span class="hl">{conf_level*100:.1f}% confidence level</span>, Apple's VaR is
        <span class="hl">{v_a:.2%}</span>. On {(1-conf_level)*100:.0f} out of 100 trading days,
        Apple could lose more than {abs(v_a):.2%} of its value. When those worst days occur,
        the average loss is <span class="hl">{e_a:.2%}</span>.
        <br><br>
        On a <span class="hl">$10,000 investment</span>, that translates to an average worst-case
        loss of <strong>${abs(e_a) * 10000:.0f}</strong>.
    </div>
        """, unsafe_allow_html=True)

    elif show_nvidia and ret_n is not None:
        st.markdown(f"""
    <div class="info-box">
        At the <span class="hl">{conf_level*100:.1f}% confidence level</span>, NVIDIA's VaR is
        <span class="hl">{v_n:.2%}</span>. On {(1-conf_level)*100:.0f} out of 100 trading days,
        NVIDIA could lose more than {abs(v_n):.2%} of its value. When those worst days occur,
        the average loss is <span class="hl">{e_n:.2%}</span>.
        <br><br>
        On a <span class="hl">$10,000 investment</span>, that translates to an average worst-case
        loss of <strong>${abs(e_n) * 10000:.0f}</strong>.
    </div>
        """, unsafe_allow_html=True)

    # --- KEY INSIGHTS ---
    st.markdown("""
    <div class="section-banner section-banner-orange">
        <span class="section-icon">🔍</span>
        <p class="section-title">Key Insights</p>
    </div>
    """, unsafe_allow_html=True)

    if show_apple and ret_a is not None and show_nvidia and ret_n is not None:
        col_i1, col_i2 = st.columns(2)
        with col_i1:
            st.markdown(f"""
            <div class="insight-card">
                <div class="card-icon-row">
                    <div class="card-icon icon-red">⚖️</div>
                    <p class="card-title">Risk Comparison</p>
                </div>
                <p class="card-body">
                    {riskier} is the riskier asset. Its VaR is {abs(riskier_var/safer_var):.1f}x larger
                    than {safer}'s, meaning the potential for extreme daily losses is substantially higher.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class="insight-card">
                <div class="card-icon-row">
                    <div class="card-icon icon-orange">⚡</div>
                    <p class="card-title">Volatility Gap</p>
                </div>
                <p class="card-body">
                    NVIDIA's daily volatility ({ret_n.std():.2%}) vs. Apple's ({ret_a.std():.2%}) reflects
                    NVIDIA's nature as a high-growth semiconductor stock with larger price swings driven
                    by AI demand cycles, earnings surprises, and sector rotation.
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col_i2:
            st.markdown("""
            <div class="insight-card">
                <div class="card-icon-row">
                    <div class="card-icon icon-purple">📉</div>
                    <p class="card-title">Tail Risk Matters</p>
                </div>
                <p class="card-body">
                    The Expected Shortfall is always worse than the VaR. When a truly bad day happens,
                    losses don't just barely cross the VaR line, they tend to go significantly beyond it.
                    Risk models that only look at VaR underestimate the true downside.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="insight-card">
                <div class="card-icon-row">
                    <div class="card-icon icon-blue">🎚️</div>
                    <p class="card-title">Confidence Level Sensitivity</p>
                </div>
                <p class="card-body">
                    Try adjusting the confidence slider in the sidebar. A higher confidence level
                    (e.g. 99%) reveals more extreme tail risks, while a lower level (e.g. 90%)
                    shows more moderate, frequent losses.
                </p>
            </div>
            """, unsafe_allow_html=True)

    elif show_apple and ret_a is not None:
        st.markdown(f"""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-blue">🍎</div>
                <p class="card-title">Apple's Risk Profile</p>
            </div>
            <p class="card-body">
                With a VaR of {v_a:.2%}, Apple shows the relatively moderate risk profile typical of a
                mega-cap stock with diversified revenue streams (iPhone, Services, Mac, Wearables).
            </p>
        </div>
        """, unsafe_allow_html=True)

    elif show_nvidia and ret_n is not None:
        st.markdown(f"""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-green">🟢</div>
                <p class="card-title">NVIDIA's Risk Profile</p>
            </div>
            <p class="card-body">
                With a VaR of {v_n:.2%}, NVIDIA carries the higher volatility typical of a growth-oriented
                semiconductor company at the center of the AI hardware boom.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # --- WHY DOES THIS MATTER ---
    st.markdown("""
    <div class="section-banner section-banner-blue">
        <span class="section-icon">💡</span>
        <p class="section-title">Why Does This Matter?</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        Understanding these risk metrics helps investors make informed decisions about
        <span class="hl">portfolio allocation</span>. A risk-averse investor might prefer a larger
        allocation to lower-VaR stocks, while a risk-tolerant investor might accept higher potential
        losses in exchange for higher expected returns.
        <br><br>
        Banks and funds are <span class="hl">legally required</span> to calculate VaR daily to ensure
        they hold enough capital to survive worst-case scenarios, a regulation established after the
        2008 financial crisis through the Basel III framework.
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <section class="research-header">
            <p class="research-header__eyebrow">Answer to the Research Question</p>
            <p class="research-header__question">
                NVIDIA carries significantly higher risk than Apple across all metrics. Its Value-at-Risk and Expected Shortfall are substantially larger, reflecting higher daily volatility driven by its position as a high-growth semiconductor stock exposed to AI demand cycles. Apple, as a diversified mega-cap, shows a more moderate risk profile. The Expected Shortfall consistently exceeds the VaR for both stocks, confirming that extreme losses tend to go well beyond the worst-case threshold, underscoring the importance of tail-risk-aware models over simple VaR-only approaches.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

else:
    st.info("Please select at least one asset in the sidebar.")
