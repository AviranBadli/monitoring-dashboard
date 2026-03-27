from datetime import datetime, timedelta, timezone
from time import time

import httpx
import pandas as pd
import streamlit as st

from config import settings


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

    phase_emojis = {
        "Active": "\u2705 Active",
        "Terminating": "\u23f3 Terminating",
        "Terminated": "\u26d4 Terminated",
    }
    df["Phase"] = df["Phase"].map(lambda p: phase_emojis.get(p, p))
    df = df.drop(columns=["Timestamp"])
    return df


st.title("Demo")
st.subheader("Namespace Events")

try:
    df = get_namespace_events()
    if df.empty:
        st.info("No namespace events found.")
    else:
        phase_colors = {
            "\u2705 Active": "background-color: #b6e2b6",
            "\u23f3 Terminating": "background-color: #f5c6a1",
            "\u26d4 Terminated": "background-color: #d3d3d3",
        }

        def color_phase(val):
            return phase_colors.get(val, "")

        styled = df.style.map(color_phase, subset=["Phase"])
        st.dataframe(styled, use_container_width=True)
except httpx.HTTPStatusError as e:
    st.error(f"API error: {e.response.status_code} — {e.response.text}")
except httpx.ConnectError:
    st.error(f"Cannot connect to Thanos at {settings.THANOS_URL}")
except Exception as e:
    st.error(f"Error fetching namespace events: {e}")
