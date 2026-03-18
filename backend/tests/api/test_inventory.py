"""Tests for GPU inventory endpoints"""

import uuid
from datetime import datetime, timedelta, UTC

import pytest

from app.models import Cloud, Team, GpuType, GPUCluster, GPUNode, GPU, Owner


@pytest.fixture
def sample_data(db):
    """Create sample data for testing"""
    # Create cloud
    cloud = Cloud(name="AWS")
    db.add(cloud)

    # Create team
    team = Team(name="AI Research")
    db.add(team)

    # Create GPU type
    gpu_type = GpuType(
        name="nvidia-a100-40gb-sxm4",
        display_name="NVIDIA A100 40GB SXM4",
        family="NVIDIA A100",
        memory_gb=40,
        variant="SXM4",
    )
    db.add(gpu_type)

    # Create owner
    owner = Owner(name="Alice Chen", email="alice@example.com", team_name="AI Research")
    db.add(owner)
    db.flush()

    # Create cluster
    cluster = GPUCluster(name="prod-us-east-1", cloud_name="AWS", owner_id=owner.id)
    db.add(cluster)

    # Create node
    node = GPUNode(
        name="node-001",
        cluster_name="prod-us-east-1",
        instance_type_name="p4d.24xlarge",
        team_name="AI Research",
    )
    db.add(node)
    db.flush()

    # Create GPUs
    gpu1 = GPU(
        uuid=str(uuid.uuid4()),
        gpu_number=0,
        gpu_cluster="prod-us-east-1",
        node_name="node-001",
        gpu_type_name="nvidia-a100-40gb-sxm4",
        first_discovered=datetime.now(UTC),
        last_seen=datetime.now(UTC),
    )
    gpu2 = GPU(
        uuid=str(uuid.uuid4()),
        gpu_number=1,
        gpu_cluster="prod-us-east-1",
        node_name="node-001",
        gpu_type_name="nvidia-a100-40gb-sxm4",
        first_discovered=datetime.now(UTC),
        last_seen=datetime.now(UTC),
    )
    db.add_all([gpu1, gpu2])
    db.commit()

    return {
        "cloud": cloud,
        "team": team,
        "gpu_type": gpu_type,
        "owner": owner,
        "cluster": cluster,
        "node": node,
        "gpus": [gpu1, gpu2],
    }


class TestGPUEndpoints:
    """Test GPU-related endpoints"""

    def test_list_gpus(self, client, sample_data):
        """Test listing all GPUs"""
        response = client.get("/api/v1/inventory/gpus")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("uuid" in gpu for gpu in data)
        assert all("gpu_number" in gpu for gpu in data)

    def test_list_gpus_filter_by_cluster(self, client, sample_data):
        """Test filtering GPUs by cluster"""
        response = client.get("/api/v1/inventory/gpus?cluster_name=prod-us-east-1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(gpu["gpu_cluster"] == "prod-us-east-1" for gpu in data)

    def test_list_gpus_filter_by_node(self, client, sample_data):
        """Test filtering GPUs by node"""
        response = client.get("/api/v1/inventory/gpus?node_name=node-001")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(gpu["node_name"] == "node-001" for gpu in data)

    def test_list_gpus_filter_by_type(self, client, sample_data):
        """Test filtering GPUs by type"""
        response = client.get("/api/v1/inventory/gpus?gpu_type=nvidia-a100-40gb-sxm4")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(gpu["gpu_type_name"] == "nvidia-a100-40gb-sxm4" for gpu in data)

    def test_get_gpu_by_uuid(self, client, sample_data):
        """Test getting a specific GPU by UUID"""
        gpu_uuid = sample_data["gpus"][0].uuid
        response = client.get(f"/api/v1/inventory/gpus/{gpu_uuid}")
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == gpu_uuid
        assert data["gpu_number"] == 0
        assert data["gpu_cluster"] == "prod-us-east-1"

    def test_get_gpu_not_found(self, client, sample_data):
        """Test getting a non-existent GPU returns 404"""
        fake_uuid = str(uuid.uuid4())
        response = client.get(f"/api/v1/inventory/gpus/{fake_uuid}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_gpu_has_relationships(self, client, sample_data):
        """Test that GPU includes relationship data"""
        gpu_uuid = sample_data["gpus"][0].uuid
        response = client.get(f"/api/v1/inventory/gpus/{gpu_uuid}")
        assert response.status_code == 200
        data = response.json()
        assert data["node_name"] == "node-001"
        assert data["gpu_type_name"] == "nvidia-a100-40gb-sxm4"

    def test_list_gpus_empty(self, client, db):
        """Test listing GPUs when none exist"""
        response = client.get("/api/v1/inventory/gpus")
        assert response.status_code == 200
        assert response.json() == []


class TestGPUModel:
    """Test GPU model validation"""

    def test_create_gpu_with_valid_uuid(self, db, sample_data):
        """Test creating GPU with valid UUID"""
        valid_uuid = str(uuid.uuid4())
        gpu = GPU(
            uuid=valid_uuid,
            gpu_number=2,
            gpu_cluster="prod-us-east-1",
            node_name="node-001",
            gpu_type_name="nvidia-a100-40gb-sxm4",
            first_discovered=datetime.now(UTC),
            last_seen=datetime.now(UTC),
        )
        db.add(gpu)
        db.commit()

        # Verify it was saved
        saved_gpu = db.query(GPU).filter(GPU.uuid == valid_uuid).first()
        assert saved_gpu is not None
        assert saved_gpu.uuid == valid_uuid.lower()  # Should be normalized to lowercase

    def test_create_gpu_with_uppercase_uuid(self, db, sample_data):
        """Test that UUID is converted to lowercase"""
        uppercase_uuid = str(uuid.uuid4()).upper()
        gpu = GPU(
            uuid=uppercase_uuid,
            gpu_number=3,
            gpu_cluster="prod-us-east-1",
            node_name="node-001",
            gpu_type_name="nvidia-a100-40gb-sxm4",
            first_discovered=datetime.now(UTC),
            last_seen=datetime.now(UTC),
        )
        db.add(gpu)
        db.commit()

        # Should be stored as lowercase
        assert gpu.uuid == uppercase_uuid.lower()

    def test_create_gpu_with_invalid_uuid(self, db, sample_data):
        """Test that invalid UUID format raises error"""
        with pytest.raises(ValueError, match="Invalid UUID format"):
            GPU(
                uuid="not-a-valid-uuid",
                gpu_number=4,
                gpu_cluster="prod-us-east-1",
                node_name="node-001",
                gpu_type_name="nvidia-a100-40gb-sxm4",
                first_discovered=datetime.now(UTC),
                last_seen=datetime.now(UTC),
            )

    def test_gpu_uuid_without_hyphens_invalid(self, db, sample_data):
        """Test that UUID without hyphens is invalid"""
        with pytest.raises(ValueError, match="Invalid UUID format"):
            GPU(
                uuid="550e8400e29b41d4a716446655440000",  # No hyphens
                gpu_number=5,
                gpu_cluster="prod-us-east-1",
                node_name="node-001",
                gpu_type_name="nvidia-a100-40gb-sxm4",
                first_discovered=datetime.now(UTC),
                last_seen=datetime.now(UTC),
            )

    def test_gpu_relationships(self, db, sample_data):
        """Test GPU relationships to node and gpu_type"""
        gpu = sample_data["gpus"][0]

        # Test node relationship
        assert gpu.node is not None
        assert gpu.node.name == "node-001"

        # Test gpu_type relationship
        assert gpu.gpu_type is not None
        assert gpu.gpu_type.name == "nvidia-a100-40gb-sxm4"
        assert gpu.gpu_type.family == "NVIDIA A100"
        assert gpu.gpu_type.memory_gb == 40

    def test_gpu_last_seen_updates(self, db, sample_data):
        """Test that last_seen timestamp can be updated"""
        gpu = sample_data["gpus"][0]
        original_last_seen = gpu.last_seen

        # Update last_seen
        new_time = datetime.now(UTC) + timedelta(hours=1)
        gpu.last_seen = new_time
        db.commit()

        # Verify update
        db.refresh(gpu)
        assert gpu.last_seen != original_last_seen


class TestClustersAndNodes:
    """Test cluster and node endpoints"""

    def test_list_clusters(self, client, sample_data):
        """Test listing all clusters"""
        response = client.get("/api/v1/inventory/clusters")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(cluster["name"] == "prod-us-east-1" for cluster in data)

    def test_get_cluster_by_name(self, client, sample_data):
        """Test getting a specific cluster"""
        response = client.get("/api/v1/inventory/clusters/prod-us-east-1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "prod-us-east-1"
        assert data["cloud_name"] == "AWS"

    def test_get_cluster_not_found(self, client, sample_data):
        """Test getting non-existent cluster returns 404"""
        response = client.get("/api/v1/inventory/clusters/non-existent")
        assert response.status_code == 404

    def test_list_nodes(self, client, sample_data):
        """Test listing all nodes"""
        response = client.get("/api/v1/inventory/nodes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(node["name"] == "node-001" for node in data)

    def test_list_nodes_filter_by_cluster(self, client, sample_data):
        """Test filtering nodes by cluster"""
        response = client.get("/api/v1/inventory/nodes?cluster_name=prod-us-east-1")
        assert response.status_code == 200
        data = response.json()
        assert all(node["cluster_name"] == "prod-us-east-1" for node in data)

    def test_list_nodes_filter_by_team(self, client, sample_data):
        """Test filtering nodes by team"""
        response = client.get("/api/v1/inventory/nodes?team_name=AI Research")
        assert response.status_code == 200
        data = response.json()
        assert all(node["team_name"] == "AI Research" for node in data)

    def test_get_node_by_name(self, client, sample_data):
        """Test getting a specific node"""
        response = client.get("/api/v1/inventory/nodes/node-001")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "node-001"
        assert data["cluster_name"] == "prod-us-east-1"

    def test_get_node_not_found(self, client, sample_data):
        """Test getting non-existent node returns 404"""
        response = client.get("/api/v1/inventory/nodes/non-existent")
        assert response.status_code == 404
