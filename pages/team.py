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
        border: 1px solid rgba(37, 99, 235, 0.2);
        background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(37,99,235,0.02) 60%, rgba(124,58,237,0.05) 100%);
    }

    .team-hero::before {
        content: "";
        position: absolute;
        top: -50px; right: -50px;
        width: 260px; height: 260px;
        background: radial-gradient(circle, rgba(37,99,235,0.1) 0%, transparent 70%);
        pointer-events: none;
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
        color: #2563eb;
        background: rgba(37, 99, 235, 0.1);
        border: 1px solid rgba(37, 99, 235, 0.3);
    }

    .team-hero__title {
        margin: 0 0 0.5rem;
        font-family: 'Syne', sans-serif;
        font-size: 2.4rem;
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .team-hero__subtitle {
        max-width: 760px;
        margin: 0;
        font-size: 1.1rem;
        line-height: 1.6;
        font-weight: 300;
        opacity: 0.7;
    }

    .team-grid-note {
        margin: 0 0 1.25rem;
        padding: 0.9rem 1rem;
        border-radius: 14px;
        background: rgba(37,99,235,0.04);
        border: 1px solid rgba(37, 99, 235, 0.15);
        color: inherit;
    }

    .team-grid-note strong {
        font-family: 'Syne', sans-serif;
        font-weight: 700;
    }

    .team-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        margin-top: 8px;
    }

    @media (max-width: 900px) {
        .team-grid { grid-template-columns: repeat(2, 1fr); }
    }

    .team-card {
        overflow: hidden;
        border-radius: 20px;
        border: 1px solid rgba(0, 0, 0, 0.1);
        background: rgba(0, 0, 0, 0.02);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
        transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
        display: flex;
        flex-direction: column;
    }

    .team-card:hover {
        transform: translateY(-6px);
        border-color: #2563eb;
        box-shadow: 0 16px 36px rgba(37, 99, 235, 0.12);
    }

    .team-card__media {
        position: relative;
        overflow: hidden;
        height: 320px;
        flex-shrink: 0;
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(124, 58, 237, 0.08));
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
        background: linear-gradient(180deg, transparent 50%, rgba(0, 0, 0, 0.15));
        pointer-events: none;
    }

    .team-card__content {
        padding: 1.15rem 1.15rem 1.2rem;
        flex: 1;
        display: flex;
        flex-direction: column;
    }

    .team-card__badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        margin-bottom: 0.8rem;
        padding: 0.42rem 0.78rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        color: white;
        background: linear-gradient(90deg, #2563eb, #0ea5e9);
        width: fit-content;
    }

    .team-card__name {
        margin: 0 0 0.55rem;
        font-family: 'Syne', sans-serif;
        font-size: 1.2rem;
        line-height: 1.2;
        color: #1e293b;
    }

    .team-card__focus {
        margin: 0 0 0.7rem;
        font-size: 0.88rem;
        line-height: 1.65;
        color: #475569;
    }

    .team-card__focus strong {
        color: #2563eb;
        font-weight: 700;
    }

    .team-card__quote {
        margin: 0;
        margin-top: auto;
        padding-top: 0.8rem;
        border-top: 1px solid rgba(0, 0, 0, 0.08);
        font-size: 0.82rem;
        line-height: 1.7;
        font-style: italic;
        color: #64748b;
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


IMG_DIR = Path(__file__).parent.parent / "static" / "img"

team = [
    {"name": "Tom Steinke", "role": "Project Coordination", "focus": "Project organization, research alignment, and analytical framing.", "img": "IMG_1174.JPG", "quote": "Data doesn't lie — but you have to ask the right questions.", "icon": "◆"},
    {"name": "Jakob Puchert", "role": "Data Engineering & Processing", "focus": "Data collection, preprocessing, and reliable analytical data structures.", "img": "IMG_2725.jpg", "quote": "Clean data is half the analysis.", "icon": "●"},
    {"name": "Ole Schweckendiek", "role": "Machine Learning & Modeling", "focus": "Model development, feature engineering, and statistical analysis.", "img": "IMG_8812.jpg", "quote": "A model is only as good as its feature engineering.", "icon": "▲"},
    {"name": "Balduin Makko", "role": "Data Visualization & Frontend", "focus": "Visual communication, interface design, and presentation of analytical results.", "img": "IMG_8813.jpg", "quote": "A good visualization says more than a thousand tables.", "icon": "■"},
]

cards_html = '<div class="team-grid">'
for member in team:
    image_path = IMG_DIR / member["img"]
    image_src = image_to_data_uri(image_path)
    name_esc = html.escape(member["name"])
    role_esc = html.escape(member["role"])
    focus_esc = html.escape(member["focus"])
    quote_esc = html.escape(member["quote"])
    icon_esc = html.escape(member["icon"])

    if image_src:
        image_markup = f'<img src="{image_src}" alt="{name_esc}" class="team-card__image">'
    else:
        image_markup = '<div class="team-card__image team-card__image--placeholder"></div>'

    cards_html += f"""
    <article class="team-card">
        <div class="team-card__media">
            {image_markup}
            <div class="team-card__overlay"></div>
        </div>
        <div class="team-card__content">
            <span class="team-card__badge">{icon_esc} {role_esc}</span>
            <h3 class="team-card__name">{name_esc}</h3>
            <p class="team-card__focus"><strong>Focus:</strong> {focus_esc}</p>
            <p class="team-card__quote">&ldquo;{quote_esc}&rdquo;</p>
        </div>
    </article>
    """

cards_html += '</div>'
st.markdown(cards_html, unsafe_allow_html=True)
