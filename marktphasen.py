import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes

# --- CONFIGURATION ---
STOCKS = {
    "Apple": "AAPL",
    "NVIDIA": "NVDA",
    "Microsoft": "MSFT",
    "J.P. Morgan": "JPM",
    "Goldman Sachs": "GS",
    "Bank of America": "BAC"
}

STOCK_COLORS = {
    "Apple": "#1f77b4",
    "NVIDIA": "#2ca02c",
    "Microsoft": "#ff7f0e",
    "J.P. Morgan": "#9467bd",
    "Goldman Sachs": "#d62728",
    "Bank of America": "#8c564b"
}

@st.cache_data(show_spinner="Loading local data...")
def get_stock_data(symbol):
    file_path = f"data/stock_{symbol}.csv"
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        df = df.sort_index()
        if '4. close' in df.columns:
            df.rename(columns={"4. close": "close"}, inplace=True)
        return df[["close"]]
    except Exception:
        return None


def identify_phases(df_input, bull_threshold, bear_threshold):
    df = df_input.copy()
    df['rolling_max'] = df['close'].rolling(window=20, min_periods=1).max()
    df['rolling_min'] = df['close'].rolling(window=20, min_periods=1).min()

    bear_limit = -bear_threshold / 100
    bull_limit = bull_threshold / 100

    df['phase'] = np.select(
        [
            (df['close'] - df['rolling_max']) / df['rolling_max'] <= bear_limit,
            (df['close'] - df['rolling_min']) / df['rolling_min'] >= bull_limit
        ],
        ['Bear', 'Bull'],
        default='Neutral'
    )
    return df


def add_phase_shading(fig, df):
    phase_colors = {
        "Bull": "rgba(0, 200, 100, 0.15)",
        "Bear": "rgba(220, 50, 50, 0.15)",
        "Neutral": "rgba(180, 180, 180, 0.07)"
    }

    df = df.reset_index()
    df.columns = ['date'] + list(df.columns[1:])

    segments = []
    current_phase = df['phase'].iloc[0]
    start_date = df['date'].iloc[0]

    for i in range(1, len(df)):
        if df['phase'].iloc[i] != current_phase:
            segments.append((start_date, df['date'].iloc[i - 1], current_phase))
            current_phase = df['phase'].iloc[i]
            start_date = df['date'].iloc[i]
    segments.append((start_date, df['date'].iloc[-1], current_phase))

    for seg_start, seg_end, phase in segments:
        fig.add_vrect(
            x0=seg_start, x1=seg_end,
            fillcolor=phase_colors.get(phase, "rgba(0,0,0,0)"),
            opacity=1.0, layer="below", line_width=0,
        )
    return fig


def build_stock_chart(stock, df_view, bull_threshold, bear_threshold):
    fig = go.Figure()
    fig = add_phase_shading(fig, df_view)

    fig.add_trace(go.Scatter(
        x=df_view.index, y=df_view['close'],
        name='Price', mode="lines",
        line=dict(color=STOCK_COLORS[stock], width=2.5),
        hovertemplate='%{x|%d.%m.%Y}<br>$%{y:.2f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(size=12, color='rgba(0, 200, 100, 0.6)', symbol='square'),
        name=f'Bull (>= +{bull_threshold}%)'
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(size=12, color='rgba(220, 50, 50, 0.6)', symbol='square'),
        name=f'Bear (<= -{bear_threshold}%)'
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='markers',
        marker=dict(size=12, color='rgba(180, 180, 180, 0.4)', symbol='square'),
        name='Neutral'
    ))

    fig.update_layout(
        title=dict(text=f"{stock}", font=dict(size=18, color="#718096")),
        template="plotly_white",
        xaxis_title="Date", yaxis_title="Price ($)",
        font=dict(color="#718096", size=14),
        xaxis=dict(tickfont=dict(color="#718096", size=13), title_font=dict(color="#718096", size=15), gridcolor="#e2e8f0", linecolor="#cbd5e0"),
        yaxis=dict(tickfont=dict(color="#718096", size=13), title_font=dict(color="#718096", size=15), gridcolor="#e2e8f0", linecolor="#cbd5e0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#718096", size=13)),
        hovermode="x unified", margin=dict(t=60), height=400,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# --- UI ---
render_page_header(
    "Market Phases",
    "How does the correlation between selected technology stocks (Apple, Microsoft, NVIDIA) and selected financial stocks (J.P. Morgan, Goldman Sachs, Bank of America) change during stable market periods compared to crisis periods (bear markets)?",
)

st.info("⬅️ Use the **sidebar** to select assets and adjust Bull/Bear thresholds.")

if "selected_stocks_multiselect" not in st.session_state:
    st.session_state["selected_stocks_multiselect"] = ["Apple", "NVIDIA"]

selected_stocks = st.sidebar.multiselect(
    "Select Assets:", list(STOCKS.keys()),
    key="selected_stocks_multiselect"
)

if not selected_stocks:
    st.warning("Please select at least one asset.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.subheader("Phase Thresholds")

bull_threshold = st.sidebar.slider(
    "Bull Market Threshold (%)", min_value=1, max_value=20, value=20, step=1,
    help="Minimum rise from rolling 20-day low to qualify as a Bull phase."
)
bear_threshold = st.sidebar.slider(
    "Bear Market Threshold (%)", min_value=1, max_value=20, value=20, step=1,
    help="Minimum drop from rolling 20-day high to qualify as a Bear phase."
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**Current Settings:**\n"
    f"- Bull: +{bull_threshold}% from 20d low\n"
    f"- Bear: -{bear_threshold}% from 20d high"
)

# --- LOAD DATA ---
all_data = {}
for stock in selected_stocks:
    df_raw = get_stock_data(STOCKS[stock])
    if df_raw is not None:
        all_data[stock] = identify_phases(df_raw, bull_threshold, bear_threshold)

if not all_data:
    st.error("No data could be loaded.")
    st.stop()

# --- CHARTS ---
stocks_list = list(all_data.items())

for i in range(0, len(stocks_list), 2):
    cols = st.columns(2)
    for j, col in enumerate(cols):
        if i + j >= len(stocks_list):
            break
        stock, df_view = stocks_list[i + j]
        with col:
            st.subheader(f"{stock}")
            fig = build_stock_chart(stock, df_view, bull_threshold, bear_threshold)
            st.plotly_chart(fig, use_container_width=True)
            st.download_button(
                label=f"{stock} als PNG",
                data=fig_to_pdf_bytes(fig),
                file_name=f"marktphasen_{stock.replace(' ', '_')}.png",
                mime="image/png",
                key=f"download_marktphasen_{stock}"
            )
            counts = df_view['phase'].value_counts()
            percentages = (counts / len(df_view) * 100).round(2)
            dist_df = pd.DataFrame({"Days": counts, "Share (%)": percentages})
            st.markdown(f"**Phase Distribution: {stock}**")
            st.table(dist_df)
    st.markdown("---")

# --- INTERPRETATION ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
.section-banner {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 22px; border-radius: 10px;
    margin-bottom: 20px; margin-top: 24px;
}
.section-banner-blue   { background: linear-gradient(90deg, rgba(37,99,235,0.08), rgba(37,99,235,0.01)); border-left: 3px solid #2563eb; }
.section-banner-green  { background: linear-gradient(90deg, rgba(22,163,74,0.08), rgba(22,163,74,0.01)); border-left: 3px solid #16a34a; }
.section-banner-purple { background: linear-gradient(90deg, rgba(124,58,237,0.08), rgba(124,58,237,0.01)); border-left: 3px solid #7c3aed; }
.section-banner-orange { background: linear-gradient(90deg, rgba(217,119,6,0.08), rgba(217,119,6,0.01)); border-left: 3px solid #d97706; }
.section-title { font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700; margin: 0; }
.info-box {
    background: rgba(37,99,235,0.04); border: 1px solid rgba(37,99,235,0.15);
    border-radius: 12px; padding: 24px 28px; margin-bottom: 16px;
    line-height: 1.75; font-size: 1.05rem;
}
.info-box .hl { color: #2563eb; font-weight: 600; }
.step-card {
    background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.08);
    border-radius: 12px; padding: 18px 20px; margin-bottom: 12px;
    display: flex; gap: 16px; align-items: flex-start;
    transition: border-color 0.2s, transform 0.2s;
}
.step-card:hover { border-color: #2563eb; transform: translateX(3px); }
.step-number {
    font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 800;
    color: #2563eb; opacity: 1; min-width: 44px; line-height: 1.2;
    background: rgba(37,99,235,0.1); border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    padding: 4px 8px; flex-shrink: 0;
}
.step-title { font-family: 'Syne', sans-serif; font-size: 1.05rem; font-weight: 700; margin: 0 0 3px 0; }
.step-desc  { font-size: 0.98rem; line-height: 1.55; margin: 0; opacity: 0.7; }
.insight-card {
    background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.1);
    border-radius: 12px; padding: 22px 22px 20px; margin-bottom: 16px;
    transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
}
.insight-card:hover { border-color: #2563eb; transform: translateY(-2px); box-shadow: 0 4px 16px rgba(37,99,235,0.1); }
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
</style>
""", unsafe_allow_html=True)

# --- DYNAMIC CALCULATIONS ---
phase_stats = {}
for stock, df in all_data.items():
    counts = df['phase'].value_counts()
    total = len(df)
    phase_stats[stock] = {
        "bull_pct":     round(counts.get("Bull", 0) / total * 100, 1),
        "bear_pct":     round(counts.get("Bear", 0) / total * 100, 1),
        "neutral_pct":  round(counts.get("Neutral", 0) / total * 100, 1),
        "bull_days":    counts.get("Bull", 0),
        "bear_days":    counts.get("Bear", 0),
        "neutral_days": counts.get("Neutral", 0),
        "total":        total,
    }

tech_stocks_selected = [s for s in selected_stocks if STOCKS[s] in ["AAPL", "MSFT", "NVDA"]]
fin_stocks_selected  = [s for s in selected_stocks if STOCKS[s] in ["JPM", "GS", "BAC"]]

def avg_pct(stocks, phase):
    if not stocks:
        return None
    return round(sum(phase_stats[s][f"{phase}_pct"] for s in stocks) / len(stocks), 1)

tech_bull    = avg_pct(tech_stocks_selected, "bull")
tech_bear    = avg_pct(tech_stocks_selected, "bear")
tech_neutral = avg_pct(tech_stocks_selected, "neutral")
fin_bull     = avg_pct(fin_stocks_selected, "bull")
fin_bear     = avg_pct(fin_stocks_selected, "bear")
fin_neutral  = avg_pct(fin_stocks_selected, "neutral")

both_sectors = bool(tech_stocks_selected and fin_stocks_selected)

if both_sectors:
    tech_active = (tech_bull or 0) + (tech_bear or 0)
    fin_active  = (fin_bull or 0)  + (fin_bear or 0)
    more_dynamic_sector = "Technology" if tech_active >= fin_active else "Financial"
    more_stable_sector  = "Financial"  if tech_active >= fin_active else "Technology"
    more_bull_sector    = "Technology" if (tech_bull or 0) >= (fin_bull or 0) else "Financial"
    more_bear_sector    = "Technology" if (tech_bear or 0) >= (fin_bear or 0) else "Financial"

most_bull_stock    = max(phase_stats, key=lambda s: phase_stats[s]["bull_pct"])    if phase_stats else None
most_bear_stock    = max(phase_stats, key=lambda s: phase_stats[s]["bear_pct"])    if phase_stats else None
most_neutral_stock = max(phase_stats, key=lambda s: phase_stats[s]["neutral_pct"]) if phase_stats else None
dominant_phase_overall = max(
    ["bull", "bear", "neutral"],
    key=lambda p: sum(phase_stats[s][f"{p}_pct"] for s in phase_stats) / len(phase_stats)
)
dominant_label = {"bull": "Bull", "bear": "Bear", "neutral": "Neutral"}[dominant_phase_overall]

threshold_desc = (
    "strict — only major sustained movements qualify"
    if bull_threshold >= 15 and bear_threshold >= 15
    else "moderate — capturing both significant and minor trends"
    if bull_threshold >= 8
    else "relaxed — even small directional moves are flagged"
)

# --- 01. WHAT DOES THIS ANALYSIS SHOW? ---
st.markdown("""
<div class="section-banner section-banner-blue">
    <p class="section-title">01. What Does This Analysis Show?</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    This page analyzes how stock price movements can be classified into different
    <span class="hl">market phases</span> (bull, bear, and neutral) and how these phases differ
    across technology and financial stocks. Instead of looking only at returns or volatility,
    this approach focuses on <span class="hl">trend behavior over time</span>.
    <br><br>
    By identifying sustained upward or downward movements, we can better understand how different
    types of stocks behave during changing market conditions. The charts show the price development
    of each selected stock, while the tables summarize how often each stock was in a bull, bear,
    or neutral phase.
</div>
""", unsafe_allow_html=True)

# --- 02. METHOD ---
st.markdown("""
<div class="section-banner section-banner-purple">
    <p class="section-title">02. Method</p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="step-card">
    <div class="step-number">01</div>
    <div>
        <p class="step-title">Rolling Window Calculation</p>
        <p class="step-desc">For each stock, we compute a 20-day rolling maximum and minimum price. This establishes the recent high and low reference points for phase detection.</p>
    </div>
</div>
<div class="step-card">
    <div class="step-number">02</div>
    <div>
        <p class="step-title">Phase Classification</p>
        <p class="step-desc">A bull phase is identified when the price rises by at least {bull_threshold}% from its recent 20-day low. A bear phase is identified when the price falls by at least {bear_threshold}% from its recent 20-day high. All other periods are classified as neutral.</p>
    </div>
</div>
<div class="step-card">
    <div class="step-number">03</div>
    <div>
        <p class="step-title">Threshold Adjustment</p>
        <p class="step-desc">The thresholds can be adjusted using the sidebar sliders. Lower thresholds lead to more frequent phase changes, while higher thresholds only capture strong, sustained trends. The current setting is {threshold_desc}.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 03. ANALYSIS AND INTERPRETATION ---
st.markdown("""
<div class="section-banner section-banner-green">
    <p class="section-title">03. Analysis and Interpretation</p>
</div>
""", unsafe_allow_html=True)

analysis_parts = []

analysis_parts.append(
    f"Across all selected stocks, the <span class='hl'>{dominant_label} phase</span> dominates "
    f"the observation period. "
)

if most_bull_stock and most_bear_stock:
    analysis_parts.append(
        f"<span class='hl'>{most_bull_stock}</span> spent the most time in a bull phase "
        f"({phase_stats[most_bull_stock]['bull_pct']}% of trading days), "
        f"while <span class='hl'>{most_bear_stock}</span> recorded the highest share of bear days "
        f"({phase_stats[most_bear_stock]['bear_pct']}%). "
    )

if both_sectors:
    analysis_parts.append(
        f"<br><br>Comparing sectors: <span class='hl'>Tech stocks</span> averaged "
        f"<span class='hl'>{tech_bull}% bull</span> / <span class='hl'>{tech_bear}% bear</span> / "
        f"{tech_neutral}% neutral, while <span class='hl'>Financial stocks</span> averaged "
        f"<span class='hl'>{fin_bull}% bull</span> / <span class='hl'>{fin_bear}% bear</span> / "
        f"{fin_neutral}% neutral. "
        f"This means <span class='hl'>{more_dynamic_sector} stocks</span> were more frequently "
        f"in an active phase (bull or bear), while <span class='hl'>{more_stable_sector} stocks</span> "
        f"spent more time in neutral territory. "
    )
elif tech_stocks_selected:
    analysis_parts.append(
        f"<br><br>The selected tech stocks averaged {tech_bull}% bull / {tech_bear}% bear / "
        f"{tech_neutral}% neutral phases. "
    )
elif fin_stocks_selected:
    analysis_parts.append(
        f"<br><br>The selected financial stocks averaged {fin_bull}% bull / {fin_bear}% bear / "
        f"{fin_neutral}% neutral phases. "
    )

analysis_parts.append(
    f"<br><br>The current thresholds (Bull: +{bull_threshold}%, Bear: -{bear_threshold}%) are "
    f"{threshold_desc}. Adjusting these values in the sidebar will directly change the phase "
    f"distributions shown in the tables above."
)

st.markdown(f"""
<div class="info-box">
    {"".join(analysis_parts)}
</div>
""", unsafe_allow_html=True)

# --- 04. KEY INSIGHTS ---
st.markdown("""
<div class="section-banner section-banner-orange">
    <p class="section-title">04. Key Insights</p>
</div>
""", unsafe_allow_html=True)

col_i1, col_i2 = st.columns(2)

with col_i1:
    st.markdown(f"""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-blue">📊</div>
            <p class="card-title">Dominance of {dominant_label} Phases</p>
        </div>
        <p class="card-body">
            Across all selected stocks, <strong>{dominant_label}</strong> is the most common phase.
            With thresholds of +{bull_threshold}% / -{bear_threshold}% ({threshold_desc}),
            most trading days do not meet the criteria for a strong directional trend.
            {"Lowering the thresholds would reveal more phase transitions." if bull_threshold >= 15 else "The current thresholds already capture moderate directional moves."}
        </p>
    </div>
    """, unsafe_allow_html=True)

    if both_sectors:
        st.markdown(f"""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-orange">⚡</div>
                <p class="card-title">Higher Reactivity: {more_dynamic_sector} Stocks</p>
            </div>
            <p class="card-body">
                {more_dynamic_sector} stocks spent more time in active (bull or bear) phases
                ({tech_active if more_dynamic_sector == "Technology" else fin_active:.1f}% combined)
                compared to {more_stable_sector} stocks
                ({fin_active if more_dynamic_sector == "Technology" else tech_active:.1f}% combined).
                This suggests they react more strongly to market events and sentiment shifts
                under the current threshold settings.
            </p>
        </div>
        """, unsafe_allow_html=True)
    elif most_bull_stock:
        st.markdown(f"""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-orange">⚡</div>
                <p class="card-title">Most Active Stock: {most_bull_stock}</p>
            </div>
            <p class="card-body">
                {most_bull_stock} recorded the highest bull phase share
                ({phase_stats[most_bull_stock]['bull_pct']}% of days), indicating
                the strongest upward trend among the selected assets.
            </p>
        </div>
        """, unsafe_allow_html=True)

with col_i2:
    if both_sectors:
        stable_neutral = fin_neutral if more_stable_sector == "Financial" else tech_neutral
        st.markdown(f"""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-green">🛡️</div>
                <p class="card-title">More Stable: {more_stable_sector} Stocks</p>
            </div>
            <p class="card-body">
                {more_stable_sector} stocks spent more time in neutral phases
                ({stable_neutral}% on average), suggesting more gradual price development
                anchored to slower-moving fundamentals.
            </p>
        </div>
        """, unsafe_allow_html=True)
    elif most_neutral_stock:
        st.markdown(f"""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-green">🛡️</div>
                <p class="card-title">Most Stable Stock: {most_neutral_stock}</p>
            </div>
            <p class="card-body">
                {most_neutral_stock} spent {phase_stats[most_neutral_stock]['neutral_pct']}% of
                trading days in a neutral phase, showing the most stable and gradual
                price development among the selected assets.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="insight-card">
        <div class="card-icon-row">
            <div class="card-icon icon-purple">🎚️</div>
            <p class="card-title">Threshold Sensitivity</p>
        </div>
        <p class="card-body">
            At the current setting (+{bull_threshold}% / -{bear_threshold}%), phase classification
            is {threshold_desc}. Adjusting the sliders will directly change the phase distribution
            shown in the tables above — try lower values to see more transitions, or higher values
            to isolate only the strongest market moves.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- DYNAMIC CONCLUSION ---
if both_sectors:
    conclusion = (
        f"Based on the current settings (Bull: +{bull_threshold}%, Bear: -{bear_threshold}%), "
        f"{more_dynamic_sector} stocks showed more frequent active phases "
        f"({tech_active if more_dynamic_sector == 'Technology' else fin_active:.1f}% combined bull/bear) "
        f"compared to {more_stable_sector} stocks "
        f"({fin_active if more_dynamic_sector == 'Technology' else tech_active:.1f}%). "
        f"{more_bull_sector} stocks led in bull phase frequency, while {more_bear_sector} stocks "
        f"recorded more bear phase days. "
        f"This confirms that sector membership influences how stocks move through market phases — "
        f"{'technology stocks react more dynamically to sentiment and news, while financial stocks follow slower macroeconomic cycles.' if more_dynamic_sector == 'Technology' else 'financial stocks showed stronger directional moves under these conditions, possibly driven by interest rate sensitivity or sector-specific events.'}"
    )
else:
    most_active = max(phase_stats, key=lambda s: phase_stats[s]["bull_pct"] + phase_stats[s]["bear_pct"])
    most_active_pct = phase_stats[most_active]["bull_pct"] + phase_stats[most_active]["bear_pct"]
    conclusion = (
        f"Among the selected stocks, {most_active} was most frequently in an active phase "
        f"({phase_stats[most_active]['bull_pct']}% bull, {phase_stats[most_active]['bear_pct']}% bear, "
        f"{most_active_pct:.1f}% combined). "
        f"With thresholds of +{bull_threshold}% / -{bear_threshold}%, most stocks spent the majority "
        f"of the observation period in {dominant_label.lower()} territory, suggesting that "
        f"{'strong directional trends are relatively rare under these strict conditions.' if bull_threshold >= 15 else 'moderate directional moves are captured under the current settings.'}"
    )

st.markdown(
    f"""
    <section class="research-header">
        <p class="research-header__eyebrow">Answer to the Research Question</p>
        <p class="research-header__question">{conclusion}</p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.caption(f"Methodology: Rolling 20-day window analysis. Bull: +{bull_threshold}% from 20d low. Bear: -{bear_threshold}% from 20d high.")