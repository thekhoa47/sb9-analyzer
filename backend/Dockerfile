# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/usr/local/bin:$PATH"

# Create user & workdir
RUN useradd -m appuser
WORKDIR /app

# System deps (psycopg2, geospatial libs if needed; add as necessary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install deps (force-install gunicorn/uvicorn if missing)
RUN pip install --upgrade pip && \
    pip install -r requirements.txt gunicorn uvicorn

# Copy app code
COPY app ./app
COPY alembic ./alembic
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Cloud Run sets $PORT; default to 8080 if not provided
ENV PORT=8080

# Run as non-root
USER appuser

# Health: if you have /health, Cloud Run can probe it
# EXPOSE is not required by Cloud Run, but harmless
EXPOSE 8080

# Entrypoint: loads DOTENV secret, then execs gunicorn
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:${PORT}", "--workers", "1", "app.main:app"]
