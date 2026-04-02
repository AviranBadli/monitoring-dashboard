from unittest.mock import MagicMock

from tests.conftest import mock_core_api, mock_k8s_api

from pages.live import (
    get_cluster_queue_flavors,
    get_gpu_nodes,
    get_localqueue_events,
    get_workloads_by_localqueue,
    render_gpu_nodes_table,
    render_html_table,
    render_workload_cell,
)


class TestRenderWorkloadCell:
    def test_empty_workloads(self):
        assert render_workload_cell([]) == ""

    def test_single_admitted_workload(self):
        workloads = [("my-job", "high-priority", "A", 4)]
        html = render_workload_cell(workloads)
        assert "my-job" in html
        assert "high-priority" in html
        assert "[4 GPU]" in html
        assert ">A<" in html
        assert "#abebc6" in html  # green for admitted

    def test_pending_workload(self):
        workloads = [("pending-job", "", "P", 2)]
        html = render_workload_cell(workloads)
        assert "pending-job" in html
        assert ">P<" in html
        assert "#aed6f1" in html  # blue for pending
        assert "[2 GPU]" in html

    def test_finished_workload(self):
        workloads = [("done-job", "", "F", 1)]
        html = render_workload_cell(workloads)
        assert ">F<" in html
        assert "#d3d3d3" in html  # grey for finished

    def test_reserving_workload(self):
        workloads = [("reserving-job", "", "R", 1)]
        html = render_workload_cell(workloads)
        assert ">R<" in html
        assert "#ddd" in html  # fallback color for reserving

    def test_no_priority_class(self):
        workloads = [("my-job", "", "A", 2)]
        html = render_workload_cell(workloads)
        assert "my-job" in html
        assert "()" not in html

    def test_zero_gpu_no_gpu_label(self):
        workloads = [("my-job", "", "A", 0)]
        html = render_workload_cell(workloads)
        assert "GPU" not in html

    def test_multiple_workloads(self):
        workloads = [
            ("job-1", "high", "A", 4),
            ("job-2", "low", "P", 2),
        ]
        html = render_workload_cell(workloads)
        assert "job-1" in html
        assert "job-2" in html
        assert ">A<" in html
        assert ">P<" in html


class TestRenderGpuNodesTable:
    def test_single_node(self):
        nodes = [{"name": "gpu-node-1", "gpu_count": 8, "gpu_type": "A100"}]
        html = render_gpu_nodes_table(nodes)
        assert "gpu-node-1" in html
        assert "8" in html
        assert "A100" in html
        assert "<table" in html

    def test_multiple_nodes(self):
        nodes = [
            {"name": "node-1", "gpu_count": 4, "gpu_type": "A100"},
            {"name": "node-2", "gpu_count": 2, "gpu_type": "T4"},
        ]
        html = render_gpu_nodes_table(nodes)
        assert "node-1" in html
        assert "node-2" in html
        assert "A100" in html
        assert "T4" in html


class TestRenderHtmlTable:
    def test_single_row(self):
        cluster_queues = ["cq-1"]
        rows = [
            {
                "namespace": "ns-1",
                "localqueue": "lq-1",
                "cluster_queue": "cq-1",
                "workloads": [("job-1", "", "A", 2)],
            }
        ]
        html = render_html_table(cluster_queues, rows)
        assert "ns-1" in html
        assert "lq-1" in html
        assert "cq-1" in html
        assert "job-1" in html

    def test_workload_in_correct_column(self):
        cluster_queues = ["cq-1", "cq-2"]
        rows = [
            {
                "namespace": "ns-1",
                "localqueue": "lq-1",
                "cluster_queue": "cq-2",
                "workloads": [("job-1", "", "A", 1)],
            }
        ]
        html = render_html_table(cluster_queues, rows)
        assert "job-1" in html

    def test_namespace_rowspan_merge(self):
        cluster_queues = ["cq-1"]
        rows = [
            {
                "namespace": "ns-1",
                "localqueue": "lq-1",
                "cluster_queue": "cq-1",
                "workloads": [],
            },
            {
                "namespace": "ns-1",
                "localqueue": "lq-2",
                "cluster_queue": "cq-1",
                "workloads": [],
            },
        ]
        html = render_html_table(cluster_queues, rows)
        assert 'rowspan="2"' in html
        # Namespace should only appear once as a td
        assert html.count("ns-1") == 1

    def test_different_namespaces_no_merge(self):
        cluster_queues = ["cq-1"]
        rows = [
            {
                "namespace": "ns-1",
                "localqueue": "lq-1",
                "cluster_queue": "cq-1",
                "workloads": [],
            },
            {
                "namespace": "ns-2",
                "localqueue": "lq-2",
                "cluster_queue": "cq-1",
                "workloads": [],
            },
        ]
        html = render_html_table(cluster_queues, rows)
        # Namespace cells in tbody should not be merged when namespaces differ
        tbody = html.split("<tbody>")[1]
        assert "rowspan" not in tbody
        assert "ns-1" in html
        assert "ns-2" in html


class TestGetGpuNodes:
    def test_returns_gpu_nodes(self):
        node = MagicMock()
        node.metadata.name = "gpu-node-1"
        node.metadata.labels = {"nvidia.com/gpu.product": "A100"}
        node.status.capacity = {"nvidia.com/gpu": "8", "cpu": "64"}
        mock_core_api.list_node.return_value = MagicMock(items=[node])

        result = get_gpu_nodes()
        assert len(result) == 1
        assert result[0] == {
            "name": "gpu-node-1",
            "gpu_count": 8,
            "gpu_type": "A100",
            "mig_resources": {},
            "gpu_utilization": [],
        }

    def test_skips_non_gpu_nodes(self):
        node = MagicMock()
        node.metadata.name = "cpu-node"
        node.metadata.labels = {}
        node.status.capacity = {"cpu": "64"}
        mock_core_api.list_node.return_value = MagicMock(items=[node])

        result = get_gpu_nodes()
        assert len(result) == 0

    def test_missing_gpu_label(self):
        node = MagicMock()
        node.metadata.name = "gpu-node"
        node.metadata.labels = {}
        node.status.capacity = {"nvidia.com/gpu": "4"}
        mock_core_api.list_node.return_value = MagicMock(items=[node])

        result = get_gpu_nodes()
        assert result[0]["gpu_type"] == "unknown"


class TestGetClusterQueueFlavors:
    def test_extracts_flavors_with_quotas(self):
        mock_k8s_api.get_cluster_custom_object.return_value = {
            "spec": {
                "resourceGroups": [
                    {
                        "flavors": [
                            {
                                "name": "gpu-flavor",
                                "resources": [
                                    {"name": "nvidia.com/gpu", "nominalQuota": 8},
                                    {"name": "cpu", "nominalQuota": 32},
                                ],
                            }
                        ]
                    }
                ]
            }
        }
        result = get_cluster_queue_flavors("test-cq")
        assert len(result) == 1
        assert result[0]["name"] == "gpu-flavor"
        assert result[0]["quotas"]["nvidia.com/gpu"] == 8
        assert result[0]["quotas"]["cpu"] == 32

    def test_deduplicates_flavors(self):
        mock_k8s_api.get_cluster_custom_object.return_value = {
            "spec": {
                "resourceGroups": [
                    {"flavors": [{"name": "flavor-a", "resources": []}]},
                    {"flavors": [{"name": "flavor-a", "resources": []}]},
                ]
            }
        }
        result = get_cluster_queue_flavors("test-cq")
        assert len(result) == 1

    def test_returns_empty_on_exception(self):
        mock_k8s_api.get_cluster_custom_object.side_effect = Exception("not found")
        result = get_cluster_queue_flavors("missing-cq")
        assert result == []
        mock_k8s_api.get_cluster_custom_object.side_effect = None


class TestGetWorkloadsByLocalqueue:
    def test_extracts_workload_state_and_gpu(self):
        mock_k8s_api.list_namespaced_custom_object.return_value = {
            "items": [
                {
                    "metadata": {
                        "name": "wl-1",
                        "ownerReferences": [{"kind": "Job", "name": "my-job"}],
                    },
                    "spec": {
                        "queueName": "lq-1",
                        "priorityClassName": "high",
                        "podSets": [
                            {
                                "template": {
                                    "spec": {
                                        "containers": [
                                            {"resources": {"requests": {"nvidia.com/gpu": "4"}}}
                                        ]
                                    }
                                }
                            }
                        ],
                    },
                    "status": {
                        "conditions": [
                            {"type": "Admitted", "status": "True"},
                        ]
                    },
                }
            ]
        }
        result = get_workloads_by_localqueue({"ns-1"})
        assert ("ns-1", "lq-1") in result
        job_name, pc, state, gpu = result[("ns-1", "lq-1")][0]
        assert job_name == "my-job"
        assert pc == "high"
        assert state == "A"
        assert gpu == 4

    def test_pending_state(self):
        mock_k8s_api.list_namespaced_custom_object.return_value = {
            "items": [
                {
                    "metadata": {"name": "wl-1", "ownerReferences": []},
                    "spec": {
                        "queueName": "lq-1",
                        "priorityClassName": "",
                        "podSets": [],
                    },
                    "status": {"conditions": []},
                }
            ]
        }
        result = get_workloads_by_localqueue({"ns-1"})
        _, _, state, _ = result[("ns-1", "lq-1")][0]
        assert state == "P"

    def test_finished_state_takes_priority(self):
        mock_k8s_api.list_namespaced_custom_object.return_value = {
            "items": [
                {
                    "metadata": {"name": "wl-1", "ownerReferences": []},
                    "spec": {
                        "queueName": "lq-1",
                        "priorityClassName": "",
                        "podSets": [],
                    },
                    "status": {
                        "conditions": [
                            {"type": "Admitted", "status": "True"},
                            {"type": "Finished", "status": "True"},
                        ]
                    },
                }
            ]
        }
        result = get_workloads_by_localqueue({"ns-1"})
        _, _, state, _ = result[("ns-1", "lq-1")][0]
        assert state == "F"

    def test_reserving_state(self):
        mock_k8s_api.list_namespaced_custom_object.return_value = {
            "items": [
                {
                    "metadata": {"name": "wl-1", "ownerReferences": []},
                    "spec": {
                        "queueName": "lq-1",
                        "priorityClassName": "",
                        "podSets": [],
                    },
                    "status": {
                        "conditions": [
                            {"type": "QuotaReserved", "status": "True"},
                        ]
                    },
                }
            ]
        }
        result = get_workloads_by_localqueue({"ns-1"})
        _, _, state, _ = result[("ns-1", "lq-1")][0]
        assert state == "R"

    def test_skips_workloads_without_queue(self):
        mock_k8s_api.list_namespaced_custom_object.return_value = {
            "items": [
                {
                    "metadata": {"name": "wl-1", "ownerReferences": []},
                    "spec": {"queueName": "", "podSets": []},
                    "status": {"conditions": []},
                }
            ]
        }
        result = get_workloads_by_localqueue({"ns-1"})
        assert len(result) == 0

    def test_continues_on_namespace_error(self):
        mock_k8s_api.list_namespaced_custom_object.side_effect = Exception("forbidden")
        result = get_workloads_by_localqueue({"ns-1", "ns-2"})
        assert result == {}
        mock_k8s_api.list_namespaced_custom_object.side_effect = None


class TestGetLocalqueueEvents:
    def test_returns_sorted_rows(self):
        mock_k8s_api.list_cluster_custom_object.return_value = {
            "items": [
                {
                    "metadata": {"namespace": "ns-b", "name": "lq-1"},
                    "spec": {"clusterQueue": "cq-1"},
                },
                {
                    "metadata": {"namespace": "ns-a", "name": "lq-2"},
                    "spec": {"clusterQueue": "cq-1"},
                },
            ]
        }
        mock_k8s_api.list_namespaced_custom_object.return_value = {"items": []}

        cqs, rows = get_localqueue_events()
        assert cqs == ["cq-1"]
        assert len(rows) == 2
        assert rows[0]["namespace"] == "ns-a"
        assert rows[1]["namespace"] == "ns-b"

    def test_multiple_cluster_queues(self):
        mock_k8s_api.list_cluster_custom_object.return_value = {
            "items": [
                {
                    "metadata": {"namespace": "ns-1", "name": "lq-1"},
                    "spec": {"clusterQueue": "cq-b"},
                },
                {
                    "metadata": {"namespace": "ns-1", "name": "lq-2"},
                    "spec": {"clusterQueue": "cq-a"},
                },
            ]
        }
        mock_k8s_api.list_namespaced_custom_object.return_value = {"items": []}

        cqs, rows = get_localqueue_events()
        assert cqs == ["cq-a", "cq-b"]

    def test_empty_cluster(self):
        mock_k8s_api.list_cluster_custom_object.return_value = {"items": []}

        cqs, rows = get_localqueue_events()
        assert cqs == []
        assert rows == []
