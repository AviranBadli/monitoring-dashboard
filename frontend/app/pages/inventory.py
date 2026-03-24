import streamlit as st
import pandas as pd

from app.api_client import APIError

st.header("Inventory")

api = st.session_state.api

# --- Filters ---
col1, col2, col3 = st.columns(3)

try:
    clouds = api.list_clouds()
    cloud_names = ["All"] + [c["name"] for c in clouds]
except APIError:
    cloud_names = ["All"]

try:
    clusters = api.list_clusters()
except APIError:
    clusters = []

try:
    gpu_types = api.list_gpu_types()
    gt_names = ["All"] + [g["name"] for g in gpu_types]
except APIError:
    gt_names = ["All"]

with col1:
    selected_cloud = st.selectbox("Cloud", cloud_names)
with col2:
    # Filter clusters by cloud if selected
    if selected_cloud != "All":
        filtered_clusters = [
            c for c in clusters if c.get("cloud_name") == selected_cloud
        ]
    else:
        filtered_clusters = clusters
    cluster_names = ["All"] + [c["name"] for c in filtered_clusters]
    selected_cluster = st.selectbox("Cluster", cluster_names)
with col3:
    selected_gpu_type = st.selectbox("GPU Type", gt_names)

# --- Tabs ---
tab_clusters, tab_nodes, tab_gpus = st.tabs(["Clusters", "Nodes", "GPUs"])

with tab_clusters:
    try:
        cluster_data = filtered_clusters
        if cluster_data:
            st.metric("Clusters", len(cluster_data))
            st.dataframe(pd.DataFrame(cluster_data), width="stretch", hide_index=True)
        else:
            st.info("No clusters found.")
    except APIError as e:
        st.error(f"Failed to load clusters: {e.message}")

with tab_nodes:
    try:
        cluster_arg = None if selected_cluster == "All" else selected_cluster
        nodes = api.list_nodes(cluster_name=cluster_arg)

        # Client-side filter by cloud if cluster isn't already filtering
        if selected_cloud != "All" and selected_cluster == "All":
            cluster_names_for_cloud = {c["name"] for c in filtered_clusters}
            nodes = [
                n for n in nodes if n.get("cluster_name") in cluster_names_for_cloud
            ]

        if nodes:
            st.metric("Nodes", len(nodes))
            st.dataframe(pd.DataFrame(nodes), width="stretch", hide_index=True)
        else:
            st.info("No nodes found.")
    except APIError as e:
        st.error(f"Failed to load nodes: {e.message}")

with tab_gpus:
    try:
        cluster_arg = None if selected_cluster == "All" else selected_cluster
        gpu_type_arg = None if selected_gpu_type == "All" else selected_gpu_type
        gpus = api.list_gpus(cluster_name=cluster_arg, gpu_type=gpu_type_arg)

        if gpus:
            st.metric("GPUs", len(gpus))
            st.dataframe(pd.DataFrame(gpus), width="stretch", hide_index=True)
        else:
            st.info("No GPUs found.")
    except APIError as e:
        st.error(f"Failed to load GPUs: {e.message}")
