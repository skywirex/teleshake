#!/bin/sh
# /app/scripts/teleshake.sh

# Configurable interval — defaults to 3600 seconds (1 hour)
LOOP_SECONDS="${LOOP_SECONDS:-3600}"

# Validate it's a positive integer
if ! echo "$LOOP_SECONDS" | grep -Eq '^[0-9]+$'; then
    echo "ERROR: LOOP_SECONDS must be a positive integer. Got: '$LOOP_SECONDS'" >&2
    exit 1
fi

echo "teleshake started — running every ${LOOP_SECONDS} seconds"

while true; do
    echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') === Running main.py (loop=${LOOP_SECONDS}s)"

    /app/venv/bin/python /app/main.py
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo "main.py completed successfully"
    else
        echo "main.py failed with exit code $EXIT_CODE"
    fi

    echo "Sleeping ${LOOP_SECONDS} seconds..."
    sleep "$LOOP_SECONDS"
done