"""Metrics endpoints (queries to Victoria Metrics)"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/usage/gpu/{uuid}")
def get_gpu_usage(
    uuid: str,
    start: datetime,
    end: datetime,
    step: str = "5m",
):
    """
    Get GPU utilization metrics from Victoria Metrics.

    Query DCGM_FI_DEV_GPU_UTIL for a specific GPU over a time range.

    TODO: Implement Victoria Metrics client
    """
    return {
        "message": "Victoria Metrics integration not yet implemented",
        "query": f'DCGM_FI_DEV_GPU_UTIL{{UUID="{uuid}"}}',
        "start": start,
        "end": end,
        "step": step,
    }


@router.get("/usage/cluster/{cluster_name}")
def get_cluster_usage(
    cluster_name: str,
    start: datetime,
    end: datetime,
    step: str = "5m",
):
    """
    Get GPU utilization metrics for all GPUs in a cluster.

    TODO: Implement Victoria Metrics client
    """
    return {
        "message": "Victoria Metrics integration not yet implemented",
        "query": f'DCGM_FI_DEV_GPU_UTIL{{gpu_cluster="{cluster_name}"}}',
        "start": start,
        "end": end,
        "step": step,
    }


@router.get("/usage/node/{node_name}")
def get_node_usage(
    node_name: str,
    start: datetime,
    end: datetime,
    step: str = "5m",
):
    """
    Get GPU utilization metrics for all GPUs in a node.

    TODO: Implement Victoria Metrics client
    """
    return {
        "message": "Victoria Metrics integration not yet implemented",
        "query": f'DCGM_FI_DEV_GPU_UTIL{{Hostname="{node_name}"}}',
        "start": start,
        "end": end,
        "step": step,
    }
