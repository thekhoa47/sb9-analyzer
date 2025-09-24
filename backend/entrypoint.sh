#!/bin/sh
set -eu

# If Cloud Run injected the entire .env as a single env var (DOTENV),
# export all lines as real environment variables before starting the app.
if [ "${DOTENV:-}" != "" ]; then
  # write to a temp file so we can 'set -a; . file'
  echo "$DOTENV" > /tmp/runtime.env
  set -a
  . /tmp/runtime.env
  set +a
fi

exec "$@"
