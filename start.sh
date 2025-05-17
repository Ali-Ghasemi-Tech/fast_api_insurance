#!/bin/bash
set -e  # Stop on error

echo "Running Alembic migrations..."
alembic upgrade head

echo "Importing hospitals data..."
python API/import_hospitals.py

echo "Starting FastAPI app..."
uvicorn API.main:app --host 0.0.0.0 --port 8000
