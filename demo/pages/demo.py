from datetime import datetime, timedelta, timezone
from time import time

import httpx
import pandas as pd
import streamlit as st

from config import settings

PHASE_DISPLAY = {
    "Active": {"label": "\u2705 Active", "color": "background-color: #b6e2b6"},
    "Terminating": {"label": "\u23f3 Terminating", "color": "background-color: #f5c6a1"},
    "Terminated": {"label": "\u26d4 Terminated", "color": "background-color: #d3d3d3"},
}


def query_thanos_range(query: str, ageSeconds: int = 600, step: str = "60s") -> dict:
    """Execute a range query against the Thanos API over the last N hours."""
    now = time()
    start = now - (ageSeconds)
    response = httpx.get(
        f"{settings.THANOS_URL}/api/v1/query_range",
        params={
            "query": query,
            "start": start,
            "end": now,
            "step": step,
        },
        headers={"Authorization": f"Bearer {settings.THANOS_TOKEN}"},
        verify=False,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_namespace_events() -> pd.DataFrame:
    """Fetch namespace phase events from the last hour."""
    rows = []

    result = query_thanos_range(
        'kube_namespace_status_phase{namespace!~"openshift.*|kube.*|redhat.*|cert.*|default.*|nvidia.*|rh.*|gpu.*|grafana.*"}'
    )
    if result.get("status") == "success":
        for series in result["data"]["result"]:
            namespace = series["metric"].get("namespace", "unknown")
            phase = series["metric"].get("phase", "unknown")

            # Take only the last data point for this namespace+phase
            active_values = [
                (ts, v) for ts, v in series["values"] if float(v) == 1
            ]
            if active_values:
                timestamp, _ = active_values[-1]
                rows.append(
                    {
                        "Namespace": namespace,
                        "Phase": phase,
                        "Timestamp": datetime.fromtimestamp(
                            timestamp, tz=timezone.utc
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

    if not rows:
        return pd.DataFrame(columns=["Namespace", "Phase"])

    df = pd.DataFrame(rows)
    # Keep only the latest phase per namespace
    df = (
        df.sort_values("Timestamp", ascending=False)
        .drop_duplicates(subset="Namespace", keep="first")
        .sort_values("Namespace")
        .reset_index(drop=True)
    )

    # Fetch workload metrics per namespace
    namespaces = df["Namespace"].unique().tolist()
    ns_regex = "|".join(namespaces)

    workload_metrics = {
        "Admitted Workloads": "kube_customresource_kueue_localqueue_admitted_workloads",
        "Pending Workloads": "kube_customresource_kueue_localqueue_pending_workloads",
        "Reserving Workloads": "kube_customresource_kueue_localqueue_reserving_workloads",
    }

    for col_name, metric_name in workload_metrics.items():
        by_ns = {}
        result = query_thanos_range(f'{metric_name}{{exported_namespace=~"{ns_regex}"}}')
        if result.get("status") == "success":
            for series in result["data"]["result"]:
                ns = series["metric"].get("namespace", "unknown")
                if series["values"]:
                    latest_value = float(series["values"][-1][1])
                    by_ns[ns] = by_ns.get(ns, 0) + latest_value
        df[col_name] = df["Namespace"].map(lambda ns, d=by_ns: int(d.get(ns, 0)))

    df["Phase"] = df["Phase"].map(lambda p: PHASE_DISPLAY[p]["label"] if p in PHASE_DISPLAY else p)
    df = df.drop(columns=["Timestamp"])
    return df


st.title("Demo")
st.subheader("Namespace Events")

# Disable the fade effect during fragment re-runs
st.markdown(
    """
    <style>
    [data-testid="stElementContainer"] { transition: none !important; opacity: 1 !important; }
    .stale-element { opacity: 1 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.fragment(run_every=5)
def namespace_table():
    try:
        df = get_namespace_events()
        if df.empty:
            st.info("No namespace events found.")
        else:
            label_to_color = {v["label"]: v["color"] for v in PHASE_DISPLAY.values()}

            def color_phase(val):
                return label_to_color.get(val, "")

            workload_cols = [
                "Admitted Workloads",
                "Pending Workloads",
                "Reserving Workloads",
            ]

            def bold_nonzero(val):
                return "font-weight: bold" if val > 0 else ""

            styled = df.style.map(color_phase, subset=["Phase"]).map(
                bold_nonzero, subset=workload_cols
            )
            st.dataframe(styled, use_container_width=True)
    except httpx.HTTPStatusError as e:
        st.error(f"API error: {e.response.status_code} — {e.response.text}")
    except httpx.ConnectError:
        st.error(f"Cannot connect to Thanos at {settings.THANOS_URL}")
    except Exception as e:
        st.error(f"Error fetching namespace events: {e}")


namespace_table()
