"""Seed test data with realistic GPU infrastructure and allocations"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models import (
    Owner, GPUCluster, GPUNode, GPU, Allocation, CostTimeseries
)


def seed_test_data():
    """Create realistic test infrastructure and allocations"""
    db = SessionLocal()
    try:
        print("Seeding test data...")

        # Create Owners
        owners = [
            Owner(name="Alice Chen", email="alice.chen@example.com", team_name="AI Research"),
            Owner(name="Bob Smith", email="bob.smith@example.com", team_name="ML Platform"),
            Owner(name="Carol Davis", email="carol.davis@example.com", team_name="LLM Training"),
            Owner(name="David Wilson", email="david.wilson@example.com", team_name="Data Science"),
        ]
        db.add_all(owners)
        db.flush()
        print(f"✓ Added {len(owners)} owners")

        # Create GPU Clusters
        clusters = [
            GPUCluster(name="prod-us-east-1", cloud_name="AWS", owner_id=owners[0].id),
            GPUCluster(name="prod-us-west-2", cloud_name="AWS", owner_id=owners[1].id),
            GPUCluster(name="prod-gcp-us-central1", cloud_name="GCP", owner_id=owners[2].id),
            GPUCluster(name="dev-azure-eastus", cloud_name="Azure", owner_id=owners[3].id),
        ]
        db.add_all(clusters)
        db.flush()
        print(f"✓ Added {len(clusters)} GPU clusters")

        # Create GPU Nodes and GPUs
        node_configs = [
            # AWS prod-us-east-1
            ("prod-us-east-1-node-001", "prod-us-east-1", "p4d.24xlarge", "AI Research", 8, "NVIDIA A100-SXM4-40GB", "A100"),
            ("prod-us-east-1-node-002", "prod-us-east-1", "p4d.24xlarge", "AI Research", 8, "NVIDIA A100-SXM4-40GB", "A100"),
            ("prod-us-east-1-node-003", "prod-us-east-1", "p4de.24xlarge", "LLM Training", 8, "NVIDIA A100-SXM4-80GB", "A100-80GB"),
            # AWS prod-us-west-2
            ("prod-us-west-2-node-001", "prod-us-west-2", "p3.16xlarge", "ML Platform", 8, "Tesla V100-SXM2-16GB", "V100"),
            ("prod-us-west-2-node-002", "prod-us-west-2", "g5.12xlarge", "ML Platform", 4, "NVIDIA A10G", "A10G"),
            # GCP prod-gcp-us-central1
            ("prod-gcp-node-001", "prod-gcp-us-central1", "a2-highgpu-8g", "LLM Training", 8, "NVIDIA A100-SXM4-40GB", "A100"),
            ("prod-gcp-node-002", "prod-gcp-us-central1", "a3-highgpu-8g", "LLM Training", 8, "NVIDIA H100-SXM5-80GB", "H100-80GB"),
            # Azure dev-azure-eastus
            ("dev-azure-node-001", "dev-azure-eastus", "Standard_NC24s_v3", "Data Science", 4, "Tesla V100-PCIE-16GB", "V100"),
        ]

        all_gpus = []
        for node_name, cluster_name, instance_type, team, gpu_count, model_name, gpu_type in node_configs:
            # Create node
            node = GPUNode(
                name=node_name,
                cluster_name=cluster_name,
                instance_type_name=instance_type,
                team_name=team
            )
            db.add(node)
            db.flush()

            # Create GPUs for this node
            for i in range(gpu_count):
                gpu_uuid = f"GPU-{node_name}-{i:02d}"
                gpu = GPU(
                    uuid=gpu_uuid,
                    gpu_number=i,
                    gpu_cluster=cluster_name,
                    model_name=model_name,
                    node_name=node_name,
                    gpu_type_name=gpu_type,
                    first_discovered=datetime.utcnow() - timedelta(days=random.randint(30, 90)),
                    last_seen=datetime.utcnow()
                )
                db.add(gpu)
                all_gpus.append(gpu)

        db.flush()
        print(f"✓ Added {len(node_configs)} GPU nodes with {len(all_gpus)} GPUs")

        # Create Allocations (last 30 days)
        allocations = []
        workload_types = ["training", "inference", "development", "idle"]
        allocation_types = ["on-demand", "reserved", "spot"]
        teams = ["AI Research", "ML Platform", "LLM Training", "Data Science"]

        base_time = datetime.utcnow() - timedelta(days=30)

        for gpu in all_gpus:
            current_time = base_time
            end_time = datetime.utcnow()

            # Create 5-10 allocation periods for each GPU over 30 days
            num_allocations = random.randint(5, 10)

            for _ in range(num_allocations):
                if current_time >= end_time:
                    break

                # Random allocation duration: 1 hour to 7 days
                duration_hours = random.randint(1, 168)
                alloc_end = min(current_time + timedelta(hours=duration_hours), end_time)

                allocation = Allocation(
                    gpu_uuid=gpu.uuid,
                    team_name=random.choice(teams),
                    workload_type_name=random.choice(workload_types),
                    allocation_type_name=random.choice(allocation_types),
                    start_time=current_time,
                    end_time=alloc_end
                )
                allocations.append(allocation)

                # Move to next time period (with possible gap)
                current_time = alloc_end + timedelta(minutes=random.randint(0, 120))

        db.add_all(allocations)
        db.flush()
        print(f"✓ Added {len(allocations)} allocations")

        # Create Cost Timeseries data
        cost_data = []

        # Cost per hour by instance type (approximations in USD)
        instance_costs = {
            "p4d.24xlarge": 32.77,
            "p4de.24xlarge": 40.96,
            "p5.48xlarge": 98.32,
            "p3.16xlarge": 24.48,
            "g5.12xlarge": 5.672,
            "a2-highgpu-8g": 12.48,
            "a3-highgpu-8g": 26.00,
            "Standard_NC24s_v3": 12.24,
        }

        # Generate hourly cost data for the last 30 days
        for node_name, cluster_name, instance_type, team, gpu_count, model_name, gpu_type in node_configs:
            base_cost = instance_costs.get(instance_type, 10.0)

            current_time = base_time
            while current_time < datetime.utcnow():
                # Randomly assign workload type based on time of day
                hour = current_time.hour
                if 2 <= hour <= 6:
                    workload = "idle"
                elif random.random() < 0.7:
                    workload = "training"
                else:
                    workload = random.choice(["inference", "development"])

                cost_entry = CostTimeseries(
                    date=current_time,
                    duration_seconds=3600,  # 1 hour
                    cost=base_cost,
                    node_name=node_name,
                    instance_type_name=instance_type,
                    workload_type_name=workload
                )
                cost_data.append(cost_entry)

                current_time += timedelta(hours=1)

        db.add_all(cost_data)
        db.flush()
        print(f"✓ Added {len(cost_data)} cost timeseries entries")

        db.commit()
        print("\n✓ Test data seeded successfully!")
        print("\nSummary:")
        print(f"  - {len(owners)} owners")
        print(f"  - {len(clusters)} GPU clusters")
        print(f"  - {len(node_configs)} GPU nodes")
        print(f"  - {len(all_gpus)} GPUs")
        print(f"  - {len(allocations)} allocations")
        print(f"  - {len(cost_data)} cost entries")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error seeding test data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_test_data()
