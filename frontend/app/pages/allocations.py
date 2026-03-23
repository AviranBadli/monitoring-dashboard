import streamlit as st
import pandas as pd
from datetime import datetime, date, time, timedelta

from app.api_client import APIError
from app.components.filters import time_range_filter, team_filter, node_filter

st.header("Allocations")

api = st.session_state.api

# --- Filters ---
with st.expander("Filters", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        selected_team = team_filter(api, key_prefix="alloc_")
    with col2:
        selected_node = node_filter(api, key_prefix="alloc_")
    start_time, end_time = time_range_filter(key_prefix="alloc_")

# --- Allocations Table ---
try:
    allocations = api.list_allocations(
        team_name=selected_team,
        node_name=selected_node,
        start_time=start_time.isoformat() if start_time else None,
        end_time=end_time.isoformat() if end_time else None,
    )
except APIError as e:
    st.error(f"Failed to load allocations: {e.message}")
    allocations = []

if allocations:
    df = pd.DataFrame(allocations)
    display_cols = ["id", "node_name", "team_name", "workload_type_name", "allocation_type_name", "start_time", "end_time"]
    available_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[available_cols], width="stretch", hide_index=True)
else:
    st.info("No allocations found.")

# --- Create Allocation ---
st.subheader("Create Allocation")

try:
    nodes = api.list_nodes()
    node_names = [n["name"] for n in nodes]
except APIError:
    node_names = []

try:
    teams = api.list_teams()
    team_names = [t["name"] for t in teams]
except APIError:
    team_names = []

try:
    workload_types = api.list_workload_types()
    wt_names = [w["name"] for w in workload_types]
except APIError:
    wt_names = []

try:
    allocation_types = api.list_allocation_types()
    at_names = [a["name"] for a in allocation_types]
except APIError:
    at_names = []

with st.form("create_allocation", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        alloc_node = st.selectbox("Node", node_names) if node_names else st.text_input("Node Name")
        alloc_team = st.selectbox("Team", team_names) if team_names else st.text_input("Team Name")
    with col2:
        alloc_wt = st.selectbox("Workload Type", wt_names) if wt_names else st.text_input("Workload Type")
        alloc_at = st.selectbox("Allocation Type", at_names) if at_names else st.text_input("Allocation Type")

    col3, col4 = st.columns(2)
    with col3:
        alloc_start_date = st.date_input("Start Date", value=date.today())
        alloc_start_time = st.time_input("Start Time", value=time(0, 0))
    with col4:
        alloc_end_date = st.date_input("End Date", value=date.today() + timedelta(days=30))
        alloc_end_time = st.time_input("End Time", value=time(23, 59))

    if st.form_submit_button("Create Allocation", type="primary"):
        if alloc_node and alloc_team and alloc_wt and alloc_at:
            start_dt = datetime.combine(alloc_start_date, alloc_start_time)
            end_dt = datetime.combine(alloc_end_date, alloc_end_time)
            try:
                api.create_allocation({
                    "node_name": alloc_node,
                    "team_name": alloc_team,
                    "workload_type_name": alloc_wt,
                    "allocation_type_name": alloc_at,
                    "start_time": start_dt.isoformat(),
                    "end_time": end_dt.isoformat(),
                })
                st.success("Allocation created.")
                st.rerun()
            except APIError as e:
                st.error(e.message)

# --- Edit / Delete Allocation ---
if allocations:
    st.subheader("Edit Allocation")
    alloc_ids = [a["id"] for a in allocations]
    selected_id = st.selectbox("Select allocation to edit", alloc_ids, format_func=lambda x: f"ID {x}")

    selected_alloc = next(a for a in allocations if a["id"] == selected_id)

    with st.form("edit_allocation"):
        new_team = st.selectbox(
            "Team",
            team_names,
            index=team_names.index(selected_alloc["team_name"]) if selected_alloc["team_name"] in team_names else 0,
        ) if team_names else st.text_input("Team Name", value=selected_alloc.get("team_name", ""))

        col1, col2 = st.columns(2)
        with col1:
            existing_start = datetime.fromisoformat(selected_alloc["start_time"])
            new_start_date = st.date_input("Start Date", value=existing_start.date(), key="edit_start_d")
            new_start_time = st.time_input("Start Time", value=existing_start.time(), key="edit_start_t")
        with col2:
            existing_end = datetime.fromisoformat(selected_alloc["end_time"])
            new_end_date = st.date_input("End Date", value=existing_end.date(), key="edit_end_d")
            new_end_time = st.time_input("End Time", value=existing_end.time(), key="edit_end_t")

        if st.form_submit_button("Update Allocation"):
            updates = {}
            new_start_dt = datetime.combine(new_start_date, new_start_time)
            new_end_dt = datetime.combine(new_end_date, new_end_time)

            if new_team != selected_alloc.get("team_name"):
                updates["team_name"] = new_team
            if new_start_dt != existing_start:
                updates["start_time"] = new_start_dt.isoformat()
            if new_end_dt != existing_end:
                updates["end_time"] = new_end_dt.isoformat()

            if updates:
                try:
                    api.update_allocation(selected_id, updates)
                    st.success("Allocation updated.")
                    st.rerun()
                except APIError as e:
                    st.error(e.message)
            else:
                st.info("No changes detected.")

    st.subheader("Delete Allocation")
    del_id = st.selectbox("Select allocation to delete", alloc_ids, format_func=lambda x: f"ID {x}", key="del_alloc")
    if st.button("Delete Allocation", type="secondary"):
        try:
            api.delete_allocation(del_id)
            st.success(f"Deleted allocation {del_id}.")
            st.rerun()
        except APIError as e:
            st.error(e.message)
