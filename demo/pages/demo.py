import streamlit as st

from config import k8s_api


def get_cluster_queue_flavors(cq_name: str) -> list[dict]:
    """Fetch resource flavor names and nominalQuotas from a ClusterQueue spec."""
    try:
        cq = k8s_api.get_cluster_custom_object(
            group="kueue.x-k8s.io",
            version="v1beta1",
            plural="clusterqueues",
            name=cq_name,
        )
        flavors = []
        seen = set()
        for rg in cq.get("spec", {}).get("resourceGroups", []):
            for fq in rg.get("flavors", []):
                name = fq.get("name", "")
                if name and name not in seen:
                    seen.add(name)
                    quotas = {}
                    for res in fq.get("resources", []):
                        res_name = res.get("name", "")
                        quota = res.get("nominalQuota")
                        if res_name and quota is not None:
                            quotas[res_name] = quota
                    flavors.append({"name": name, "quotas": quotas})
        return flavors
    except Exception:
        return []


def get_workloads_by_localqueue(namespaces: set) -> dict:
    """Fetch Kueue Workloads and derive per-job queue state, grouped by (namespace, localqueue)."""
    workloads_map = {}  # {(namespace, localqueue): [(job_name, priority_class, state), ...]}
    for ns in namespaces:
        try:
            wl_list = k8s_api.list_namespaced_custom_object(
                group="kueue.x-k8s.io",
                version="v1beta1",
                plural="workloads",
                namespace=ns,
            )
            for wl in wl_list.get("items", []):
                lq = wl.get("spec", {}).get("queueName", "")
                if not lq:
                    continue

                # Get job name from owner reference
                job_name = wl.get("metadata", {}).get("name", "unknown")
                for ref in wl.get("metadata", {}).get("ownerReferences", []):
                    if ref.get("kind") == "Job":
                        job_name = ref.get("name", job_name)
                        break

                priority_class = wl.get("spec", {}).get("priorityClassName", "")

                # Sum nvidia.com/gpu requests across all podSets and containers
                gpu_count = 0
                for pod_set in wl.get("spec", {}).get("podSets", []):
                    containers = pod_set.get("template", {}).get("spec", {}).get("containers", [])
                    for container in containers:
                        requests = container.get("resources", {}).get("requests", {})
                        gpu_count += int(requests.get("nvidia.com/gpu", 0))

                # Derive state from conditions
                conditions = {
                    c["type"]: c["status"]
                    for c in wl.get("status", {}).get("conditions", [])
                }
                if conditions.get("Finished") == "True":
                    state = "F"
                elif conditions.get("Admitted") == "True":
                    state = "A"
                elif conditions.get("QuotaReserved") == "True":
                    state = "R"
                else:
                    state = "P"

                workloads_map.setdefault((ns, lq), []).append(
                    (job_name, priority_class, state, gpu_count)
                )
        except Exception:
            continue
    return workloads_map


def get_localqueue_events():
    """Fetch LocalQueue status from the Kubernetes API."""
    lq_list = k8s_api.list_cluster_custom_object(
        group="kueue.x-k8s.io",
        version="v1beta1",
        plural="localqueues",
    )

    # Collect data keyed by (namespace, cluster_queue, localqueue)
    all_queue_pairs = set()  # (cluster_queue, localqueue)
    all_namespaces = set()
    workload_data = {}  # {(namespace, cluster_queue, localqueue): {metric_key: value}}

    for item in lq_list.get("items", []):
        ns = item.get("metadata", {}).get("namespace", "unknown")
        lq = item.get("metadata", {}).get("name", "unknown")
        cq = item.get("spec", {}).get("clusterQueue", "unknown")
        status = item.get("status", {})

        all_namespaces.add(ns)
        all_queue_pairs.add((cq, lq))
        workload_data[(ns, cq, lq)] = {
            "pending": status.get("pendingWorkloads", 0),
            "admitted": status.get("admittedWorkloads", 0),
            "reserving": status.get("reservingWorkloads", 0),
        }

    sorted_pairs = sorted(all_queue_pairs)
    sorted_namespaces = sorted(all_namespaces)

    # Fetch workloads with per-job queue state
    workloads_map = get_workloads_by_localqueue(all_namespaces)

    # Build row data with workload details
    result_rows = []
    for ns in sorted_namespaces:
        queue_data = {}
        for cq, lq in sorted_pairs:
            data = workload_data.get((ns, cq, lq), {})
            queue_data[(cq, lq)] = {
                "pending": int(data.get("pending", 0)),
                "admitted": int(data.get("admitted", 0)),
                "reserving": int(data.get("reserving", 0)),
                "workloads": workloads_map.get((ns, lq), []),
            }
        result_rows.append({"namespace": ns, "queues": queue_data})

    return sorted_pairs, result_rows


WORKLOAD_COLORS = {
    "P": "#aed6f1",  # pastel blue
    "A": "#abebc6",  # pastel green
    "R": "#f5b7b1",  # pastel red
    "F": "#d3d3d3",  # light grey
}


def render_workload_cell(counts: dict) -> str:
    """Render per-job state badges with job name and priority class."""
    workloads = counts.get("workloads", [])
    if not workloads:
        return ""
    lines = []
    for name, pc, state, gpu_count in workloads:
        color = WORKLOAD_COLORS.get(state, "#ddd")
        badge = (
            f'<span style="background-color:{color};padding:2px 6px;'
            f"margin-right:4px;border-radius:3px;font-weight:bold;"
            f'font-size:0.85em;display:inline-block">{state}</span>'
        )
        label = f"{name} ({pc})" if pc else name
        gpu_str = f" [{gpu_count} GPU]" if gpu_count else ""
        lines.append(
            f'<div style="margin:2px 0;font-size:0.8em">'
            f"{badge}"
            f'<span style="color:#555">{label}{gpu_str}</span></div>'
        )
    return "".join(lines)


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
        flavors = get_cluster_queue_flavors(cq)
        flavor_html = ""
        if flavors:
            parts = []
            for f in flavors:
                gpu_quota = f["quotas"].get("nvidia.com/gpu")
                if gpu_quota is not None:
                    parts.append(f'{f["name"]} ({gpu_quota} GPU)')
                else:
                    parts.append(f["name"])
            flavor_html = (
                '<br><span style="font-size:0.75em;font-weight:normal;color:#555">'
                + ", ".join(parts)
                + "</span>"
            )
        html.append(
            f'<th colspan="{len(lqs)}" style="border:1px solid #ddd;padding:8px;'
            f'background:#e8e8e8;text-align:center">{cq}{flavor_html}</th>'
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

        html.append("<tr>")
        html.append(
            f'<td style="border:1px solid #ddd;padding:8px">{ns}</td>'
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
st.subheader("Workflow activity: Pending/Admitted/Finished")

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
    except Exception as e:
        st.error(f"Error fetching localqueue events: {e}")


namespace_table()
