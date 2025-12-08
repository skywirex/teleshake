#!/bin/sh
set -eu

echo "[INFO] Entrypoint starting..."
echo "[INFO] LOOP_SECONDS=${LOOP_SECONDS:-3600}"

# Start teleshake loop script
exec /app/scripts/teleshake.sh