import streamlit as st

st.set_page_config(
    page_title="Demo Dashboard",
    layout="wide",
)

pages = [
    st.Page("pages/home.py", title="Home", default=True),
    st.Page("pages/live.py", title="Kueue Live View"),
    st.Page("pages/history.py", title="Kueue History"),
]

pg = st.navigation(pages)
pg.run()
