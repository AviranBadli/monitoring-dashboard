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


render_charts()
