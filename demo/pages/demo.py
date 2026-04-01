import streamlit as st

from config import core_api, k8s_api, settings


def get_gpu_nodes() -> list[dict]:
    """Fetch nodes that have nvidia.com/gpu or nvidia.com/mig-* resources."""
    nodes = core_api.list_node()
    gpu_nodes = []
    for node in nodes.items:
        capacity = node.status.capacity or {}
        gpu_count = int(capacity.get("nvidia.com/gpu", 0))
        mig_resources = {
            k: int(v) for k, v in capacity.items() if k.startswith("nvidia.com/mig-") and int(v) > 0
        }
        if gpu_count > 0 or mig_resources:
            labels = node.metadata.labels or {}
            gpu_type = labels.get("nvidia.com/gpu.product", "unknown")
            gpu_nodes.append(
                {
                    "name": node.metadata.name,
                    "gpu_count": gpu_count,
                    "gpu_type": gpu_type,
                    "mig_resources": mig_resources,
                }
            )
    return gpu_nodes


def render_gpu_nodes_table(gpu_nodes: list[dict]) -> str:
    """Build an HTML table showing GPU nodes."""
    html = [
        '<table style="width:100%;border-collapse:collapse;font-family:sans-serif;font-size:0.9em">',
        "<thead><tr>",
        '<th style="border:1px solid #ddd;padding:8px;background:#f8f8f8;text-align:left">Node</th>',
        '<th style="border:1px solid #ddd;padding:8px;background:#f8f8f8;text-align:center">GPUs</th>',
        '<th style="border:1px solid #ddd;padding:8px;background:#f8f8f8;text-align:left">GPU Type</th>',
        '<th style="border:1px solid #ddd;padding:8px;background:#f8f8f8;text-align:left">MIG Instances</th>',
        "</tr></thead><tbody>",
    ]
    for node in gpu_nodes:
        mig = node.get("mig_resources", {})
        if mig:
            mig_parts = [f"{k.removeprefix('nvidia.com/')}: {v}" for k, v in sorted(mig.items())]
            mig_html = "<br>".join(mig_parts)
        else:
            mig_html = ""
        html.append(
            f"<tr>"
            f'<td style="border:1px solid #ddd;padding:8px">{node["name"]}</td>'
            f'<td style="border:1px solid #ddd;padding:8px;text-align:center">{node["gpu_count"]}</td>'
            f'<td style="border:1px solid #ddd;padding:8px">{node["gpu_type"]}</td>'
            f'<td style="border:1px solid #ddd;padding:8px;font-size:0.85em">{mig_html}</td>'
            f"</tr>"
        )
    html.append("</tbody></table>")
    return "\n".join(html)


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
                    c["type"]: c["status"] for c in wl.get("status", {}).get("conditions", [])
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
        except Exception as e:
            st.warning(f"Failed to fetch workloads in namespace '{ns}': {e}")
            continue
    return workloads_map


def get_localqueue_events():
    """Fetch LocalQueue status from the Kubernetes API."""
    lq_list = k8s_api.list_cluster_custom_object(
        group="kueue.x-k8s.io",
        version="v1beta1",
        plural="localqueues",
    )

    # Collect all localqueue entries
    all_namespaces = set()
    all_cluster_queues = set()
    lq_entries = []
    for item in lq_list.get("items", []):
        ns = item.get("metadata", {}).get("namespace", "unknown")
        lq = item.get("metadata", {}).get("name", "unknown")
        cq = item.get("spec", {}).get("clusterQueue", "unknown")
        all_namespaces.add(ns)
        all_cluster_queues.add(cq)
        lq_entries.append(
            {
                "namespace": ns,
                "localqueue": lq,
                "cluster_queue": cq,
            }
        )

    # Fetch workloads with per-job queue state
    workloads_map = get_workloads_by_localqueue(all_namespaces)

    # Build one row per localqueue with workloads
    result_rows = []
    for entry in sorted(lq_entries, key=lambda e: (e["namespace"], e["localqueue"])):
        ns = entry["namespace"]
        lq = entry["localqueue"]
        entry["workloads"] = workloads_map.get((ns, lq), [])
        result_rows.append(entry)

    # Test rows — add a dummy namespace with 2 local queues
    if settings.TEST_ROW and all_cluster_queues:
        test_cq = sorted(all_cluster_queues)[0]
        result_rows.append(
            {
                "namespace": "test-namespace",
                "localqueue": "test-lq-training",
                "cluster_queue": test_cq,
                "workloads": [
                    ("test-train-job-1", "high-priority", "A", 4),
                    ("test-train-job-2", "low-priority", "P", 2),
                ],
            }
        )
        result_rows.append(
            {
                "namespace": "test-namespace",
                "localqueue": "test-lq-inference",
                "cluster_queue": test_cq,
                "workloads": [
                    ("test-infer-job-1", "high-priority", "A", 1),
                    ("test-infer-job-2", "", "F", 1),
                ],
            }
        )

    return sorted(all_cluster_queues), result_rows


WORKLOAD_COLORS = {
    "P": "#aed6f1",  # pastel blue
    "A": "#abebc6",  # pastel green
    "F": "#d3d3d3",  # light grey
}


def render_workload_cell(workloads: list) -> str:
    """Render per-job state badges with job name and priority class."""
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


def render_html_table(cluster_queues, rows):
    """Build an HTML table with one row per localqueue and one column per cluster queue."""
    html = []
    html.append(
        '<table style="width:100%;border-collapse:collapse;font-family:sans-serif;font-size:0.9em">'
    )

    # Header row
    html.append("<thead><tr>")
    html.append('<th style="border:1px solid #ddd;padding:8px;background:#f8f8f8">Namespace</th>')
    html.append('<th style="border:1px solid #ddd;padding:8px;background:#f8f8f8">LocalQueue</th>')
    for cq in cluster_queues:
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
            f'<th style="border:1px solid #ddd;padding:8px;'
            f'background:#e8e8e8;text-align:center">{cq}{flavor_html}</th>'
        )
    html.append("</tr></thead>")

    # Count rows per namespace for rowspan
    ns_counts = {}
    for row in rows:
        ns_counts[row["namespace"]] = ns_counts.get(row["namespace"], 0) + 1

    # Data rows — one per localqueue, with merged namespace cells
    html.append("<tbody>")
    ns_seen = set()
    for row in rows:
        ns = row["namespace"]
        html.append("<tr>")
        if ns not in ns_seen:
            ns_seen.add(ns)
            count = ns_counts[ns]
            rowspan = f' rowspan="{count}"' if count > 1 else ""
            html.append(
                f'<td{rowspan} style="border:1px solid #ddd;padding:8px;'
                f'vertical-align:top">{ns}</td>'
            )
        html.append(f'<td style="border:1px solid #ddd;padding:8px">{row["localqueue"]}</td>')
        for cq in cluster_queues:
            if row["cluster_queue"] == cq:
                cell_html = render_workload_cell(row.get("workloads", []))
            else:
                cell_html = ""
            html.append(
                f'<td style="border:1px solid #ddd;padding:6px;text-align:center">{cell_html}</td>'
            )
        html.append("</tr>")
    html.append("</tbody></table>")

    return "\n".join(html)


st.title("Kueue Activity Live View Dashboard")
st.text("Activity of the Kueue scheduler across the cluster in real time.")

st.subheader("Cluster Nodes")

try:
    gpu_nodes = get_gpu_nodes()
    if gpu_nodes:
        st.markdown(render_gpu_nodes_table(gpu_nodes), unsafe_allow_html=True)
    else:
        st.info("No GPU nodes found.")
except Exception as e:
    st.error(f"Error fetching GPU nodes: {e}")

st.markdown(
    f"<h3>Workload activity: "
    f'<span style="background-color:{WORKLOAD_COLORS["P"]};padding:2px 6px;border-radius:3px">Pending</span>/'
    f'<span style="background-color:{WORKLOAD_COLORS["A"]};padding:2px 6px;border-radius:3px">Admitted</span>/'
    f'<span style="background-color:{WORKLOAD_COLORS["F"]};padding:2px 6px;border-radius:3px">Finished</span>'
    f"</h3>",
    unsafe_allow_html=True,
)

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
        cluster_queues, rows = get_localqueue_events()
        if not rows:
            st.info("No localqueue events found.")
        else:
            table_html = render_html_table(cluster_queues, rows)
            st.markdown(table_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error fetching localqueue events: {e}")


namespace_table()
