"""Seed reference/lookup data for the database"""

import sys
import csv
import re
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models import Cloud, GpuType, Team, WorkloadType, AllocationType, InstanceType


def to_kebab_case(text):
    """
    Convert text to kebab-case (lowercase with hyphens)

    Examples:
        "NVIDIA A100 40GB SXM4" -> "nvidia-a100-40gb-sxm4"
        "Intel Gaudi 3 128GB PCIe" -> "intel-gaudi-3-128gb-pcie"
    """
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    # Remove any non-alphanumeric characters except hyphens
    text = re.sub(r'[^a-zA-Z0-9-]', '', text)
    # Convert to lowercase
    text = text.lower()
    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text


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

        # GPU Types - read from CSV file
        csv_path = Path(__file__).parent.parent.parent / "apptio" / "GPU-types-by-cloud-provider.csv"
        gpu_types_data = set()  # Use set to get unique combinations

        try:
            with open(csv_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    gpu_family = row['GPU Type'].strip()
                    memory_str = row['GPU Memory (GB)'].strip()
                    variant = row['GPU Variant'].strip()

                    # Skip if GPU Type is empty
                    if not gpu_family:
                        raise ValueError(f"GPU Type is empty in row {row} of {csv_path}");

                    # Parse memory (handle cases like "1/8" or empty values)
                    try:
                        if '/' in memory_str:
                            # For fractional values, use 0 or skip
                            memory_gb = 0
                        elif memory_str:
                            memory_gb = int(float(memory_str))
                        else:
                            memory_gb = 0
                    except (ValueError, AttributeError):
                        memory_gb = 0

                    # Create unique tuple
                    gpu_types_data.add((gpu_family, memory_gb, variant))

            # Create GpuType objects from unique combinations
            gpu_types = []
            for family, memory_gb, variant in sorted(gpu_types_data):
                # Create display name from family, memory, and variant
                if variant and memory_gb > 0:
                    display_name = f"{family} {memory_gb}GB {variant}"
                elif memory_gb > 0:
                    display_name = f"{family} {memory_gb}GB"
                elif variant:
                    display_name = f"{family} {variant}"
                else:
                    display_name = family

                # Convert display name to kebab-case for the name field (primary key)
                kebab_name = to_kebab_case(display_name)

                gpu_type = GpuType(
                    name=kebab_name,
                    display_name=display_name,
                    family=family,
                    memory_gb=memory_gb,
                    variant=variant if variant else None
                )
                gpu_types.append(gpu_type)

            db.add_all(gpu_types)
            db.flush()
            print(f"✓ Added {len(gpu_types)} GPU types from CSV")

        except FileNotFoundError:
            print(f"⚠ Warning: CSV file not found at {csv_path}")
            print("  Using fallback GPU types...")
            # Fallback to basic GPU types if CSV not found
            fallback_data = [
                ("NVIDIA A100", 40, None),
                ("NVIDIA H100", 80, None),
                ("NVIDIA V100", 16, None),
                ("NVIDIA L4", 24, None),
            ]
            gpu_types = []
            for family, memory_gb, variant in fallback_data:
                display_name = f"{family} {memory_gb}GB"
                name = to_kebab_case(display_name)
                gpu_types.append(
                    GpuType(
                        name=name,
                        display_name=display_name,
                        family=family,
                        memory_gb=memory_gb,
                        variant=variant
                    )
                )
            db.add_all(gpu_types)
            db.flush()
            print(f"✓ Added {len(gpu_types)} fallback GPU types")

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
