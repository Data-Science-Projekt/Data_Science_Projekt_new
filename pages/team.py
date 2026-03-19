import base64
import html
import mimetypes
from pathlib import Path

import streamlit as st


def image_to_data_uri(image_path: Path) -> str | None:
    if not image_path.exists():
        return None

    mime_type, _ = mimetypes.guess_type(image_path.name)
    mime_type = mime_type or "image/jpeg"
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def render_team_member(name: str, role: str, focus: str, image_name: str, quote: str, icon: str) -> None:
    image_path = IMG_DIR / image_name
    image_src = image_to_data_uri(image_path)
    image_markup = (
        f'<img src="{image_src}" alt="{html.escape(name)}" class="team-card__image">'
        if image_src
        else '<div class="team-card__image team-card__image--placeholder"></div>'
    )

    st.markdown(
        f"""
        <article class="team-card">
            <div class="team-card__media">
                {image_markup}
                <div class="team-card__overlay"></div>
            </div>
            <div class="team-card__content">
                <span class="team-card__badge">{html.escape(icon)} {html.escape(role)}</span>
                <h3 class="team-card__name">{html.escape(name)}</h3>
                <p class="team-card__focus"><strong>Focus:</strong> {html.escape(focus)}</p>
                <p class="team-card__quote">&ldquo;{html.escape(quote)}&rdquo;</p>
            </div>
        </article>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .team-hero {
        position: relative;
        overflow: hidden;
        margin-bottom: 1.75rem;
        padding: 2.4rem 2.6rem;
        border-radius: 22px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        background:
            radial-gradient(circle at top right, rgba(37, 99, 235, 0.18), transparent 32%),
            radial-gradient(circle at bottom left, rgba(16, 185, 129, 0.12), transparent 28%),
            linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.78));
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
    }

    .team-hero__eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        margin-bottom: 0.95rem;
        padding: 0.42rem 0.8rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #dbeafe;
        background: rgba(37, 99, 235, 0.18);
        border: 1px solid rgba(96, 165, 250, 0.22);
    }

    .team-hero__title {
        margin: 0 0 0.5rem;
        font-family: 'Syne', sans-serif;
        font-size: 3rem;
        line-height: 1.05;
        letter-spacing: -0.04em;
        color: #f8fafc;
    }

    .team-hero__subtitle {
        max-width: 760px;
        margin: 0;
        font-size: 1.05rem;
        line-height: 1.75;
        color: rgba(226, 232, 240, 0.88);
    }

    .team-grid-note {
        margin: 0 0 1.25rem;
        padding: 0.9rem 1rem;
        border-radius: 14px;
        background: linear-gradient(90deg, rgba(37, 99, 235, 0.08), rgba(14, 165, 233, 0.02));
        border: 1px solid rgba(37, 99, 235, 0.14);
        color: inherit;
    }

    .team-grid-note strong {
        font-family: 'Syne', sans-serif;
        font-weight: 700;
    }

    .team-card {
        overflow: hidden;
        height: 100%;
        border-radius: 20px;
        border: 1px solid rgba(148, 163, 184, 0.16);
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.04));
        box-shadow: 0 16px 34px rgba(15, 23, 42, 0.1);
        backdrop-filter: blur(10px);
        transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
    }

    .team-card:hover {
        transform: translateY(-6px);
        border-color: rgba(59, 130, 246, 0.35);
        box-shadow: 0 22px 42px rgba(15, 23, 42, 0.16);
    }

    .team-card__media {
        position: relative;
        overflow: hidden;
        aspect-ratio: 4 / 4.8;
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(15, 23, 42, 0.12));
    }

    .team-card__image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
        transform: scale(1.01);
        transition: transform 0.35s ease;
    }

    .team-card:hover .team-card__image {
        transform: scale(1.08);
    }

    .team-card__image--placeholder {
        width: 100%;
        height: 100%;
    }

    .team-card__overlay {
        position: absolute;
        inset: 0;
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.04), rgba(15, 23, 42, 0.44));
        pointer-events: none;
    }

    .team-card__content {
        padding: 1.15rem 1.15rem 1.2rem;
    }

    .team-card__badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        margin-bottom: 0.8rem;
        padding: 0.42rem 0.78rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        color: #dbeafe;
        background: linear-gradient(90deg, rgba(37, 99, 235, 0.82), rgba(14, 165, 233, 0.78));
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
    }

    .team-card__name {
        margin: 0 0 0.55rem;
        font-family: 'Syne', sans-serif;
        font-size: 1.35rem;
        line-height: 1.2;
        color: inherit;
    }

    .team-card__focus {
        margin: 0 0 0.7rem;
        font-size: 0.92rem;
        line-height: 1.65;
        color: rgba(226, 232, 240, 0.84);
    }

    .team-card__focus strong {
        color: #bfdbfe;
        font-weight: 700;
    }

    .team-card__quote {
        margin: 0;
        padding-top: 0.8rem;
        border-top: 1px solid rgba(148, 163, 184, 0.18);
        font-size: 0.84rem;
        line-height: 1.7;
        font-style: italic;
        color: rgba(226, 232, 240, 0.62);
        opacity: 1;
    }

    @media (max-width: 900px) {
        .team-hero {
            padding: 2rem 1.5rem;
        }

        .team-hero__title {
            font-size: 2.3rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="team-hero">
        <div class="team-hero__eyebrow">University Data Science Project</div>
        <h1 class="team-hero__title">Our Team</h1>
        <p class="team-hero__subtitle">
            This page presents the team contributing to a university data science project focused on
            financial data analysis, statistical methods, machine learning, and visualization.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="team-grid-note">
        <strong>Core Team</strong><br>
        Four team members contributing to data acquisition, processing, statistical analysis, modeling, and visual communication.
    </div>
    """,
    unsafe_allow_html=True,
)

IMG_DIR = Path(__file__).parent.parent / "static" / "img"

team = [
    {"name": "Tom Steinke", "role": "Project Coordination", "focus": "Project organization, research alignment, and analytical framing.", "img": "IMG_1174.JPG", "quote": "Data doesn't lie — but you have to ask the right questions.", "icon": "◆"},
    {"name": "Jakob Puchert", "role": "Data Engineering & Processing", "focus": "Data collection, preprocessing, and reliable analytical data structures.", "img": "IMG_2725.jpg", "quote": "Clean data is half the analysis.", "icon": "●"},
    {"name": "Ole Schweckendiek", "role": "Machine Learning & Modeling", "focus": "Model development, feature engineering, and statistical analysis.", "img": "IMG_8812.jpg", "quote": "A model is only as good as its feature engineering.", "icon": "▲"},
    {"name": "Balduin Makko", "role": "Data Visualization & Frontend", "focus": "Visual communication, interface design, and presentation of analytical results.", "img": "IMG_8813.jpg", "quote": "A good visualization says more than a thousand tables.", "icon": "■"},
]

columns = st.columns(len(team), gap="medium")
for index, column in enumerate(columns):
    member = team[index]
    with column:
        render_team_member(
            name=member["name"],
            role=member["role"],
            focus=member["focus"],
            image_name=member["img"],
            quote=member["quote"],
            icon=member["icon"],
        )
