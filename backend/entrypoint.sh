#!/bin/sh
set -e  # keep -e so we exit on real failures; drop -u because it's too strict for secrets

if [ -f /tmp/runtime.env ]; then
  while IFS= read -r line; do
    case "$line" in
      ''|\#*)
        continue
        ;;
      *=*)
        key=$(printf '%s' "$line" | cut -d '=' -f 1)
        val=$(printf '%s' "$line" | cut -d '=' -f 2-)
        export "$key=$val"
        ;;
      *)
        # skip anything not KEY=VALUE
        ;;
    esac
  done < /tmp/runtime.env
fi

exec "$@"
