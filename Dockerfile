FROM python:3.11-slim

# Install system dependencies needed to build psycopg
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy requirements.txt and install python packages
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Set PYTHONPATH so Python can find 'API' module
ENV PYTHONPATH=/app

# CMD ["bash", "-c", "alembic upgrade head"] 
# COPY start.sh /app/start.sh
# RUN chmod +x /app/start.sh
# CMD ["/app/start.sh"]

CMD ["tail", "-f", "/dev/null"]