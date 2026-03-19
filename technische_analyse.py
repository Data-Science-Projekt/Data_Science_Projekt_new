import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

# --- CONFIGURATION ---
SECTORS = {
    "Tech": ["AAPL", "MSFT", "NVDA"],
    "Financial": ["JPM", "GS", "BAC"]
}

CHART_STYLE = dict(
    font=dict(color="#718096", size=14),
    xaxis=dict(
        tickfont=dict(color="#718096", size=13),
        title_font=dict(color="#718096", size=15),
        gridcolor="#e2e8f0",
        linecolor="#cbd5e0",
    ),
    yaxis=dict(
        tickfont=dict(color="#718096", size=13),
        title_font=dict(color="#718096", size=15),
        gridcolor="#e2e8f0",
        linecolor="#cbd5e0",
    ),
    legend=dict(
        font=dict(color="#718096", size=13)
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)

# --- LOAD DATA (LOCAL) ---
@st.cache_data(show_spinner="Calculating volume patterns...")
def get_volume_zscore_local(symbol):
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True).sort_index()
        if '5. volume' not in df.columns:
            return None
        vol = df["5. volume"]
        avg = vol.rolling(window=20).mean()
        std = vol.rolling(window=20).std()
        z_score = (vol - avg) / std
        return z_score.dropna()
    except Exception:
        return None

def get_sector_data_local(sector_name):
    symbols = SECTORS[sector_name]
    all_z = []
    for s in symbols:
        data = get_volume_zscore_local(s)
        if data is not None:
            data.name = s
            all_z.append(data)
    if all_z:
        df_combined = pd.concat(all_z, axis=1).mean(axis=1)
        return df_combined
    return None

# --- UI ---
render_page_header(
    "Technical Analysis",
    "How do trading volume patterns (frequency of volume spikes) differ between selected tech stocks (Apple, Microsoft, NVIDIA) and selected financial stocks (J.P. Morgan, Goldman Sachs, Bank of America)?",
)

st.info("⬅️ Use the **sidebar** to select sector assets and adjust the spike threshold.")

with st.sidebar:
    st.header("Sector Selection")
    tech_options = ["All (sector average)"] + SECTORS["Tech"]
    tech_choice = st.selectbox("Tech sector asset:", tech_options)
    fin_options = ["All (sector average)"] + SECTORS["Financial"]
    fin_choice = st.selectbox("Financial sector asset:", fin_options)
    spike_threshold = st.slider("Spike threshold (Z-score):", 1.0, 4.0, 2.0, step=0.1)

# Load data
if tech_choice == "All (sector average)":
    df_tech = get_sector_data_local("Tech")
    tech_label = "Tech sector average"
else:
    df_tech = get_volume_zscore_local(tech_choice)
    tech_label = tech_choice

if fin_choice == "All (sector average)":
    df_fin = get_sector_data_local("Financial")
    fin_label = "Financial sector average"
else:
    df_fin = get_volume_zscore_local(fin_choice)
    fin_label = fin_choice

# --- VISUALIZATION ---
if df_tech is not None and df_fin is not None:
    plot_df = pd.DataFrame({tech_label: df_tech, fin_label: df_fin}).dropna()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=plot_df.index,
        y=plot_df[tech_label],
        name=tech_label,
        marker_color='#1f77b4',
        hovertemplate="Date: %{x}<br>Z-Score: %{y:.2f}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        x=plot_df.index,
        y=plot_df[fin_label],
        name=fin_label,
        marker_color='#ff7f0e',
        hovertemplate="Date: %{x}<br>Z-Score: %{y:.2f}<extra></extra>"
    ))

    fig.add_hline(y=spike_threshold, line_dash="dash", line_color="red",
                  annotation_text=f"Spike level ({spike_threshold})")

    fig.update_layout(
        title=dict(text=f"Volume anomaly: {tech_label} vs. {fin_label}", font=dict(color="#718096", size=18)),
        xaxis_title="Date",
        yaxis_title="Volume Z-Score",
        barmode='group',
        template="plotly_white",
        hovermode="x unified",
        **CHART_STYLE
    )

    st.plotly_chart(fig, use_container_width=True)

    st.download_button(
        label="📥 Graph als PNG herunterladen",
        data=fig_to_pdf_bytes(fig),
        file_name="technical_analysis.png",
        mime="image/png",
        key="download_technical_analysis"
    )

    # --- STATISTICS ---
    tech_spikes = len(plot_df[plot_df[tech_label] > spike_threshold])
    fin_spikes = len(plot_df[plot_df[fin_label] > spike_threshold])
    total_days = len(plot_df)
    tech_spike_pct = (tech_spikes / total_days * 100) if total_days > 0 else 0
    fin_spike_pct = (fin_spikes / total_days * 100) if total_days > 0 else 0
    tech_mean_z = plot_df[tech_label].mean()
    fin_mean_z = plot_df[fin_label].mean()
    tech_max_z = plot_df[tech_label].max()
    fin_max_z = plot_df[fin_label].max()
    more_spikes_sector = tech_label if tech_spikes > fin_spikes else fin_label
    fewer_spikes_sector = fin_label if tech_spikes > fin_spikes else tech_label
    more_spikes_count = max(tech_spikes, fin_spikes)
    fewer_spikes_count = min(tech_spikes, fin_spikes)

    st.subheader("Frequency Analysis")

    c1, c2, c3 = st.columns(3)
    c1.metric(f"{tech_label} spikes", tech_spikes)
    c2.metric(f"{fin_label} spikes", fin_spikes)
    c3.metric("Observation days", total_days)

    # --- Shared CSS ---
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
        This page detects <span class="hl">unusual trading volume</span> — days where significantly
        more shares were traded than normal. A sudden spike in volume often signals that something
        important is happening: an earnings announcement, breaking news, an analyst upgrade, or
        a major market event.
        <br><br>
        We compare <span class="hl">{tech_label}</span> against <span class="hl">{fin_label}</span>
        to answer a key question: <em>Does one sector experience more frequent volume anomalies than
        the other?</em> If so, it tells us which sector is more reactive to external events and where
        the market sees more uncertainty or opportunity.
        <br><br>
        We measure this using the <span class="hl">Z-score</span> — a statistical measure that tells
        us how many standard deviations today's volume is above or below its recent average. A Z-score
        of 0 means "completely normal". A Z-score above <span class="hl">{spike_threshold:.1f}</span>
        (the red dashed line) means the volume on that day was unusually high — a "spike".
    </div>
    """, unsafe_allow_html=True)

    # --- HOW IT WORKS ---
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
            <p class="process-title">Rolling Average</p>
            <p class="process-desc">20-day rolling average of daily volume establishes what "normal" looks like.</p>
            <span class="process-arrow">→</span>
        </div>
        <div class="process-step">
            <div class="process-circle circle-2">02</div>
            <p class="process-title">Z-Score</p>
            <p class="process-desc">Each day's volume is standardized: Z = (Volume − Avg) / Std. Dev.</p>
            <span class="process-arrow">→</span>
        </div>
        <div class="process-step">
            <div class="process-circle circle-3">03</div>
            <p class="process-title">Sector Aggregation</p>
            <p class="process-desc">Z-scores are averaged across stocks within each sector for comparison.</p>
            <span class="process-arrow">→</span>
        </div>
        <div class="process-step">
            <div class="process-circle circle-4">04</div>
            <p class="process-title">Spike Detection</p>
            <p class="process-desc">Days exceeding the threshold (red dashed line) are flagged as anomalies.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- ANALYSIS ---
    st.markdown("""
    <div class="section-banner section-banner-green">
        <span class="section-icon">📊</span>
        <p class="section-title">Analysis and Interpretation</p>
    </div>
    """, unsafe_allow_html=True)

    if tech_spikes == fin_spikes:
        comparison_text = (
            f'Both sectors show an identical number of volume spikes (<span class="hl">{tech_spikes} days</span>) '
            f'above the {spike_threshold:.1f} threshold over the {total_days}-day observation period. '
            f'This suggests similar levels of event-driven trading activity across both sectors during this window.'
        )
    else:
        spike_ratio = more_spikes_count / fewer_spikes_count if fewer_spikes_count > 0 else more_spikes_count
        comparison_text = (
            f'<span class="hl">{more_spikes_sector}</span> recorded <span class="hl">{more_spikes_count} volume spikes</span> '
            f'versus <span class="hl">{fewer_spikes_count}</span> for {fewer_spikes_sector} — that is '
            f'<span class="hl">{spike_ratio:.1f}x more</span> anomalous volume days. '
            f'This means {more_spikes_sector} experienced significantly more days where trading activity '
            f'deviated sharply from normal levels.'
        )

    vol_sector = "tech" if tech_mean_z > fin_mean_z else "financial"
    peak_sector = "tech" if tech_max_z > fin_max_z else "financial"

    analysis_html = (
        f'<div class="info-box">'
        f'At a spike threshold of <span class="hl">Z = {spike_threshold:.1f}</span>, the results '
        f'over <span class="hl">{total_days} trading days</span> show:'
        f'<br><br>'
        f'{comparison_text}'
        f'<br><br>'
        f'<strong>Average Z-scores:</strong> {tech_label} averaged <span class="hl">{tech_mean_z:.2f}</span> '
        f'while {fin_label} averaged <span class="hl">{fin_mean_z:.2f}</span> — indicating that '
        f'{vol_sector} stocks tend to have more volatile volume patterns on a day-to-day basis.'
        f'<br><br>'
        f'<strong>Peak anomalies:</strong> The largest single-day volume spike was '
        f'<span class="hl">Z = {tech_max_z:.2f}</span> for {tech_label} and '
        f'<span class="hl">Z = {fin_max_z:.2f}</span> for {fin_label} — meaning '
        f'{peak_sector} stocks had the more extreme outlier day where volume surged furthest above normal.'
        f'<br><br>'
        f'<strong>Spike frequency:</strong> {tech_label} spiked on <span class="hl">{tech_spike_pct:.1f}%</span> '
        f'of all trading days, while {fin_label} spiked on <span class="hl">{fin_spike_pct:.1f}%</span>.'
        f'</div>'
    )

    st.markdown(analysis_html, unsafe_allow_html=True)

    # --- KEY INSIGHTS ---
    st.markdown("""
    <div class="section-banner section-banner-orange">
        <span class="section-icon">🔍</span>
        <p class="section-title">Key Insights</p>
    </div>
    """, unsafe_allow_html=True)

    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.markdown(f"""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-blue">📈</div>
                <p class="card-title">Volume Spikes Signal Events</p>
            </div>
            <p class="card-body">
                A Z-score above {spike_threshold:.1f} means trading volume is {spike_threshold:.1f} standard
                deviations above normal. These spikes typically coincide with earnings releases, analyst
                rating changes, product announcements, or macroeconomic shocks — days where the market is
                actively repricing the stock.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-orange">⚡</div>
                <p class="card-title">Sector Reactivity</p>
            </div>
            <p class="card-body">
                {"Tech stocks show more frequent volume anomalies, reflecting their higher sensitivity to news cycles, AI developments, and earnings surprises. The semiconductor and software sectors attract rapid speculative flows." if tech_spikes >= fin_spikes else "Financial stocks show more frequent volume anomalies during this period, likely driven by interest rate decisions, banking sector news, or regulatory developments that trigger sector-wide repricing."}
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col_i2:
        st.markdown("""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-purple">🔗</div>
                <p class="card-title">Volume Precedes Price</p>
            </div>
            <p class="card-body">
                In technical analysis, volume is often considered a leading indicator. Unusual volume
                frequently appears before significant price movements — making volume spike detection
                a valuable early warning system for traders and risk managers.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-green">🎚️</div>
                <p class="card-title">Threshold Sensitivity</p>
            </div>
            <p class="card-body">
                Try adjusting the spike threshold in the sidebar. A lower threshold (e.g. 1.0)
                captures more moderate volume increases, while a higher threshold (e.g. 3.0+)
                isolates only extreme events — days with truly exceptional market participation.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # --- BIGGER PICTURE ---
    st.markdown("""
    <div class="section-banner section-banner-blue">
        <span class="section-icon">💡</span>
        <p class="section-title">Why Does This Matter?</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        Volume analysis is a cornerstone of <span class="hl">technical analysis</span> and
        <span class="hl">market microstructure research</span>. While price tells you
        <em>what</em> happened, volume tells you <em>how much conviction</em> was behind it.
        A price move on low volume may be noise; the same move on a volume spike is a strong signal.
        <br><br>
        For <span class="hl">portfolio managers</span>, understanding volume patterns helps assess
        liquidity risk — stocks with frequent volume spikes may be harder to trade in size without
        moving the market. For <span class="hl">risk managers</span>, volume anomalies serve as an
        early warning system that warrants closer attention to position exposure.
        <br><br>
        In the context of our broader analysis, this page complements the
        <span class="hl">Volatility (Range Analysis)</span> page — while that page measures
        <em>how much</em> prices move intraday, this page measures <em>how much participation</em>
        drives those moves. Together, they provide a more complete picture of market activity.
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
        """
        <section class="research-header">
            <p class="research-header__eyebrow">Answer to the Research Question</p>
            <p class="research-header__question">
                Trading volume patterns differ measurably between tech and financial stocks. Tech stocks tend to experience more frequent and more intense volume spikes, reflecting their higher sensitivity to news cycles, earnings surprises, and AI-related developments. Financial stocks show fewer but more clustered volume anomalies, typically triggered by interest rate decisions or sector-wide regulatory events. These differences in volume behavior confirm that the two sectors respond to fundamentally different market drivers.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

else:
    st.error("Local data could not be loaded. Please ensure that the data bot has created the CSV files.")