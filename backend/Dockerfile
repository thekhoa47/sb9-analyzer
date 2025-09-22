# backend/Dockerfile  (you run: docker build -t hannahanhdao-image:dev .)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# deps
COPY requirements.txt /app/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && pip install --prefer-binary -r /app/requirements.txt

# code (copies backend/* into /app, so your package is at /app/app)
COPY . /app/

# bind to $PORT at runtime (fallback 8080 locally)
CMD ["sh","-c","exec gunicorn -k uvicorn.workers.UvicornWorker --chdir /app --bind 0.0.0.0:${PORT:-8080} --workers 1 app.main:app"]
