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
RUN pip install --upgrade pip && \
    pip install --prefer-binary -r /app/requirements.txt

# code
COPY app /app

# non-root
RUN useradd -m appuser && chown -R appuser:appuser /app

# entrypoint to expand DOTENV (Secret Manager) into env vars
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["sh","-c","exec gunicorn -k uvicorn.workers.UvicornWorker --chdir / --bind 0.0.0.0:${PORT:-8080} --workers 1 app.main:app"]
# Use --chdir / (then app.main:app) instead of /app (main:app) because otherwise, we will run into import error for any "from app.something.something import ..."