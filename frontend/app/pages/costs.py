import streamlit as st
import pandas as pd
import plotly.express as px

from app.api_client import APIError
from app.components.filters import time_range_filter

st.header("Cost Explorer")

api = st.session_state.api

# --- Load reference data ---
try:
    clouds = api.list_clouds()
    cloud_names = [c["name"] for c in clouds]
except APIError:
    cloud_names = []

try:
    gpu_types = api.list_gpu_types()
    gt_names = [g["name"] for g in gpu_types]
except APIError:
    gt_names = []

try:
    workload_types = api.list_workload_types()
    wt_names = [w["name"] for w in workload_types]
except APIError:
    wt_names = []

try:
    clusters = api.list_clusters()
    cluster_names = [c["name"] for c in clusters]
except APIError:
    cluster_names = []

# --- Filters ---
with st.expander("Filters", expanded=True):
    start_time, end_time = time_range_filter(key_prefix="cost_")

    col1, col2 = st.columns(2)
    with col1:
        selected_clouds = st.multiselect("Cloud", cloud_names, default=cloud_names)
        selected_gpu_types = st.multiselect("GPU Type", gt_names, default=gt_names)
    with col2:
        selected_wt = st.multiselect("Workload Type", wt_names, default=wt_names)
        selected_clusters = st.multiselect(
            "Cluster", cluster_names, default=cluster_names
        )

    group_by = st.selectbox(
        "Group by",
        ["Cloud", "GPU Type", "Workload Type", "Cluster", "Node"],
    )

# --- Fetch and join data ---
# Build node metadata lookup
try:
    nodes = api.list_nodes()
except APIError:
    nodes = []
    st.error("Failed to load nodes.")

# Build node -> metadata mapping
node_meta = {}
for node in nodes:
    cluster_name = node.get("cluster_name", "")
    instance_type_name = node.get("instance_type_name", "")

    # Find cloud from cluster
    cloud_name = ""
    for c in clusters:
        if c["name"] == cluster_name:
            cloud_name = c.get("cloud_name", "")
            break

    # Find gpu_type from instance_type
    gpu_type_name = ""
    try:
        instance_types = api.list_instance_types()
        for it in instance_types:
            if it["name"] == instance_type_name:
                gpu_type_name = it.get("gpu_type_name", "")
                break
    except APIError:
        pass

    node_meta[node["name"]] = {
        "cloud": cloud_name,
        "cluster": cluster_name,
        "gpu_type": gpu_type_name,
        "instance_type": instance_type_name,
    }

# Filter nodes by selected filters
filtered_nodes = []
for name, meta in node_meta.items():
    if meta["cloud"] and meta["cloud"] not in selected_clouds:
        continue
    if meta["gpu_type"] and meta["gpu_type"] not in selected_gpu_types:
        continue
    if meta["cluster"] and meta["cluster"] not in selected_clusters:
        continue
    filtered_nodes.append(name)

# Fetch costs for filtered nodes
all_costs = []
for node_name in filtered_nodes:
    try:
        costs = api.get_node_costs(
            node_name,
            start=start_time.isoformat() if start_time else None,
            end=end_time.isoformat() if end_time else None,
        )
        for cost_entry in costs:
            meta = node_meta.get(node_name, {})
            cost_entry["node"] = node_name
            cost_entry["cloud"] = meta.get("cloud", "")
            cost_entry["gpu_type"] = meta.get("gpu_type", "")
            cost_entry["cluster"] = meta.get("cluster", "")
        all_costs.extend(costs)
    except APIError:
        pass

# Filter by workload type
if selected_wt:
    all_costs = [c for c in all_costs if c.get("workload_type_name", "") in selected_wt]

if not all_costs:
    st.info("No cost data found for the selected filters.")
    st.stop()

df = pd.DataFrame(all_costs)
df["date"] = pd.to_datetime(df["date"])

# --- Metrics ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Cost", f"${df['cost'].sum():,.2f}")
with col2:
    n_days = max((df["date"].max() - df["date"].min()).days, 1)
    st.metric("Avg Daily Cost", f"${df['cost'].sum() / n_days:,.2f}")
with col3:
    st.metric("Data Points", len(df))

# --- Map group_by to column ---
group_col_map = {
    "Cloud": "cloud",
    "GPU Type": "gpu_type",
    "Workload Type": "workload_type_name",
    "Cluster": "cluster",
    "Node": "node",
}
group_col = group_col_map[group_by]

# --- Charts ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader(f"Cost Over Time by {group_by}")
    ts_df = (
        df.groupby([pd.Grouper(key="date", freq="D"), group_col])["cost"]
        .sum()
        .reset_index()
    )
    fig_ts = px.line(
        ts_df,
        x="date",
        y="cost",
        color=group_col,
        labels={"cost": "Cost ($)", "date": "Date"},
    )
    st.plotly_chart(fig_ts, width="stretch")

with col_right:
    st.subheader(f"Cost Breakdown by {group_by}")
    bar_df = (
        df.groupby(group_col)["cost"]
        .sum()
        .reset_index()
        .sort_values("cost", ascending=False)
    )
    fig_bar = px.bar(bar_df, x=group_col, y="cost", labels={"cost": "Cost ($)"})
    st.plotly_chart(fig_bar, width="stretch")

st.subheader(f"Cost Proportions by {group_by}")
pie_df = df.groupby(group_col)["cost"].sum().reset_index()
fig_pie = px.pie(pie_df, values="cost", names=group_col)
st.plotly_chart(fig_pie, width="stretch")

# --- Data table ---
st.subheader("Raw Data")
st.dataframe(df, width="stretch", hide_index=True)
st.download_button(
    "Download CSV",
    df.to_csv(index=False),
    "cost_data.csv",
    "text/csv",
)
