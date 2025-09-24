# backend/Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    PORT=8080

WORKDIR /app

# minimal OS deps (curl only if you truly need it)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# deps
COPY requirements.txt /app/requirements.txt
# BuildKit cache speeds up builds (safe to keep; if it’s ignored, still fine)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --prefer-binary -r /app/requirements.txt gunicorn uvicorn

# code
COPY app/ ./app

# non-root
RUN useradd -m appuser && chown -R appuser:appuser /app

# entrypoint to expand DOTENV (Secret Manager) into env vars
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["sh","-c","exec gunicorn -k uvicorn.workers.UvicornWorker --chdir /app --bind 0.0.0.0:${PORT:-8080} --workers 1 app.main:app"]
