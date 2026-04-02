import datetime
import logging

import altair as alt
import httpx
import pandas as pd
import streamlit as st

from config import settings

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)
logger.addHandler(logging.StreamHandler())

METRICS = [
    ("kube_customresource_kueue_localqueue_pending_workloads", "Pending"),
    ("kube_customresource_kueue_localqueue_admitted_workloads", "Admitted"),
]

STATE_COLORS = {
    "Pending": "#aed6f1",
    "Admitted": "#abebc6",
}


def query_thanos_range(
    metric: str, start: datetime.datetime, end: datetime.datetime, step: str
) -> list:
    """Query Thanos query_range API for a given metric."""
    headers = {}
    if settings.THANOS_TOKEN:
        headers["Authorization"] = f"Bearer {settings.THANOS_TOKEN}"
    url = f"{settings.THANOS_URL}/api/v1/query_range"
    params = {
        "query": metric,
        "start": int(start.timestamp()) // 10 * 10,
        "end": int(end.timestamp()) // 10 * 10,
        "step": step,
    }
    resp = httpx.get(url, params=params, headers=headers, verify=False, timeout=30)
    logger.info("Thanos query: %s", resp.request.url)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "success":
        raise ValueError(f"Thanos query failed: {data}")
    return data.get("data", {}).get("result", [])


def build_dataframe(start: datetime.datetime, end: datetime.datetime, step: str) -> pd.DataFrame:
    """Query all three metrics and combine into a single DataFrame."""
    rows = []
    for metric_name, label in METRICS:
        results = query_thanos_range(metric_name, start, end, step)
        for series in results:
            lq = series.get("metric", {}).get("localqueue", "unknown")
            ns = series.get("metric", {}).get("exported_namespace", "unknown")
            queue_label = f"{ns}/{lq}"
            for timestamp, value in series.get("values", []):
                rows.append(
                    {
                        "time": pd.to_datetime(timestamp, unit="s", utc=True),
                        "queue": queue_label,
                        "state": label,
                        "count": float(value),
                    }
                )
    if not rows:
        return pd.DataFrame(columns=["time", "queue", "state", "count"])
    return pd.DataFrame(rows)


def build_gpu_util_dataframe(
    start: datetime.datetime, end: datetime.datetime, step: str
) -> pd.DataFrame:
    """Query DCGM_FI_DEV_GPU_UTIL and return a DataFrame with per-GPU utilization over time."""
    results = query_thanos_range("DCGM_FI_DEV_GPU_UTIL", start, end, step)
    rows = []
    for series in results:
        metric = series.get("metric", {})
        hostname = metric.get("Hostname", "unknown")
        gpu_id = metric.get("gpu", "0")
        gpu_label = f"GPU {gpu_id}"
        for timestamp, value in series.get("values", []):
            rows.append(
                {
                    "time": pd.to_datetime(timestamp, unit="s", utc=True),
                    "node": hostname,
                    "gpu": gpu_label,
                    "utilization": float(value),
                }
            )
    if not rows:
        return pd.DataFrame(columns=["time", "node", "gpu", "utilization"])
    return pd.DataFrame(rows)


st.title("Kueue Historical View")
st.text("Historical view of Kueue local queue workload activity from Thanos metrics.")

col1, col2, col3 = st.columns(3)
with col1:
    minutes_back = st.selectbox(
        "Time range", [5, 15, 30, 60, 120, 180, 300], index=1, format_func=lambda m: f"{m}m"
    )
with col2:
    step = st.selectbox("Resolution", ["10s", "30s", "1m", "5m"], index=0)
with col3:
    end_time = st.date_input("End date", value=datetime.date.today())

end_dt = datetime.datetime.combine(
    end_time, datetime.time(23, 59, 59), tzinfo=datetime.timezone.utc
)
if end_time == datetime.date.today():
    end_dt = datetime.datetime.now(datetime.timezone.utc)
start_dt = end_dt - datetime.timedelta(minutes=minutes_back)


@st.fragment(run_every=10)
def render_charts():
    # Recalculate end/start on each refresh so the window slides forward
    now = datetime.datetime.now(datetime.timezone.utc)
    end = now if end_time == datetime.date.today() else end_dt
    start = end - datetime.timedelta(minutes=minutes_back)

    try:
        df = build_dataframe(start, end, step)
    except Exception as e:
        st.error(f"Failed to query Thanos: {e}")
        return

    if df.empty:
        st.info("No data returned for the selected time range.")
        return

    queues = sorted(df["queue"].unique())
    selected_queues = st.multiselect("Filter queues", queues, default=queues)
    if selected_queues:
        df = df[df["queue"].isin(selected_queues)]

    # Aggregate across queues per time bucket and state
    agg_df = df.groupby(["time", "state"], as_index=False)["count"].sum()

    chart = (
        alt.Chart(agg_df)
        .mark_bar(size=20)
        .encode(
            x=alt.X(
                "time:T",
                title="Time",
                axis=alt.Axis(format="%H:%M:%S", labelAngle=-90),
                scale=alt.Scale(domain=[start.isoformat(), end.isoformat()]),
            ),
            y=alt.Y("count:Q", title="Workloads", stack="zero"),
            color=alt.Color(
                "state:N",
                title="State",
                scale=alt.Scale(
                    domain=list(STATE_COLORS.keys()),
                    range=list(STATE_COLORS.values()),
                ),
            ),
            tooltip=["time:T", "state:N", "count:Q"],
        )
        .properties(height=400)
    )

    st.altair_chart(chart, use_container_width=True)

    st.subheader("Per-LocalQueue Breakdown")

    for queue in sorted(df["queue"].unique()):
        q_df = df[df["queue"] == queue].groupby(["time", "state"], as_index=False)["count"].sum()
        q_chart = (
            alt.Chart(q_df)
            .mark_bar(size=20)
            .encode(
                x=alt.X(
                    "time:T",
                    title="Time",
                    axis=alt.Axis(format="%H:%M:%S", labelAngle=-90),
                    scale=alt.Scale(domain=[start.isoformat(), end.isoformat()]),
                ),
                y=alt.Y("count:Q", title="Workloads", stack="zero"),
                color=alt.Color(
                    "state:N",
                    title="State",
                    scale=alt.Scale(
                        domain=list(STATE_COLORS.keys()),
                        range=list(STATE_COLORS.values()),
                    ),
                ),
                tooltip=["time:T", "state:N", "count:Q"],
            )
            .properties(height=250)
        )
        st.markdown(f"**{queue}**")
        st.altair_chart(q_chart, use_container_width=True)

    # GPU Utilization section
    if settings.SHOW_GPU_UTIL:
        st.subheader("GPU Utilization per Node")
        try:
            gpu_df = build_gpu_util_dataframe(start, end, step)
        except Exception as e:
            st.error(f"Failed to query GPU utilization: {e}")
            gpu_df = pd.DataFrame()

        if gpu_df.empty:
            st.info("No GPU utilization data returned for the selected time range.")
        else:
            nodes = sorted(gpu_df["node"].unique())
            selected_nodes = st.multiselect("Filter nodes", nodes, default=nodes)
            if selected_nodes:
                gpu_df = gpu_df[gpu_df["node"].isin(selected_nodes)]

            for node in sorted(gpu_df["node"].unique()):
                node_df = gpu_df[gpu_df["node"] == node]
                gpu_chart = (
                    alt.Chart(node_df)
                    .mark_line(point=True)
                    .encode(
                        x=alt.X(
                            "time:T",
                            title="Time",
                            axis=alt.Axis(format="%H:%M:%S", labelAngle=-90),
                            scale=alt.Scale(domain=[start.isoformat(), end.isoformat()]),
                        ),
                        y=alt.Y(
                            "utilization:Q",
                            title="Utilization %",
                            axis=alt.Axis(values=[0, 25, 50, 75, 100], format="d", tickCount=5),
                            scale=alt.Scale(domain=[0, 100]),
                        ),
                        color=alt.Color("gpu:N", title="GPU"),
                        tooltip=["time:T", "gpu:N", "utilization:Q"],
                    )
                    .properties(height=250)
                )
                st.markdown(f"**{node}**")
                st.altair_chart(gpu_chart, use_container_width=True)


render_charts()
