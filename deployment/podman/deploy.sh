#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../../backend" && pwd)"

echo "=== GPU Monitoring Dashboard - Podman Deployment ==="
echo ""

# Build backend image
echo "Step 1: Building backend container image..."
cd "$BACKEND_DIR"
podman build -t localhost/gpuaas-backend:latest -f "$SCRIPT_DIR/Containerfile" .
echo "✓ Backend image built"
echo ""

# Deploy PostgreSQL (includes secrets)
echo "Step 2: Deploying PostgreSQL..."
cd "$SCRIPT_DIR"
podman kube play postgres.yaml
echo "✓ PostgreSQL deployed"
echo ""

# Wait for PostgreSQL to be ready
echo "Step 3: Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
  if podman exec postgres pg_isready -U gpuaas &>/dev/null; then
    echo "✓ PostgreSQL is ready"
    break
  fi
  echo "  Waiting... ($i/30)"
  sleep 2
done
echo ""

# Deploy Victoria Metrics
echo "Step 4: Deploying Victoria Metrics..."
podman kube play victoria-metrics.yaml
echo "✓ Victoria Metrics deployed"
echo ""

# Deploy backend (includes config)
echo "Step 5: Deploying backend API..."
podman kube play backend.yaml
echo "✓ Backend API deployed"
echo ""

# Wait for backend to be ready
echo "Step 6: Waiting for backend to be ready..."
for i in {1..30}; do
  if curl -s http://localhost:8000/health &>/dev/null; then
    echo "✓ Backend is ready"
    break
  fi
  echo "  Waiting... ($i/30)"
  sleep 2
done
echo ""

echo "=== Deployment Complete ==="
echo ""
echo "Access points:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - PostgreSQL: localhost:5432"
echo "  - Victoria Metrics: http://localhost:8428"
echo ""
echo "Useful commands:"
echo "  - View pods: podman pod ps"
echo "  - View logs: podman logs <container-name>"
echo "  - Stop all: $SCRIPT_DIR/undeploy.sh"
