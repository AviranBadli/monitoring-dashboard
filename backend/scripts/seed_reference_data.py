"""Seed reference/lookup data for the database"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models import Cloud, GpuType, Team, WorkloadType, AllocationType, InstanceType


def seed_reference_data():
    """Seed lookup tables with reference data"""
    db = SessionLocal()
    try:
        print("Seeding reference data...")

        # Clouds
        clouds = [
            Cloud(name="AWS"),
            Cloud(name="GCP"),
            Cloud(name="Azure"),
            Cloud(name="IBM Cloud"),
            Cloud(name="OCI"),
        ]
        db.add_all(clouds)
        db.flush()
        print(f"✓ Added {len(clouds)} cloud providers")

        # GPU Types
        gpu_types = [
            GpuType(name="A100"),
            GpuType(name="A100-80GB"),
            GpuType(name="H100"),
            GpuType(name="H100-80GB"),
            GpuType(name="V100"),
            GpuType(name="V100-32GB"),
            GpuType(name="L4"),
            GpuType(name="L40S"),
            GpuType(name="A10G"),
            GpuType(name="T4"),
        ]
        db.add_all(gpu_types)
        db.flush()
        print(f"✓ Added {len(gpu_types)} GPU types")

        # Teams
        teams = [
            Team(name="AI Research"),
            Team(name="ML Platform"),
            Team(name="Data Science"),
            Team(name="DevOps"),
            Team(name="LLM Training"),
            Team(name="Computer Vision"),
        ]
        db.add_all(teams)
        db.flush()
        print(f"✓ Added {len(teams)} teams")

        # Workload Types
        workload_types = [
            WorkloadType(name="training"),
            WorkloadType(name="inference"),
            WorkloadType(name="development"),
            WorkloadType(name="idle"),
            WorkloadType(name="testing"),
        ]
        db.add_all(workload_types)
        db.flush()
        print(f"✓ Added {len(workload_types)} workload types")

        # Allocation Types
        allocation_types = [
            AllocationType(name="on-demand", priority=1),
            AllocationType(name="reserved", priority=2),
            AllocationType(name="spot", priority=3),
        ]
        db.add_all(allocation_types)
        db.flush()
        print(f"✓ Added {len(allocation_types)} allocation types")

        # Instance Types
        instance_types = [
            # AWS
            InstanceType(name="p4d.24xlarge", cloud_name="AWS"),      # 8x A100 40GB
            InstanceType(name="p4de.24xlarge", cloud_name="AWS"),     # 8x A100 80GB
            InstanceType(name="p5.48xlarge", cloud_name="AWS"),       # 8x H100 80GB
            InstanceType(name="p3.2xlarge", cloud_name="AWS"),        # 1x V100
            InstanceType(name="p3.8xlarge", cloud_name="AWS"),        # 4x V100
            InstanceType(name="p3.16xlarge", cloud_name="AWS"),       # 8x V100
            InstanceType(name="g5.xlarge", cloud_name="AWS"),         # 1x A10G
            InstanceType(name="g5.12xlarge", cloud_name="AWS"),       # 4x A10G
            InstanceType(name="g4dn.xlarge", cloud_name="AWS"),       # 1x T4
            # GCP
            InstanceType(name="a2-highgpu-1g", cloud_name="GCP"),     # 1x A100 40GB
            InstanceType(name="a2-highgpu-2g", cloud_name="GCP"),     # 2x A100 40GB
            InstanceType(name="a2-highgpu-4g", cloud_name="GCP"),     # 4x A100 40GB
            InstanceType(name="a2-highgpu-8g", cloud_name="GCP"),     # 8x A100 40GB
            InstanceType(name="a2-ultragpu-1g", cloud_name="GCP"),    # 1x A100 80GB
            InstanceType(name="a2-ultragpu-8g", cloud_name="GCP"),    # 8x A100 80GB
            InstanceType(name="a3-highgpu-8g", cloud_name="GCP"),     # 8x H100 80GB
            InstanceType(name="g2-standard-4", cloud_name="GCP"),     # 1x L4
            # Azure
            InstanceType(name="Standard_ND96asr_v4", cloud_name="Azure"),  # 8x A100 40GB
            InstanceType(name="Standard_ND96amsr_A100_v4", cloud_name="Azure"),  # 8x A100 80GB
            InstanceType(name="Standard_NC24ads_A100_v4", cloud_name="Azure"),   # 1x A100 80GB
            InstanceType(name="Standard_NC6s_v3", cloud_name="Azure"),     # 1x V100
            InstanceType(name="Standard_NC24s_v3", cloud_name="Azure"),    # 4x V100
        ]
        db.add_all(instance_types)
        db.flush()
        print(f"✓ Added {len(instance_types)} instance types")

        db.commit()
        print("\n✓ Reference data seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_reference_data()
