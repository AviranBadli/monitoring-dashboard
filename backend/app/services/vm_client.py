"""Victoria Metrics client for querying DCGM metrics"""

import httpx
from typing import Dict, Any, List
from datetime import datetime

from app.core.config import settings


class VictoriaMetricsClient:
    """Client for querying Victoria Metrics"""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.VICTORIA_METRICS_URL
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def query(self, query: str, time: datetime | None = None) -> Dict[str, Any]:
        """
        Execute an instant query against Victoria Metrics

        Args:
            query: MetricsQL query string
            time: Optional timestamp for the query (defaults to now)

        Returns:
            Query result as dictionary
        """
        params = {"query": query}
        if time:
            params["time"] = int(time.timestamp())

        response = await self.client.get("/api/v1/query", params=params)
        response.raise_for_status()
        return response.json()

    async def query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "5m",
    ) -> Dict[str, Any]:
        """
        Execute a range query against Victoria Metrics

        Args:
            query: MetricsQL query string
            start: Start time
            end: End time
            step: Query resolution (e.g., "5m", "1h")

        Returns:
            Query result as dictionary with time series data
        """
        params = {
            "query": query,
            "start": int(start.timestamp()),
            "end": int(end.timestamp()),
            "step": step,
        }

        response = await self.client.get("/api/v1/query_range", params=params)
        response.raise_for_status()
        return response.json()

    async def get_gpu_utilization(
        self,
        gpu_uuid: str,
        start: datetime,
        end: datetime,
        step: str = "5m",
    ) -> List[Dict[str, Any]]:
        """
        Get GPU utilization for a specific GPU

        Args:
            gpu_uuid: GPU UUID
            start: Start time
            end: End time
            step: Query resolution

        Returns:
            List of time series data points
        """
        query = f'DCGM_FI_DEV_GPU_UTIL{{UUID="{gpu_uuid}"}}'
        result = await self.query_range(query, start, end, step)
        return result.get("data", {}).get("result", [])

    async def get_cluster_utilization(
        self,
        cluster_name: str,
        start: datetime,
        end: datetime,
        step: str = "5m",
    ) -> List[Dict[str, Any]]:
        """
        Get GPU utilization for all GPUs in a cluster

        Args:
            cluster_name: Cluster name
            start: Start time
            end: End time
            step: Query resolution

        Returns:
            List of time series data points
        """
        query = f'DCGM_FI_DEV_GPU_UTIL{{gpu_cluster="{cluster_name}"}}'
        result = await self.query_range(query, start, end, step)
        return result.get("data", {}).get("result", [])

    async def get_available_gpus(self, cluster_name: str | None = None) -> List[str]:
        """
        Get list of GPU UUIDs currently reporting metrics

        Args:
            cluster_name: Optional cluster filter

        Returns:
            List of GPU UUIDs
        """
        query = "group by (UUID) (DCGM_FI_DEV_GPU_UTIL)"
        if cluster_name:
            query = f'group by (UUID) (DCGM_FI_DEV_GPU_UTIL{{gpu_cluster="{cluster_name}"}})'

        result = await self.query(query)
        # Extract UUIDs from result
        return [series["metric"]["UUID"] for series in result.get("data", {}).get("result", [])]

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Dependency for FastAPI
async def get_vm_client() -> VictoriaMetricsClient:
    """Dependency to get Victoria Metrics client"""
    client = VictoriaMetricsClient()
    try:
        yield client
    finally:
        await client.close()
