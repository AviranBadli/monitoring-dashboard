import streamlit as st

st.set_page_config(
    page_title="Kueue Dashboard",
    layout="wide",
)

pages = [
    st.Page("pages/live.py", title="Kueue Live View", default=True),
    st.Page("pages/history.py", title="Kueue Historical View"),
]

pg = st.navigation(pages)
pg.run()
