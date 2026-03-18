"""Run all seed scripts in the correct order"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from seed_reference_data import seed_reference_data
from seed_test_data import seed_test_data


def main():
    """Seed all data"""
    print("=" * 60)
    print("SEEDING DATABASE")
    print("=" * 60)
    print()

    try:
        # Step 1: Reference data (must come first due to foreign keys)
        print("Step 1: Seeding reference data...")
        print("-" * 60)
        seed_reference_data()
        print()

        # Step 2: Test data
        print("Step 2: Seeding test data...")
        print("-" * 60)
        seed_test_data()
        print()

        print("=" * 60)
        print("✓ ALL DATA SEEDED SUCCESSFULLY!")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ SEEDING FAILED: {e}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
