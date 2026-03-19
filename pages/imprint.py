import streamlit as st

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root { --accent-blue: #2563eb; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.page-hero {
    background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(37,99,235,0.02) 60%, rgba(124,58,237,0.05) 100%);
    border: 1px solid rgba(37,99,235,0.2); border-radius: 16px;
    padding: 40px 56px; margin-bottom: 32px;
    position: relative; overflow: hidden;
}
.page-hero::before {
    content: ""; position: absolute; top: -50px; right: -50px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(37,99,235,0.1) 0%, transparent 70%);
    pointer-events: none;
}
.page-badge {
    display: inline-block; background: rgba(37,99,235,0.1);
    border: 1px solid rgba(37,99,235,0.3); color: #2563eb;
    font-size: 0.82rem; font-weight: 500; letter-spacing: 1.5px;
    text-transform: uppercase; padding: 4px 12px;
    border-radius: 20px; margin-bottom: 12px;
}
.page-title {
    font-family: 'Syne', sans-serif; font-size: 2.4rem; font-weight: 800;
    letter-spacing: -0.5px; margin: 0 0 6px 0;
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1.15;
}
.page-subtitle {
    font-size: 1.2rem; font-weight: 300; margin: 0;
    max-width: 580px; line-height: 1.6; opacity: 0.7;
}

.section-banner {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 22px; border-radius: 10px;
    margin-bottom: 20px; margin-top: 10px;
}
.section-banner-blue { background: linear-gradient(90deg, rgba(37,99,235,0.08), rgba(37,99,235,0.01)); border-left: 3px solid #2563eb; }
.section-banner-purple { background: linear-gradient(90deg, rgba(124,58,237,0.08), rgba(124,58,237,0.01)); border-left: 3px solid #7c3aed; }
.section-banner-green { background: linear-gradient(90deg, rgba(22,163,74,0.08), rgba(22,163,74,0.01)); border-left: 3px solid #16a34a; }
.section-icon { font-size: 1.5rem; line-height: 1; }
.section-title { font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700; margin: 0; }

.info-box {
    background: rgba(37,99,235,0.04); border: 1px solid rgba(37,99,235,0.15);
    border-radius: 12px; padding: 24px 28px; margin-bottom: 16px;
    line-height: 1.75; font-size: 1.08rem;
}
.info-box .hl { color: #2563eb; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── Page Hero ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-hero">
    <div class="page-badge">Legal</div>
    <h1 class="page-title">Imprint</h1>
    <p class="page-subtitle">
        Legal information as required by German law (§ 5 TMG).
    </p>
</div>
""", unsafe_allow_html=True)


# ── Responsible Institution ──────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-blue">
    <span class="section-icon">🏛️</span>
    <p class="section-title">Responsible Institution</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    <span class="hl">Christian-Albrechts-Universität zu Kiel (CAU)</span>
    <br>Christian-Albrechts-Platz 4
    <br>24118 Kiel
    <br>Germany
    <br><br>
    <strong>Phone:</strong> +49 (0)431 880-00
    <br><strong>Email:</strong> mail@uni-kiel.de
    <br><strong>Website:</strong> www.uni-kiel.de
    <br><br>
    The Christian-Albrechts-Universität zu Kiel is a public corporation
    (<em>Körperschaft des öffentlichen Rechts</em>). It is legally represented
    by the Presidium.
</div>
""", unsafe_allow_html=True)


# ── Project Context ──────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-purple">
    <span class="section-icon">📚</span>
    <p class="section-title">Project Context</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    This web application was developed as part of a <span class="hl">Data Science course project</span>
    at the Christian-Albrechts-Universität zu Kiel. It is an academic exercise and does not constitute
    financial advice, investment recommendations, or any form of professional financial analysis.
    <br><br>
    All data used in this project is sourced from publicly available APIs
    (<span class="hl">Alpha Vantage</span>, <span class="hl">FRED</span>) and public financial reports.
    No proprietary or confidential data is used.
</div>
""", unsafe_allow_html=True)


# ── Disclaimer ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-banner section-banner-blue">
    <span class="section-icon">📝</span>
    <p class="section-title">Disclaimer</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    <strong>No financial advice:</strong> The analyses, visualizations, and interpretations presented
    on this website are for <span class="hl">educational and academic purposes only</span>. They do not
    constitute financial advice or investment recommendations. Past performance does not guarantee
    future results.
    <br><br>
    <strong>Data accuracy:</strong> While we strive for accuracy, we cannot guarantee the completeness
    or correctness of all data. Stock prices are sourced from Alpha Vantage, macroeconomic data from
    FRED, and iPhone unit sales are third-party estimates (not official Apple data).
    <br><br>
    <strong>Liability:</strong> The authors assume no liability for decisions made based on the
    information presented in this application.
</div>
""", unsafe_allow_html=True)
