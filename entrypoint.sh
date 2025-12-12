#!/bin/sh
set -eu

# --- 1. STARTING ---
echo "[INFO] Entrypoint starting..."
echo "[INFO] LOOP_SECONDS=${LOOP_SECONDS:-3600}"

# --- 2. GET NODE_API_KEY ---
CONFIG_FILE="/app/config.json"
NODE_API_KEY=""

if [ -f "$CONFIG_FILE" ]; then
    # Use grep and sed to locate and extract the value of NODE_API_KEY
    # Assumes NODE_API_KEY is on its own line and has the format: "NODE_API_KEY": "value",
    NODE_API_KEY=$(grep '"NODE_API_KEY"' "$CONFIG_FILE" | sed -E 's/.*: *"(.*)",?/\1/')

    if [ -z "$NODE_API_KEY" ]; then
        echo "[ERROR] NODE_API_KEY not found or is empty in $CONFIG_FILE." >&2
        exit 1
    else
        echo "[INFO] Extracted NODE_API_KEY."
    fi
else
    echo "[ERROR] Config file $CONFIG_FILE not found." >&2
        exit 1
fi

# --- 3. CHECK HSD VIA HTTP API ---

# API endpoint

ENDPOINT="http://x:${NODE_API_KEY}@127.0.0.1:12037"

echo "--- Starting HSD API check at 127.0.0.1:12037 ---"

# Optional -sf flag: Silent (no error output) and Fail (returns an error code if the HTTP request fails)
# Requires curl to be installed in the image

until curl -sf "$ENDPOINT"; do
  echo "Waiting for hsd...";
  sleep 3;
done;

echo "hsd ready -> starting Teleshake";

# --- 4. Start teleshake loop script ---
exec /app/scripts/teleshake.sh