#!/bin/bash
set -e  # Stop on error

# echo "Running Alembic migrations..."
# alembic upgrade head

echo "Starting FastAPI app..."
uvicorn API.main:app --host 0.0.0.0 --port 3000 --limit-concurrency 10
