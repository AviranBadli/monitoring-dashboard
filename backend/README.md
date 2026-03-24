# GPU Monitoring API

FastAPI backend for GPU monitoring, allocation, and cost tracking.

## Setup

### Prerequisites
- Python 3.11+
- Poetry
- PostgreSQL (or PostgreSQL + TimescaleDB)
- Victoria Metrics

### Installation

```bash
# Install dependencies
poetry install

# Copy environment file
cp .env.example .env

# Edit .env with your database and Victoria Metrics URLs
```

### Database Setup

```bash
# Run migrations
poetry run python -m alembic upgrade head
```

### Running the API

```bash
# Development mode with auto-reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: http://localhost:8000

- API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Development

### Create a new migration

```bash
poetry run python -m alembic revision --autogenerate -m "description"
```

### Run tests

```bash
poetry run pytest
```

### Code formatting

```bash
poetry run black .
poetry run ruff check .
```

## Project Structure

```
app/
├── api/v1/          # API endpoints
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
├── services/        # Business logic
└── core/            # Core config and setup
```
