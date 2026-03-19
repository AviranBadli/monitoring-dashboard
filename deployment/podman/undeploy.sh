#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== GPU Monitoring Dashboard - Undeploy ==="
echo ""

cd "$SCRIPT_DIR"

echo "Stopping backend..."
podman kube down backend.yaml 2>/dev/null || true

echo "Stopping Victoria Metrics..."
podman kube down victoria-metrics.yaml 2>/dev/null || true

echo "Stopping PostgreSQL..."
podman kube down postgres.yaml 2>/dev/null || true

echo ""
echo "=== Undeploy Complete ==="
echo ""
echo "Note: Persistent volumes (postgres-data, vm-data) are preserved."
echo "To remove them, run:"
echo "  podman volume rm postgres-data vm-data"
