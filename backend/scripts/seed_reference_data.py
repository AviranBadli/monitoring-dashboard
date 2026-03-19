"""Seed reference/lookup data for the database"""

from typing import Any


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
    text = re.sub(r"[\s_]+", "-", text)
    # Remove any non-alphanumeric characters except hyphens
    text = re.sub(r"[^a-zA-Z0-9-]", "", text)
    # Convert to lowercase
    text = text.lower()
    # Remove multiple consecutive hyphens
    text = re.sub(r"-+", "-", text)
    # Remove leading/trailing hyphens
    text = text.strip("-")
    return text


def parse_gpu_memory(memory_str):
    """Parse GPU memory string, handling fractional values and empty strings"""
    try:
        if "/" in memory_str:
            # For fractional values, use 0
            return 0
        elif memory_str:
            return int(float(memory_str))
        else:
            return 0
    except (ValueError, AttributeError):
        return 0


def build_gpu_display_name(family, memory_gb, variant):
    """Build GPU type display name from components"""
    if variant and memory_gb > 0:
        return f"{family} {memory_gb}GB {variant}"
    elif memory_gb > 0:
        return f"{family} {memory_gb}GB"
    elif variant:
        return f"{family} {variant}"
    else:
        return family


def read_csv_data(csv_path):
    """Read CSV file and return all rows as a list"""
    with open(csv_path, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def seed_reference_data():
    """Seed lookup tables with reference data"""
    db = SessionLocal()
    try:
        print("Seeding reference data...")

        # Read CSV file once
        csv_path = (
            Path(__file__).parent.parent.parent / "apptio" / "GPU-types-by-cloud-provider.csv"
        )

        csv_data = read_csv_data(csv_path)
        print(f"✓ Read {len(csv_data)} rows from CSV file")

        # Clouds
        cloud_names = set[str]()
        for row in csv_data:
            cloud_name = row["Cloud Provider"].strip()
            if cloud_name:
                cloud_names.add(cloud_name)

        # Hardcoded cloud names for now
        cloud_names.update(["RDU4", "IAD1"])

        clouds = [Cloud(name=name) for name in sorted(cloud_names)]
        db.add_all(clouds)
        db.flush()
        print(f"✓ Added {len(clouds)} cloud providers: {', '.join(sorted(cloud_names))}")


        # GPU Types
        gpu_types_data = set[Any]()  # Use set to get unique combinations
        for row in csv_data:
            gpu_family = row["GPU Type"].strip()
            memory_str = row["GPU Memory (GB)"].strip()
            variant = row["GPU Variant"].strip()

            # Skip if GPU Type is empty
            if not gpu_family:
                continue

            memory_gb = parse_gpu_memory(memory_str)
            gpu_types_data.add((gpu_family, memory_gb, variant))

        # Create GpuType objects from unique combinations
        gpu_types = []
        for family, memory_gb, variant in sorted(gpu_types_data):
            display_name = build_gpu_display_name(family, memory_gb, variant)
            kebab_name = to_kebab_case(display_name)

            gpu_type = GpuType(
                name=kebab_name,
                display_name=display_name,
                family=family,
                memory_gb=memory_gb,
                variant=variant if variant else None,
            )
            gpu_types.append(gpu_type)

        db.add_all(gpu_types)
        db.flush()
        print(f"✓ Added {len(gpu_types)} GPU types from CSV")


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
        instance_types = []
        skipped_count = 0
        for row in csv_data:
            instance_name = row["Instance Type"].strip()
            instance_family = row["Instance Family"].strip()
            cloud_name = row["Cloud Provider"].strip()
            gpu_family = row["GPU Type"].strip()
            memory_str = row["GPU Memory (GB)"].strip()
            variant = row["GPU Variant"].strip()
            gpu_count_str = row.get("GPU Count", "").strip()

            # Skip if required fields are empty
            if not instance_name or not cloud_name or not gpu_family or not gpu_count_str:
                skipped_count += 1
                continue

            # Parse GPU count
            try:
                gpu_count = float(gpu_count_str)
            except (ValueError, AttributeError):
                print(f"  ⚠ Warning: Invalid GPU count '{gpu_count_str}' for instance '{instance_name}', skipping")
                skipped_count += 1
                continue

            # Build GPU type name (same logic as GPU type creation)
            memory_gb = parse_gpu_memory(memory_str)
            gpu_display_name = build_gpu_display_name(gpu_family, memory_gb, variant)
            gpu_type_name = to_kebab_case(gpu_display_name)

            # Verify that the GPU type exists in the database
            gpu_type = db.query(GpuType).filter(GpuType.name == gpu_type_name).first()
            if not gpu_type:
                print(f"  ⚠ Warning: GPU type '{gpu_type_name}' not found for instance '{instance_name}', skipping")
                skipped_count += 1
                continue

            # Create instance type
            instance_type = InstanceType(
                name=instance_name,
                cloud_name=cloud_name,
                gpu_type_name=gpu_type_name,
                gpu_count=gpu_count,
                instance_family=instance_family,
            )
            instance_types.append(instance_type)

        db.add_all(instance_types)
        db.flush()
        print(f"✓ Added {len(instance_types)} instance types from CSV")
        if skipped_count > 0:
            print(f"  ⚠ Skipped {skipped_count} instance types (missing data or GPU type not found)")


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
