# Podman Kube Play Deployment

This directory contains Kubernetes manifests for running the GPU Monitoring Dashboard with Podman's `kube play` feature.

## Prerequisites

- Podman 4.0 or later
- Sufficient disk space for persistent volumes

## Quick Start

### 1. Build the Backend Container Image

```bash
cd /home/scondon/git/AIPCC-GPUaaS/monitoring-dashboard/backend
podman build -t localhost/gpuaas-backend:latest -f ../deployment/podman/Containerfile .
```

### 2. Create the Persistent Volumes (Optional)

Podman will create volumes automatically, but you can pre-create them:

```bash
podman volume create postgres-data
podman volume create vm-data
```

### 3. Deploy the Application

Deploy in this order to ensure dependencies are ready:

```bash
cd /home/scondon/git/AIPCC-GPUaaS/monitoring-dashboard/deployment/podman

# Deploy secrets and config
podman kube play secret.yaml
podman kube play configmap.yaml

# Deploy PostgreSQL
podman kube play postgres.yaml

# Deploy Victoria Metrics
podman kube play victoria-metrics.yaml

# Wait a few seconds for PostgreSQL to be ready, then deploy backend
sleep 5
podman kube play backend.yaml
```

### 4. Verify Deployment

```bash
# Check running pods
podman pod ps

# Check container logs
podman logs postgres
podman logs victoria-metrics
podman logs gpuaas-backend

# Test the API
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## Access Points

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Victoria Metrics**: http://localhost:8428

## Sample data

To load in some sample data run (from `backend` folder):

```bash
DATABASE_URL=postgresql://gpuaas:changeme123@localhost:5432/gpuaas \ poetry run python scripts/seed_all.py
```


## Management Commands

### Stop All Services

```bash
podman kube down backend.yaml
podman kube down victoria-metrics.yaml
podman kube down postgres.yaml
podman kube down configmap.yaml
podman kube down secret.yaml
```

### Restart a Service

```bash
# Example: Restart backend
podman kube down backend.yaml
podman kube play backend.yaml
```

### View Logs

```bash
# All containers in a pod
podman pod logs gpuaas-backend

# Specific container
podman logs gpuaas-backend-backend

# Follow logs
podman logs -f gpuaas-backend-backend
```

### Access Database

```bash
podman exec -it postgres psql -U gpuaas -d gpuaas
```

## Development Workflow

The backend manifest uses a hostPath volume mount, so code changes are reflected immediately:

1. Make changes to code in `/home/scondon/git/AIPCC-GPUaaS/monitoring-dashboard/backend`
2. Restart the backend pod:
   ```bash
   podman kube down backend.yaml
   podman kube play backend.yaml
   ```

For production, rebuild the container image instead:

```bash
cd /home/scondon/git/AIPCC-GPUaaS/monitoring-dashboard/backend
podman build -t localhost/gpuaas-backend:latest -f ../deployment/podman/Containerfile .
podman kube down backend.yaml
podman kube play backend.yaml
```

## Customization

### Change Database Password

Edit `secret.yaml` and update the `postgres-password` and `database-url` fields, then redeploy:

```bash
podman kube down backend.yaml
podman kube down postgres.yaml
podman kube down secret.yaml
podman kube play secret.yaml
podman kube play postgres.yaml
podman kube play backend.yaml
```

### Change Resource Limits

Edit the respective YAML files and modify the `resources` sections, then redeploy.

### Adjust Storage Size

Edit the PersistentVolumeClaim `storage` values in `postgres.yaml` or `victoria-metrics.yaml`, then redeploy. Note: existing data will be preserved.

## Troubleshooting

### Backend fails to start

Check if PostgreSQL is ready:
```bash
podman exec -it postgres pg_isready
```

Check backend logs:
```bash
podman logs gpuaas-backend-backend
```

### Database connection errors

Verify the secret is correctly configured:
```bash
podman exec -it postgres env | grep POSTGRES
```

### Port already in use

If ports 5432, 8428, or 8000 are already in use, edit the `hostPort` values in the respective YAML files.

## Data Persistence

Data is stored in Podman volumes:
- `postgres-data`: PostgreSQL database
- `vm-data`: Victoria Metrics time-series data

To back up data:
```bash
# Export PostgreSQL data
podman exec postgres pg_dump -U gpuaas gpuaas > backup.sql

# Restore PostgreSQL data
podman exec -i postgres psql -U gpuaas gpuaas < backup.sql
```

## Cleanup

To remove everything including data:

```bash
podman kube down backend.yaml
podman kube down victoria-metrics.yaml
podman kube down postgres.yaml
podman kube down configmap.yaml
podman kube down secret.yaml

# Remove volumes (WARNING: This deletes all data)
podman volume rm postgres-data vm-data
```
