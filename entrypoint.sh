#!/bin/sh

# Start OpenRC
openrc default

# Add service to default runlevel
rc-update add teleshake default 2>/dev/null || true

# Start service with LOOP_SECONDS (fallback to 3600)
echo "Starting teleshake with LOOP_SECONDS=${LOOP_SECONDS:-3600}"
env LOOP_SECONDS="${LOOP_SECONDS:-3600}" rc-service teleshake start

# Become PID 1
exec /sbin/init