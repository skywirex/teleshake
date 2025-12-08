#!/bin/sh
# /app/scripts/teleshake.sh

# Default to 3600 seconds if LOOP_SECONDS is not set
LOOP_SECONDS="${LOOP_SECONDS:-3600}"

# Validate it's a positive integer
if ! echo "$LOOP_SECONDS" | grep -qE '^[0-9]+$'; then
    echo "ERROR: LOOP_SECONDS must be a positive integer. Got: '$LOOP_SECONDS'" >&2
    exit 1
fi

if [ "$LOOP_SECONDS" -lt 1 ]; then
    echo "ERROR: LOOP_SECONDS must be >= 1. Got: $LOOP_SECONDS" >&2
    exit 1
fi

echo "teleshake service started"
echo "Loop interval: ${LOOP_SECONDS} seconds"

# Write PID for OpenRC
echo $$ > /run/teleshake.pid

while :; do
    echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') === Running teleshake (loop=${LOOP_SECONDS}s)"

    /app/venv/bin/python /app/main.py
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo "teleshake completed successfully"
    else
        echo "teleshake failed with exit code $EXIT_CODE"
    fi

    echo "Sleeping ${LOOP_SECONDS} seconds..."
    sleep "$LOOP_SECONDS"
done