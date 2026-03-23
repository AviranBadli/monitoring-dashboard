import streamlit as st
import pandas as pd

from app.api_client import APIError

st.header("Reference Data")

api = st.session_state.api

tab_teams, tab_clouds, tab_gpu_types, tab_instance_types, tab_workload_types, tab_allocation_types = st.tabs(
    ["Teams", "Clouds", "GPU Types", "Instance Types", "Workload Types", "Allocation Types"]
)

# --- Teams ---
with tab_teams:
    try:
        teams = api.list_teams()
        if teams:
            st.dataframe(pd.DataFrame(teams), width="stretch", hide_index=True)
        else:
            st.info("No teams found.")
    except APIError as e:
        st.error(f"Failed to load teams: {e.message}")
        teams = []

    with st.form("create_team", clear_on_submit=True):
        st.subheader("Add Team")
        name = st.text_input("Team Name")
        if st.form_submit_button("Create Team"):
            if name:
                try:
                    api.create_team(name)
                    st.success(f"Created team '{name}'")
                    st.rerun()
                except APIError as e:
                    st.error(e.message)

    if teams:
        st.subheader("Delete Team")
        team_to_delete = st.selectbox("Select team", [t["name"] for t in teams], key="del_team")
        if st.button("Delete Team", type="secondary"):
            try:
                api.delete_team(team_to_delete)
                st.success(f"Deleted team '{team_to_delete}'")
                st.rerun()
            except APIError as e:
                st.error(e.message)

# --- Clouds ---
with tab_clouds:
    try:
        clouds = api.list_clouds()
        if clouds:
            st.dataframe(pd.DataFrame(clouds), width="stretch", hide_index=True)
        else:
            st.info("No clouds found.")
    except APIError as e:
        st.error(f"Failed to load clouds: {e.message}")
        clouds = []

    with st.form("create_cloud", clear_on_submit=True):
        st.subheader("Add Cloud")
        name = st.text_input("Cloud Name")
        if st.form_submit_button("Create Cloud"):
            if name:
                try:
                    api.create_cloud(name)
                    st.success(f"Created cloud '{name}'")
                    st.rerun()
                except APIError as e:
                    st.error(e.message)

    if clouds:
        st.subheader("Delete Cloud")
        cloud_to_delete = st.selectbox("Select cloud", [c["name"] for c in clouds], key="del_cloud")
        if st.button("Delete Cloud", type="secondary"):
            try:
                api.delete_cloud(cloud_to_delete)
                st.success(f"Deleted cloud '{cloud_to_delete}'")
                st.rerun()
            except APIError as e:
                st.error(e.message)

# --- GPU Types ---
with tab_gpu_types:
    try:
        gpu_types = api.list_gpu_types()
        if gpu_types:
            st.dataframe(pd.DataFrame(gpu_types), width="stretch", hide_index=True)
        else:
            st.info("No GPU types found.")
    except APIError as e:
        st.error(f"Failed to load GPU types: {e.message}")
        gpu_types = []

    with st.form("create_gpu_type", clear_on_submit=True):
        st.subheader("Add GPU Type")
        name = st.text_input("Name (kebab-case, e.g. a100-40gb-sxm4)")
        display_name = st.text_input("Display Name (e.g. A100 40GB SXM4)")
        family = st.text_input("Family (e.g. A100)")
        memory_gb = st.number_input("Memory (GB)", min_value=0, value=0, step=1)
        variant = st.text_input("Variant (optional)")
        if st.form_submit_button("Create GPU Type"):
            if name and display_name and family:
                try:
                    api.create_gpu_type(
                        name=name,
                        display_name=display_name,
                        family=family,
                        memory_gb=int(memory_gb),
                        variant=variant or None,
                    )
                    st.success(f"Created GPU type '{name}'")
                    st.rerun()
                except APIError as e:
                    st.error(e.message)

    if gpu_types:
        st.subheader("Delete GPU Type")
        gt_to_delete = st.selectbox("Select GPU type", [g["name"] for g in gpu_types], key="del_gpu_type")
        if st.button("Delete GPU Type", type="secondary"):
            try:
                api.delete_gpu_type(gt_to_delete)
                st.success(f"Deleted GPU type '{gt_to_delete}'")
                st.rerun()
            except APIError as e:
                st.error(e.message)

# --- Instance Types ---
with tab_instance_types:
    try:
        instance_types = api.list_instance_types()
        if instance_types:
            st.dataframe(pd.DataFrame(instance_types), width="stretch", hide_index=True)
        else:
            st.info("No instance types found.")
    except APIError as e:
        st.error(f"Failed to load instance types: {e.message}")
        instance_types = []

    with st.form("create_instance_type", clear_on_submit=True):
        st.subheader("Add Instance Type")
        name = st.text_input("Name (e.g. p4d.24xlarge)")

        try:
            cloud_names = [c["name"] for c in api.list_clouds()]
        except APIError:
            cloud_names = []
        cloud_name = st.selectbox("Cloud", cloud_names) if cloud_names else st.text_input("Cloud Name")

        try:
            gt_names = [g["name"] for g in api.list_gpu_types()]
        except APIError:
            gt_names = []
        gpu_type_name = st.selectbox("GPU Type", gt_names) if gt_names else st.text_input("GPU Type Name")

        gpu_count = st.number_input("GPU Count", min_value=0.0625, value=1.0, step=1.0)
        instance_family = st.text_input("Instance Family (e.g. p4d)")

        if st.form_submit_button("Create Instance Type"):
            if name and cloud_name and gpu_type_name and instance_family:
                try:
                    api.create_instance_type(
                        name=name,
                        cloud_name=cloud_name,
                        gpu_type_name=gpu_type_name,
                        gpu_count=gpu_count,
                        instance_family=instance_family,
                    )
                    st.success(f"Created instance type '{name}'")
                    st.rerun()
                except APIError as e:
                    st.error(e.message)

    if instance_types:
        st.subheader("Delete Instance Type")
        it_to_delete = st.selectbox(
            "Select instance type", [i["name"] for i in instance_types], key="del_instance_type"
        )
        if st.button("Delete Instance Type", type="secondary"):
            try:
                api.delete_instance_type(it_to_delete)
                st.success(f"Deleted instance type '{it_to_delete}'")
                st.rerun()
            except APIError as e:
                st.error(e.message)

# --- Workload Types ---
with tab_workload_types:
    try:
        workload_types = api.list_workload_types()
        if workload_types:
            st.dataframe(pd.DataFrame(workload_types), width="stretch", hide_index=True)
        else:
            st.info("No workload types found.")
    except APIError as e:
        st.error(f"Failed to load workload types: {e.message}")
        workload_types = []

    with st.form("create_workload_type", clear_on_submit=True):
        st.subheader("Add Workload Type")
        name = st.text_input("Name")
        if st.form_submit_button("Create Workload Type"):
            if name:
                try:
                    api.create_workload_type(name)
                    st.success(f"Created workload type '{name}'")
                    st.rerun()
                except APIError as e:
                    st.error(e.message)

    if workload_types:
        st.subheader("Delete Workload Type")
        wt_to_delete = st.selectbox(
            "Select workload type", [w["name"] for w in workload_types], key="del_workload_type"
        )
        if st.button("Delete Workload Type", type="secondary"):
            try:
                api.delete_workload_type(wt_to_delete)
                st.success(f"Deleted workload type '{wt_to_delete}'")
                st.rerun()
            except APIError as e:
                st.error(e.message)

# --- Allocation Types ---
with tab_allocation_types:
    try:
        allocation_types = api.list_allocation_types()
        if allocation_types:
            st.dataframe(pd.DataFrame(allocation_types), width="stretch", hide_index=True)
        else:
            st.info("No allocation types found.")
    except APIError as e:
        st.error(f"Failed to load allocation types: {e.message}")
        allocation_types = []

    with st.form("create_allocation_type", clear_on_submit=True):
        st.subheader("Add Allocation Type")
        name = st.text_input("Name")
        priority = st.number_input("Priority", min_value=0, value=0, step=1)
        if st.form_submit_button("Create Allocation Type"):
            if name:
                try:
                    api.create_allocation_type(name, int(priority))
                    st.success(f"Created allocation type '{name}'")
                    st.rerun()
                except APIError as e:
                    st.error(e.message)

    if allocation_types:
        st.subheader("Delete Allocation Type")
        at_to_delete = st.selectbox(
            "Select allocation type", [a["name"] for a in allocation_types], key="del_allocation_type"
        )
        if st.button("Delete Allocation Type", type="secondary"):
            try:
                api.delete_allocation_type(at_to_delete)
                st.success(f"Deleted allocation type '{at_to_delete}'")
                st.rerun()
            except APIError as e:
                st.error(e.message)
