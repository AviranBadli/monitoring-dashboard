import streamlit as st

st.title("Kueue Dashboard")

st.subheader("This dashboard shows the activity of the Kueue scheduler across the cluster.")
st.text("Please ensure you have configured the Thanos metrics endpoint in the config.py file.")

st.text("Navigate to the Live View or History pages to see the activity of the Kueue scheduler.")