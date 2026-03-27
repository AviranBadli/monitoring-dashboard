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

    workload_metrics = [
        ("pending", "kube_customresource_kueue_localqueue_pending_workloads"),
        ("admitted", "kube_customresource_kueue_localqueue_admitted_workloads"),
        ("reserving", "kube_customresource_kueue_localqueue_reserving_workloads"),
    ]

    # Collect data keyed by (namespace, cluster_queue, localqueue)
    all_queue_pairs = set()  # (cluster_queue, localqueue)
    workload_data = {}  # {(namespace, cluster_queue, localqueue): {metric_key: value}}
    for key, metric_name in workload_metrics:
        result = query_thanos_range(f'{metric_name}{{exported_namespace=~"{ns_regex}"}}')
        if result.get("status") == "success":
            for series in result["data"]["result"]:
                ns = series["metric"].get("namespace", "unknown")
                cq = series["metric"].get("cluster_queue", "unknown")
                lq = series["metric"].get("localqueue", "unknown")
                all_queue_pairs.add((cq, lq))
                if series["values"]:
                    latest_value = float(series["values"][-1][1])
                    combo = (ns, cq, lq)
                    if combo not in workload_data:
                        workload_data[combo] = {}
                    workload_data[combo][key] = (
                        workload_data[combo].get(key, 0) + latest_value
                    )

    # Build MultiIndex columns: (cluster_queue, localqueue) for each queue pair
    sorted_pairs = sorted(all_queue_pairs)
    multi_cols = [("", "Namespace"), ("", "Phase")]
    for cq, lq in sorted_pairs:
        multi_cols.append((cq, lq))

    # Build rows with multi-level column data
    result_rows = []
    for _, row in df.iterrows():
        ns = row["Namespace"]
        phase = PHASE_DISPLAY[row["Phase"]]["label"] if row["Phase"] in PHASE_DISPLAY else row["Phase"]
        values = [ns, phase]
        for cq, lq in sorted_pairs:
            data = workload_data.get((ns, cq, lq), {})
            values.append(
                "{}/{}/{}".format(
                    int(data.get("pending", 0)),
                    int(data.get("admitted", 0)),
                    int(data.get("reserving", 0)),
                )
            )
        result_rows.append(values)

    multi_index = pd.MultiIndex.from_tuples(multi_cols)
    return pd.DataFrame(result_rows, columns=multi_index)


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

            def bold_workloads(val):
                return "font-weight: bold" if val != "0/0/0" else ""

            phase_col = ("", "Phase")
            workload_cols = [c for c in df.columns if c[0] != ""]
            styled = df.style.map(color_phase, subset=[phase_col])
            if workload_cols:
                styled = styled.map(bold_workloads, subset=workload_cols)
            st.dataframe(styled, use_container_width=True)
    except httpx.HTTPStatusError as e:
        st.error(f"API error: {e.response.status_code} — {e.response.text}")
    except httpx.ConnectError:
        st.error(f"Cannot connect to Thanos at {settings.THANOS_URL}")
    except Exception as e:
        st.error(f"Error fetching namespace events: {e}")


namespace_table()
