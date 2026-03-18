# Database Seed Scripts

Scripts to populate the database with reference and test data.

## Usage

### Seed All Data (Recommended)

Run this to populate the entire database with reference data and realistic test data:

```bash
poetry run python scripts/seed_all.py
```

### Seed Individual Datasets

**Reference Data Only** (clouds, GPU types, teams, instance types, etc.):
```bash
poetry run python scripts/seed_reference_data.py
```

**Test Data Only** (requires reference data to exist first):
```bash
poetry run python scripts/seed_test_data.py
```

## What Gets Created

### Reference Data
- **5 Cloud Providers**: AWS, GCP, Azure, IBM Cloud, OCI
- **10 GPU Types**: A100, H100, V100, L4, L40S, etc.
- **6 Teams**: AI Research, ML Platform, Data Science, DevOps, LLM Training, Computer Vision
- **5 Workload Types**: training, inference, development, idle, testing
- **3 Allocation Types**: on-demand, reserved, spot
- **22 Instance Types**: Various AWS, GCP, and Azure GPU instance types

### Test Data
- **4 Owners**: Team leads with email addresses
- **4 GPU Clusters**: Across AWS, GCP, and Azure
- **8 GPU Nodes**: With different instance types
- **60 GPUs**: Distributed across nodes (A100, H100, V100, A10G)
- **~500 Allocations**: 30 days of allocation history
- **~5,760 Cost Entries**: Hourly cost data for 30 days

## Test Data Details

### Clusters
- `prod-us-east-1` (AWS) - AI Research team
- `prod-us-west-2` (AWS) - ML Platform team
- `prod-gcp-us-central1` (GCP) - LLM Training team
- `dev-azure-eastus` (Azure) - Data Science team

### Sample Nodes
- 3x p4d.24xlarge (8x A100 40GB each)
- 1x p4de.24xlarge (8x A100 80GB)
- 1x p3.16xlarge (8x V100)
- 1x g5.12xlarge (4x A10G)
- 1x a2-highgpu-8g (8x A100 40GB)
- 1x a3-highgpu-8g (8x H100 80GB)
- 1x Standard_NC24s_v3 (4x V100)

### Data Characteristics
- Allocations span the last 30 days
- Random allocation durations (1 hour to 7 days)
- Mix of workload types (training, inference, development, idle)
- Mix of allocation types (on-demand, reserved, spot)
- Hourly cost tracking with realistic pricing
- More idle time during early morning hours (2-6 AM)

## Prerequisites

1. Database must be running and accessible
2. Database schema must be up to date:
   ```bash
   poetry run python -m alembic upgrade head
   ```

## Resetting Data

To start fresh, drop and recreate the database, then run migrations and seed scripts:

```bash
# Drop all tables (requires database access)
poetry run python -m alembic downgrade base

# Recreate tables
poetry run python -m alembic upgrade head

# Seed data
poetry run python scripts/seed_all.py
```

## Notes

- Scripts are idempotent within a transaction but will fail if run twice (duplicate keys)
- Foreign key relationships are respected (reference data must exist first)
- All timestamps use UTC
- GPU UUIDs follow pattern: `GPU-{node_name}-{gpu_number}`
- Cost data uses approximate real-world pricing
