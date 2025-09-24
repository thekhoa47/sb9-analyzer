#!/bin/sh
set -eu

# Expand single-secret .env into real env vars
if [ "${DOTENV:-}" != "" ]; then
  echo "$DOTENV" > /tmp/runtime.env
  set -a; . /tmp/runtime.env; set +a
fi

exec "$@"
