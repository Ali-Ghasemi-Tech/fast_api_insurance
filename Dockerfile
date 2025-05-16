FROM python:3.11-slim

# Install system dependencies needed to build psycopg
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install python packages
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .
CMD ["bash", "-c", "alembic upgrade head &&python app/API/import_hospitals.py &&uvicorn app/API.main:app --host 0.0.0.0 --port 8000"] 