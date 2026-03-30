import httpx
import streamlit as st

from config import settings

PHASE_DISPLAY = {
    "Active": {"icon": "\u2705", "color": "background-color: #b6e2b6"},
    "Terminating": {"icon": "\u23f3", "color": "background-color: #f5c6a1"},
    "Terminated": {"icon": "\u26d4", "color": "background-color: #d3d3d3"},
}


def query_thanos(query: str) -> dict:
    """Execute an instant query against the Thanos API."""
    response = httpx.get(
        f"{settings.THANOS_URL}/api/v1/query",
        params={"query": query},
        headers={"Authorization": f"Bearer {settings.THANOS_TOKEN}"},
        verify=False,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_localqueue_events():
    """Fetch kueue workload metrics and derive namespaces from them."""
    workload_metrics = [
        ("pending", "kube_customresource_kueue_localqueue_pending_workloads"),
        ("admitted", "kube_customresource_kueue_localqueue_admitted_workloads"),
        ("reserving", "kube_customresource_kueue_localqueue_reserving_workloads"),
    ]

    # Collect data keyed by (namespace, cluster_queue, localqueue)
    all_queue_pairs = set()  # (cluster_queue, localqueue)
    all_namespaces = set()
    workload_data = {}  # {(namespace, cluster_queue, localqueue): {metric_key: value}}
    for key, metric_name in workload_metrics:
        result = query_thanos(metric_name)
        if result.get("status") == "success":
            for series in result["data"]["result"]:
                ns = series["metric"].get("exported_namespace", "unknown")
                cq = series["metric"].get("cluster_queue", "unknown")
                lq = series["metric"].get("localqueue", "unknown")
                all_namespaces.add(ns)
                all_queue_pairs.add((cq, lq))
                if series["value"]:
                    latest_value = float(series["value"][1])
                    combo = (ns, cq, lq)
                    if combo not in workload_data:
                        workload_data[combo] = {}
                    workload_data[combo][key] = workload_data[combo].get(key, 0) + latest_value

    sorted_pairs = sorted(all_queue_pairs)
    sorted_namespaces = sorted(all_namespaces)

    # Build row data with raw counts
    result_rows = []
    for ns in sorted_namespaces:
        queue_data = {}
        for cq, lq in sorted_pairs:
            data = workload_data.get((ns, cq, lq), {})
            queue_data[(cq, lq)] = {
                "pending": int(data.get("pending", 0)),
                "admitted": int(data.get("admitted", 0)),
                "reserving": int(data.get("reserving", 0)),
            }
        result_rows.append({"namespace": ns, "phase": "Active", "queues": queue_data})

    # Test row — set TEST_ROW = True to add a dummy row with sample workload values
    TEST_ROW = settings.TEST_ROW
    if TEST_ROW and sorted_pairs:
        samples = [
            {"pending": 1, "admitted": 2, "reserving": 0},
            {"pending": 0, "admitted": 4, "reserving": 0},
            {"pending": 2, "admitted": 1, "reserving": 1},
        ]
        test_queues = {}
        for i, (cq, lq) in enumerate(sorted_pairs):
            test_queues[(cq, lq)] = samples[i % len(samples)]
        result_rows.append(
            {"namespace": "\u26a0\ufe0f test-namespace", "phase": "Active", "queues": test_queues}
        )

    return sorted_pairs, result_rows


WORKLOAD_COLORS = {
    "P": "#aed6f1",  # pastel blue
    "A": "#abebc6",  # pastel green
    "R": "#f5b7b1",  # pastel red
}


def render_workload_cell(counts: dict) -> str:
    """Render pending/admitted/reserving as individually colored HTML spans."""
    spans = []
    for letter, key in [("P", "pending"), ("A", "admitted"), ("R", "reserving")]:
        count = counts.get(key, 0)
        color = WORKLOAD_COLORS[letter]
        for _ in range(count):
            spans.append(
                f'<span style="background-color:{color};padding:2px 6px;'
                f"margin:1px;border-radius:3px;font-weight:bold;"
                f'font-size:0.85em;display:inline-block">{letter}</span>'
            )
    return "".join(spans)


def render_html_table(sorted_pairs, rows):
    """Build an HTML table with two-level headers and colored workload badges."""
    # Group queue pairs by cluster_queue for colspan
    cq_groups = {}
    for cq, lq in sorted_pairs:
        cq_groups.setdefault(cq, []).append(lq)

    html = []
    html.append(
        '<table style="width:100%;border-collapse:collapse;font-family:sans-serif;font-size:0.9em">'
    )

    # Top header row: cluster_queue names with colspan
    html.append("<thead><tr>")
    html.append(
        '<th rowspan="2" style="border:1px solid #ddd;padding:8px;background:#f8f8f8">Namespace</th>'
    )
    for cq, lqs in cq_groups.items():
        html.append(
            f'<th colspan="{len(lqs)}" style="border:1px solid #ddd;padding:8px;'
            f'background:#e8e8e8;text-align:center">{cq}</th>'
        )
    html.append("</tr>")

    # Second header row: localqueue names
    html.append("<tr>")
    for cq, lqs in cq_groups.items():
        for lq in lqs:
            html.append(
                f'<th style="border:1px solid #ddd;padding:8px;background:#f0f0f0;'
                f'text-align:center;font-size:0.85em">{lq}</th>'
            )
    html.append("</tr></thead>")

    # Data rows
    html.append("<tbody>")
    for row in rows:
        ns = row["namespace"]
        phase = row["phase"]
        phase_info = PHASE_DISPLAY.get(phase, {"icon": "", "color": ""})

        html.append("<tr>")
        html.append(
            f'<td style="border:1px solid #ddd;padding:8px;{phase_info["color"]}">'
            f'{ns} {phase_info["icon"]}</td>'
        )
        for cq, lq in sorted_pairs:
            counts = row["queues"].get((cq, lq), {})
            cell_html = render_workload_cell(counts)
            html.append(
                f'<td style="border:1px solid #ddd;padding:6px;text-align:center">{cell_html}</td>'
            )
        html.append("</tr>")
    html.append("</tbody></table>")

    return "\n".join(html)


st.title("GPUaaS Kueue Activity")
st.subheader("Workflow activity: Pending/Admitted/Reserving")

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
        sorted_pairs, rows = get_localqueue_events()
        if not rows:
            st.info("No namespace events found.")
        else:
            table_html = render_html_table(sorted_pairs, rows)
            st.markdown(table_html, unsafe_allow_html=True)
    except httpx.HTTPStatusError as e:
        st.error(f"API error: {e.response.status_code} — {e.response.text}")
    except httpx.ConnectError:
        st.error(f"Cannot connect to Thanos at {settings.THANOS_URL}")
    except Exception as e:
        st.error(f"Error fetching namespace events: {e}")


namespace_table()
