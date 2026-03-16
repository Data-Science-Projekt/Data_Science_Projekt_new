import streamlit as st
from pathlib import Path

st.title("Our Team")
st.markdown("The people behind the project")

st.divider()

img_dir = Path(__file__).parent.parent / "static" / "img"

team = [
    {"name": "Tom Steinke", "role": "Project Lead", "img": "IMG_1174.JPG",
     "quote": "Data doesn't lie — but you have to ask the right questions."},
    {"name": "Jakob Puchert", "role": "Data Engineering", "img": "IMG_2725.jpg",
     "quote": "Clean data is half the analysis."},
    {"name": "Ole Schweckendiek", "role": "Machine Learning", "img": "IMG_8812.jpg",
     "quote": "A model is only as good as its feature engineering."},
    {"name": "Balduin Makko", "role": "Visualization & Frontend", "img": "IMG_8813.jpg",
     "quote": "A good visualization says more than a thousand tables."},
]

cols = st.columns(4)
for col, member in zip(cols, team):
    with col:
        img_path = img_dir / member["img"]
        if img_path.exists():
            st.image(str(img_path), use_container_width=True)
        st.markdown(f"**{member['name']}**")
        st.caption(member["role"])
        st.markdown(f"*\"{member['quote']}\"*")
