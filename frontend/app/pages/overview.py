from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px

from app.api_client import APIError

st.header("GPU Resource Dashboard")

api = st.session_state.api

# --- Summary metrics ---
col1, col2, col3, col4 = st.columns(4)

try:
    clusters = api.list_clusters()
except APIError:
    clusters = []
try:
    nodes = api.list_nodes()
except APIError:
    nodes = []
try:
    gpus = api.list_gpus()
except APIError:
    gpus = []
try:
    teams = api.list_teams()
except APIError:
    teams = []

with col1:
    st.metric("Clusters", len(clusters))
with col2:
    st.metric("Nodes", len(nodes))
with col3:
    st.metric("GPUs", len(gpus))
with col4:
    st.metric("Teams", len(teams))

# --- Current allocations ---
st.subheader("Active Allocations")
now = datetime.now().isoformat()
try:
    allocations = api.list_allocations(start_time=now, end_time=now)
except APIError:
    allocations = []

if allocations:
    df = pd.DataFrame(allocations)
    display_cols = [c for c in ["id", "node_name", "team_name", "workload_type_name", "allocation_type_name", "start_time", "end_time"] if c in df.columns]
    st.dataframe(df[display_cols], width="stretch", hide_index=True)
else:
    st.info("No active allocations.")

# --- Charts ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("GPUs per Cluster")
    if gpus:
        gpu_df = pd.DataFrame(gpus)
        if "gpu_cluster" in gpu_df.columns:
            cluster_counts = gpu_df["gpu_cluster"].value_counts().reset_index()
            cluster_counts.columns = ["Cluster", "GPU Count"]
            fig = px.bar(cluster_counts, x="Cluster", y="GPU Count")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No cluster data available.")
    else:
        st.info("No GPU data available.")

with col_right:
    st.subheader("Nodes per Team")
    if nodes:
        node_df = pd.DataFrame(nodes)
        if "team_name" in node_df.columns:
            team_counts = node_df["team_name"].value_counts().reset_index()
            team_counts.columns = ["Team", "Node Count"]
            fig = px.bar(team_counts, x="Team", y="Node Count")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No team data available.")
    else:
        st.info("No node data available.")
