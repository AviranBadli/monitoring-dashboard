import streamlit as st

st.set_page_config(
    page_title="Demo Dashboard",
    layout="wide",
)

pages = [
    st.Page("pages/home.py", title="Home", default=True),
    st.Page("pages/demo.py", title="Demo"),
]

pg = st.navigation(pages)
pg.run()
