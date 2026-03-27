# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GPU resource management and cost monitoring dashboard. Tracks GPU allocations across cloud providers (AWS, GCP, Azure, IBM Cloud, OCI), correlates with cost data from Apptio/Cloudability, and provides team-based resource management. Built with a FastAPI backend, Streamlit frontend, PostgreSQL for relational data, and Victoria Metrics for time-series metrics.

## Common Commands

### Backend (run from `/backend/`)

```bash
poetry install                                    # Install dependencies
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # Dev server
poetry run pytest -v                              # Run all tests
poetry run pytest tests/api/test_resources.py -v  # Run single test file
poetry run pytest -k "test_name" -v               # Run single test by name
poetry run black --check .                        # Check formatting
poetry run black .                                # Auto-format
poetry run ruff check .                           # Lint
poetry run ruff check --fix .                     # Auto-fix lint issues
poetry run python -m alembic upgrade head         # Run DB migrations
poetry run python -m alembic revision --autogenerate -m "description"  # Create migration
```

### Frontend (run from `/frontend/`)

```bash
poetry install                    # Install dependencies
streamlit run main.py             # Dev server (port 8501)
poetry run pytest -v              # Run tests
poetry run black --check .        # Check formatting
poetry run ruff check .           # Lint
```

## Architecture

### Data Flow

```
DCGM Metrics (Prometheus) → Victoria Metrics → Backend API (FastAPI) → Frontend (Streamlit)
                                                      ↕
                                                 PostgreSQL
```

Cost data flows from Apptio/Cloudability through the `/cloudability/` scripts into the backend.

### Backend Structure (`/backend/`)

- `app/main.py` — FastAPI app entry point
- `app/api/v1/` — Route handlers organized by domain:
  - `resources/` — Reference data (clouds, teams, GPU types)
  - `inventory/` — Clusters, nodes, GPUs
  - `allocations/` — GPU allocation management
  - `metrics/` — Victoria Metrics queries
  - `costs/` — Cost analysis
  - `analytics/` — Aggregation endpoints
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic request/response schemas
- `app/crud/` — Database operations
- `app/db/` — Database connection and session management
- `alembic/` — Database migration files

### Core Domain Entities

- **GpuType** — GPU models (A100, H100, L4, T4, etc.)
- **GPUCluster / GPUNode / GPU** — Infrastructure hierarchy
- **Team** — Organizational units consuming GPU resources
- **Allocation** — Maps GPUs to teams with time periods and workload types (committed, on-demand, spot)
- **CostTimeseries** — Historical cost data from cloud billing

### Frontend Structure (`/frontend/`)

- `main.py` — Streamlit app entry point
- Pages: Overview, Cost Explorer, Inventory, Allocations, Reference Data

### Deployment (`/deployment/podman/`)

Podman/Kubernetes YAML manifests with init containers for PostgreSQL readiness and Alembic migrations. Uses Red Hat UBI9 Python 3.12 base images.

## Configuration

Backend and frontend each have `.env.example` files showing required environment variables (database URL, Victoria Metrics URL, CORS origins, backend API URL).

All python programs should be run through the poetry command.

When running containers prefer the use of podman, and try to reuse the podman play pattern used in the deployment folder.

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on push to main and PRs: black, ruff, pytest for both backend and frontend, plus Trivy security scanning and Hadolint for Containerfiles.
