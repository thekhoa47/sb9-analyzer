#!/bin/sh
set -eu

set -a; . /tmp/runtime.env; set +a

exec "$@"
