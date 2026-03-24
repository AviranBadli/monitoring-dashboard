from datetime import datetime, time

import streamlit as st

from app.api_client import APIClient, APIError


def time_range_filter(key_prefix: str = "") -> tuple[datetime | None, datetime | None]:
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", value=None, key=f"{key_prefix}start_date")
    with col2:
        end_date = st.date_input("End date", value=None, key=f"{key_prefix}end_date")

    start = datetime.combine(start_date, time.min) if start_date else None
    end = datetime.combine(end_date, time.max) if end_date else None
    return start, end


def team_filter(api: APIClient, key_prefix: str = "") -> str | None:
    try:
        teams = api.list_teams()
        names = [t["name"] for t in teams]
    except APIError:
        names = []
    options = ["All"] + names
    selected = st.selectbox("Team", options, key=f"{key_prefix}team_filter")
    return None if selected == "All" else selected


def node_filter(api: APIClient, key_prefix: str = "") -> str | None:
    try:
        nodes = api.list_nodes()
        names = [n["name"] for n in nodes]
    except APIError:
        names = []
    options = ["All"] + names
    selected = st.selectbox("Node", options, key=f"{key_prefix}node_filter")
    return None if selected == "All" else selected


def cluster_filter(api: APIClient, key_prefix: str = "") -> str | None:
    try:
        clusters = api.list_clusters()
        names = [c["name"] for c in clusters]
    except APIError:
        names = []
    options = ["All"] + names
    selected = st.selectbox("Cluster", options, key=f"{key_prefix}cluster_filter")
    return None if selected == "All" else selected
