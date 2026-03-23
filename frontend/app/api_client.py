import httpx


class APIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class APIClient:
    def __init__(self, base_url: str):
        self.client = httpx.Client(base_url=base_url, timeout=30.0)

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            resp = self.client.request(method, path, **kwargs)
        except httpx.ConnectError:
            raise APIError(0, "Cannot connect to backend. Is it running?")
        except httpx.TimeoutException:
            raise APIError(0, "Backend request timed out.")
        if resp.status_code >= 400:
            detail = resp.text
            try:
                detail = resp.json().get("detail", detail)
            except Exception:
                pass
            raise APIError(resp.status_code, str(detail))
        return resp

    def _get(self, path: str, **params) -> list | dict:
        filtered = {k: v for k, v in params.items() if v is not None}
        resp = self._request("GET", path, params=filtered)
        if not resp.content:
            return []
        return resp.json()

    def _post(self, path: str, params: dict | None = None, json: dict | None = None) -> dict:
        filtered_params = {k: v for k, v in (params or {}).items() if v is not None}
        return self._request("POST", path, params=filtered_params, json=json).json()

    def _patch(self, path: str, json: dict) -> dict:
        return self._request("PATCH", path, json=json).json()

    def _delete(self, path: str) -> None:
        self._request("DELETE", path)

    # --- Health ---

    def health(self) -> dict:
        return self._request("GET", "/health").json()

    # --- Allocations ---

    def list_allocations(
        self,
        team_name: str | None = None,
        node_name: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list:
        return self._get(
            "/allocations",
            team_name=team_name,
            node_name=node_name,
            start_time=start_time,
            end_time=end_time,
        )

    def create_allocation(self, data: dict) -> dict:
        return self._post("/allocations", json=data)

    def get_allocation(self, allocation_id: int) -> dict:
        return self._get(f"/allocations/{allocation_id}")

    def update_allocation(self, allocation_id: int, data: dict) -> dict:
        return self._patch(f"/allocations/{allocation_id}", json=data)

    def delete_allocation(self, allocation_id: int) -> None:
        self._delete(f"/allocations/{allocation_id}")

    # --- Costs ---

    def get_node_costs(
        self,
        node_name: str,
        start: str | None = None,
        end: str | None = None,
    ) -> list:
        return self._get(f"/costs/node/{node_name}", start=start, end=end)

    # --- Inventory ---

    def list_clusters(self) -> list:
        return self._get("/inventory/clusters")

    def get_cluster(self, name: str) -> dict:
        return self._get(f"/inventory/clusters/{name}")

    def list_nodes(
        self,
        cluster_name: str | None = None,
        team_name: str | None = None,
    ) -> list:
        return self._get("/inventory/nodes", cluster_name=cluster_name, team_name=team_name)

    def get_node(self, name: str) -> dict:
        return self._get(f"/inventory/nodes/{name}")

    def list_gpus(
        self,
        cluster_name: str | None = None,
        node_name: str | None = None,
        gpu_type: str | None = None,
    ) -> list:
        return self._get(
            "/inventory/gpus",
            cluster_name=cluster_name,
            node_name=node_name,
            gpu_type=gpu_type,
        )

    # --- Resources: Clouds ---

    def list_clouds(self) -> list:
        return self._get("/resources/clouds")

    def create_cloud(self, name: str) -> dict:
        return self._post("/resources/clouds", json={"name": name})

    def delete_cloud(self, name: str) -> None:
        self._delete(f"/resources/clouds/{name}")

    # --- Resources: Teams ---

    def list_teams(self) -> list:
        return self._get("/resources/teams")

    def create_team(self, name: str) -> dict:
        return self._post("/resources/teams", json={"name": name})

    def delete_team(self, name: str) -> None:
        self._delete(f"/resources/teams/{name}")

    # --- Resources: GPU Types ---

    def list_gpu_types(self) -> list:
        return self._get("/resources/gpu-types")

    def create_gpu_type(
        self,
        name: str,
        display_name: str,
        family: str,
        memory_gb: int = 0,
        variant: str | None = None,
    ) -> dict:
        return self._post(
            "/resources/gpu-types",
            params={
                "name": name,
                "display_name": display_name,
                "family": family,
                "memory_gb": memory_gb,
                "variant": variant,
            },
        )

    def delete_gpu_type(self, name: str) -> None:
        self._delete(f"/resources/gpu-types/{name}")

    # --- Resources: Workload Types ---

    def list_workload_types(self) -> list:
        return self._get("/resources/workload-types")

    def create_workload_type(self, name: str) -> dict:
        return self._post("/resources/workload-types", params={"name": name})

    def delete_workload_type(self, name: str) -> None:
        self._delete(f"/resources/workload-types/{name}")

    # --- Resources: Allocation Types ---

    def list_allocation_types(self) -> list:
        return self._get("/resources/allocation-types")

    def create_allocation_type(self, name: str, priority: int) -> dict:
        return self._post(
            "/resources/allocation-types",
            params={"name": name, "priority": priority},
        )

    def delete_allocation_type(self, name: str) -> None:
        self._delete(f"/resources/allocation-types/{name}")

    # --- Resources: Instance Types ---

    def list_instance_types(self) -> list:
        return self._get("/resources/instance-types")

    def create_instance_type(
        self,
        name: str,
        cloud_name: str,
        gpu_type_name: str,
        gpu_count: float,
        instance_family: str,
    ) -> dict:
        return self._post(
            "/resources/instance-types",
            params={
                "name": name,
                "cloud_name": cloud_name,
                "gpu_type_name": gpu_type_name,
                "gpu_count": gpu_count,
                "instance_family": instance_family,
            },
        )

    def delete_instance_type(self, name: str) -> None:
        self._delete(f"/resources/instance-types/{name}")
