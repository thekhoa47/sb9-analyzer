FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps only if needed (psycopg[binary] works without build tools).
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*

# Install deps first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy your app
COPY . .

# Cloud Run sends traffic to $PORT (default 8080). Gunicorn binds to it.
ENV PORT=8080
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--workers", "1", "app.main:app"]
