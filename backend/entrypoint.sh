#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until python3 -c "
import psycopg2, os, sys
try:
    psycopg2.connect(os.environ['DATABASE_URL'])
    print('PostgreSQL is ready!')
except Exception as e:
    print(f'Not ready: {e}')
    sys.exit(1)
" 2>/dev/null; do
  echo "  ...still waiting"
  sleep 2
done

echo "Running database migrations..."
python -m alembic upgrade head

echo "Seeding mock data..."
python scripts/seed_all.py

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
