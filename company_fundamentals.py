import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import pearsonr
from scipy import stats as scipy_stats
import os
from analysis.utils import render_page_header
from utils.export import fig_to_pdf_bytes, figs_to_pdf_bytes


# --- MAIN PAGE ---
render_page_header(
    "Company Fundamentals",
    "How does the quarterly sales volume of iPhone units statistically correlate with Apple's stock price returns in the month following the earnings release?",
)



# --- Load iPhone Sales Data (includes pre-collected price data) ---
@st.cache_data
def load_earnings_dataset():
    csv_path = os.path.join(os.path.dirname(__file__), "data", "iphone_sales.csv")
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    df = pd.read_csv(csv_path)
    df["earnings_date"] = pd.to_datetime(df["earnings_date"])
    df["return_30d"] = (df["price_30d_after"] - df["price_on_earnings"]) / df["price_on_earnings"]
    df["return_30d_pct"] = (df["return_30d"] * 100).round(2)
    df["iphone_sales_growth"] = df["iphone_units_million"].pct_change()
    return df


# --- Main RQ7 Section ---
merged = load_earnings_dataset()

if merged.empty:
    st.error("The file data/iphone_sales.csv was not found or is empty. Please maintain data manually.")
    st.stop()

st.write(f"**Analysis Period:** {merged['quarter'].iloc[0]} to {merged['quarter'].iloc[-1]} ({len(merged)} quarters)")

if len(merged) >= 3:
    # --- Statistical Analysis ---
    x = merged["iphone_units_million"].values
    y = merged["return_30d"].values

    corr, p_corr = pearsonr(x, y)
    slope, intercept, r_value, p_reg, std_err = scipy_stats.linregress(x, y)
    r_squared = r_value ** 2

    # --- 1. Scatter Plot with Regression Line ---
    st.subheader("1. Scatter Plot: iPhone Sales vs 30-Day Post-Earnings Return")

    fig_scatter = go.Figure()

    fig_scatter.add_trace(go.Scatter(
        x=x, y=y * 100,
        mode="markers+text",
        text=merged["quarter"],
        textposition="top center",
        textfont=dict(size=9),
        marker=dict(size=10, color="#e94560", line=dict(width=1, color="white")),
        name="Quarters",
    ))

    # Regression line
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = (slope * x_line + intercept) * 100
    fig_scatter.add_trace(go.Scatter(
        x=x_line, y=y_line,
        mode="lines",
        name=f"Regression (R²={r_squared:.3f})",
        line=dict(color="#1f77b4", dash="dash", width=2),
    ))

    fig_scatter.update_layout(
        xaxis_title="iPhone Units Sold (millions)",
        yaxis_title="30-Day Post-Earnings Return (%)",
        template="plotly_white",
        height=500,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.download_button(
        label="📥 Graph als PNG herunterladen",
        data=fig_to_pdf_bytes(fig_scatter),
        file_name="fundamentals_scatter.png",
        mime="image/png",
        key="download_fundamentals_scatter"
    )

    # --- 2. Time Series Chart ---
    st.subheader("2. Time Series: iPhone Sales & Post-Earnings Returns by Quarter")

    fig_ts = make_subplots(specs=[[{"secondary_y": True}]])

    fig_ts.add_trace(
        go.Bar(
            x=merged["quarter"], y=merged["iphone_units_million"],
            name="iPhone Units (M)", marker_color="#1f77b4", opacity=0.7,
        ),
        secondary_y=False,
    )

    fig_ts.add_trace(
        go.Scatter(
            x=merged["quarter"], y=merged["return_30d_pct"],
            name="30-Day Return (%)", mode="lines+markers",
            line=dict(color="#e94560", width=2),
            marker=dict(size=7),
        ),
        secondary_y=True,
    )

    fig_ts.update_layout(
        template="plotly_white", height=500,
        legend=dict(yanchor="top", y=1.15, xanchor="center", x=0.5, orientation="h"),
    )
    fig_ts.update_yaxes(title_text="iPhone Units Sold (millions)", secondary_y=False)
    fig_ts.update_yaxes(title_text="30-Day Post-Earnings Return (%)", secondary_y=True)

    st.plotly_chart(fig_ts, use_container_width=True)

    st.download_button(
        label="📥 Graph als PNG herunterladen",
        data=fig_to_pdf_bytes(fig_ts),
        file_name="fundamentals_timeseries.png",
        mime="image/png",
        key="download_fundamentals_timeseries"
    )

    # --- 3. Statistical Results ---
    st.subheader("3. Statistical Results")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pearson r", f"{corr:.4f}")
    col2.metric("R²", f"{r_squared:.4f}")
    col3.metric("p-value", f"{p_corr:.4f}")
    col4.metric("Slope (β₁)", f"{slope:.6f}")

    st.markdown("**Linear Regression Model:**")
    st.latex(
        rf"\text{{Return}}_{{30d}} = {intercept:.4f} + {slope:.6f} "
        rf"\times \text{{iPhone\_Sales}} \quad (p = {p_reg:.4f})"
    )

    # --- Data Table ---
    with st.expander("View Full Dataset"):
        display_cols = [
            "quarter", "earnings_date", "iphone_units_million",
            "iphone_revenue_billion", "price_on_earnings",
            "price_30d_after", "return_30d_pct",
        ]
        st.dataframe(
            merged[display_cols].rename(columns={
                "quarter": "Quarter",
                "earnings_date": "Earnings Date",
                "iphone_units_million": "iPhone Units (M)",
                "iphone_revenue_billion": "iPhone Revenue ($B)",
                "price_on_earnings": "Price at Earnings ($)",
                "price_30d_after": "Price 30d After ($)",
                "return_30d_pct": "30-Day Return (%)",
            }),
            use_container_width=True,
            hide_index=True,
        )

    # --- STYLED ANALYSIS SECTIONS ---
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
    .process-flow { display: flex; gap: 0; margin-bottom: 24px; position: relative; }
    .process-step {
        flex: 1; text-align: center; padding: 24px 16px 20px; position: relative;
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
        font-family: 'Syne', sans-serif; font-weight: 800; color: white;
    }
    .circle-1 { background: linear-gradient(135deg, #2563eb, #3b82f6); }
    .circle-2 { background: linear-gradient(135deg, #7c3aed, #8b5cf6); }
    .circle-3 { background: linear-gradient(135deg, #d97706, #f59e0b); }
    .circle-4 { background: linear-gradient(135deg, #16a34a, #22c55e); }
    .process-title { font-family: 'Syne', sans-serif; font-size: 0.95rem; font-weight: 700; margin: 0 0 6px 0; }
    .process-desc { font-size: 0.88rem; line-height: 1.5; margin: 0; opacity: 0.65; }
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
        This page investigates whether <span class="hl">iPhone sales figures</span> — Apple's most
        important product line — have a measurable impact on <span class="hl">Apple's stock price</span>
        in the month following each quarterly earnings announcement.
        <br><br>
        Every quarter, Apple reports its financial results, including iPhone revenue and estimated unit
        sales. Investors closely watch these numbers. The question is: <em>Do higher iPhone sales
        actually lead to higher stock returns, or does the market already price in expectations?</em>
        <br><br>
        We analyze <span class="hl">{len(merged)} quarters</span> from {merged['quarter'].iloc[0]} to
        {merged['quarter'].iloc[-1]}, comparing iPhone units sold against the stock's 30-day
        post-earnings return.
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
            <p class="process-title">Sales Data</p>
            <p class="process-desc">Quarterly iPhone unit sales and revenue from earnings reports and third-party estimates.</p>
            <span class="process-arrow">→</span>
        </div>
        <div class="process-step">
            <div class="process-circle circle-2">02</div>
            <p class="process-title">Price Capture</p>
            <p class="process-desc">Apple's closing price on earnings day and exactly 30 calendar days later.</p>
            <span class="process-arrow">→</span>
        </div>
        <div class="process-step">
            <div class="process-circle circle-3">03</div>
            <p class="process-title">Return Calculation</p>
            <p class="process-desc">30-day post-earnings return = (Price after − Price at earnings) / Price at earnings.</p>
            <span class="process-arrow">→</span>
        </div>
        <div class="process-step">
            <div class="process-circle circle-4">04</div>
            <p class="process-title">Regression</p>
            <p class="process-desc">Pearson correlation and OLS linear regression quantify the relationship.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- ANALYSIS AND INTERPRETATION ---
    st.markdown("""
    <div class="section-banner section-banner-green">
        <span class="section-icon">📊</span>
        <p class="section-title">Analysis and Interpretation</p>
    </div>
    """, unsafe_allow_html=True)

    sig_level = 0.05
    is_significant = p_corr < sig_level
    direction = "positive" if corr > 0 else "negative"

    if is_significant:
        sig_html = (
            f'The Pearson correlation of <span class="hl">r = {corr:.4f}</span> is '
            f'<span class="hl">statistically significant</span> (p = {p_corr:.4f} &lt; 0.05), '
            f'indicating a {direction} linear relationship between iPhone unit sales and '
            f'Apple\'s 30-day post-earnings return. The regression model explains '
            f'<span class="hl">{r_squared*100:.1f}%</span> of the variance in post-earnings returns.'
        )
    else:
        sig_html = (
            f'The Pearson correlation of <span class="hl">r = {corr:.4f}</span> is '
            f'<span class="hl">not statistically significant</span> (p = {p_corr:.4f} &gt; 0.05). '
            f'The regression model explains only <span class="hl">{r_squared*100:.1f}%</span> of the '
            f'variance, suggesting that iPhone unit sales alone are not a reliable predictor of '
            f'post-earnings returns.'
        )

    analysis_html = (
        f'<div class="info-box">'
        f'Over <span class="hl">{len(merged)} quarters</span>, the results show:'
        f'<br><br>'
        f'{sig_html}'
        f'<br><br>'
        f'<strong>Regression model:</strong> For every additional million iPhones sold, the model '
        f'predicts a change of <span class="hl">{slope*100:.4f} percentage points</span> in the '
        f'30-day post-earnings return. However, the wide scatter in the data and the '
        f'{"significant" if is_significant else "high"} p-value '
        f'{"confirm" if is_significant else "suggest"} that this relationship is '
        f'{"real but modest" if is_significant else "too weak to be distinguished from random noise"}.'
        f'<br><br>'
        f'<strong>What this means in practice:</strong> Even with {len(merged)} quarters of data, '
        f'knowing how many iPhones Apple sold does {"help" if is_significant else "not help"} predict '
        f'what the stock will do in the following month. The market\'s reaction to earnings is driven '
        f'by many factors beyond unit sales — including guidance, margins, services growth, and '
        f'macroeconomic conditions.'
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
        st.markdown("""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-blue">📱</div>
                <p class="card-title">Expectations vs. Reality</p>
            </div>
            <p class="card-body">
                Markets don't react to absolute sales numbers — they react to surprises.
                If analysts expect 70 million iPhones and Apple delivers 71 million, the stock
                may barely move. But delivering 65 million could trigger a sell-off, even though
                65 million is still a massive number.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-orange">📊</div>
                <p class="card-title">Earnings Are Multi-Dimensional</p>
            </div>
            <p class="card-body">
                Apple's stock reacts to guidance, services revenue, margins, buyback announcements,
                and macroeconomic outlook — not just iPhone units. Isolating one variable
                inevitably misses the full picture of what drives post-earnings returns.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col_i2:
        st.markdown("""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-purple">🔄</div>
                <p class="card-title">Product Cycle Seasonality</p>
            </div>
            <p class="card-body">
                Launch quarters (Q4/Q1) naturally show higher sales due to the iPhone release cycle
                and holiday shopping. The market anticipates this seasonality, which dampens the
                return signal — high sales in Q1 are expected, not surprising.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="insight-card">
            <div class="card-icon-row">
                <div class="card-icon icon-red">⚠️</div>
                <p class="card-title">Data Source Caveat</p>
            </div>
            <p class="card-body">
                Apple officially stopped reporting iPhone unit sales after Q4 2018. The unit figures
                in this analysis ({merged['quarter'].iloc[0]}–{merged['quarter'].iloc[-1]}) are
                third-party estimates (Statista, IDC, analyst consensus) — not official Apple data.
                This introduces measurement uncertainty into the analysis.
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
        This analysis tests a common investor assumption: <span class="hl">"If the product sells well,
        the stock should go up."</span> The results show that this intuition is far too simplistic
        for modern financial markets.
        <br><br>
        The <span class="hl">Efficient Market Hypothesis</span> suggests that stock prices already
        reflect all publicly available information — including analyst forecasts for iPhone sales.
        By the time Apple reports actual numbers, the market has largely priced in expectations.
        Only the <em>deviation</em> from expectations (the "earnings surprise") drives the reaction.
        <br><br>
        For <span class="hl">investors</span>, this underscores the importance of looking beyond
        headline numbers. Understanding consensus expectations, guidance changes, and margin trends
        is more valuable than simply tracking unit sales.
        <br><br>
        In the broader context of this project, this page complements the
        <span class="hl">Return Analysis</span> (which examines how returns are distributed) and
        <span class="hl">Risk Management</span> (which quantifies downside risk). Together, they
        show that stock behavior is driven by a complex interplay of fundamental, technical, and
        sentiment factors — not any single metric.
    </div>
    """, unsafe_allow_html=True)

    # --- ANSWER TO THE RESEARCH QUESTION ---
    st.markdown(
        f"""
        <section class="research-header">
            <p class="research-header__eyebrow">Answer to the Research Question</p>
            <p class="research-header__question">
                Over {len(merged)} quarters of data, {"a statistically significant " + direction + " correlation was found" if is_significant else "no statistically significant correlation was found"} between quarterly iPhone unit sales and Apple's 30-day post-earnings stock returns (r = {corr:.4f}, p = {p_corr:.4f}). The regression model explains only {r_squared*100:.1f}% of the variance in returns, indicating that iPhone sales volume alone is not a meaningful predictor of short-term stock performance. This is consistent with the Efficient Market Hypothesis — markets price in expected sales before earnings, so only surprises relative to consensus drive the post-announcement return.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

else:
    st.warning("Not enough data points to perform a meaningful analysis.")

st.caption("Data source: Apple Investor Relations / Statista (unit estimates). Manual updates required in data/iphone_sales.csv.")
