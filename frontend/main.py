import streamlit as st

from app.config import settings
from app.api_client import APIClient

st.set_page_config(
    page_title="GPU Resource Dashboard",
    layout="wide",
)


@st.cache_resource
def get_client():
    return APIClient(f"{settings.BACKEND_URL}{settings.API_V1_PREFIX}")

def get_health():
    return APIClient(f"{settings.BACKEND_URL}").health()

st.session_state.api = get_client()

# Sidebar health check
with st.sidebar:
    health = get_health()
    if health.get("status") == "healthy":
        st.success("Backend: Connected", icon="✅")
    else:
        st.warning("Backend: Degraded", icon="⚠️")

pages = {
    "View & Analyze": [
        st.Page("app/pages/overview.py", title="Overview", default=True),
        st.Page("app/pages/costs.py", title="Cost Explorer", icon="💰"),
        st.Page("app/pages/inventory.py", title="Inventory", icon="💻"),
    ],
    "Manage": [
        st.Page("app/pages/allocations.py", title="Allocations", icon="💰"),
        st.Page("app/pages/reference_data.py", title="Reference Data"),
    ],
}

pg = st.navigation(pages)
pg.run()
