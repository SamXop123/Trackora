#!/usr/bin/env bash
set -e

# Start background daemon if not already running
if ! pgrep -f "trackora-daemon" > /dev/null 2>&1; then
    echo "[Trackora Container] Starting background tracking daemon..."
    trackora-daemon &
    sleep 0.5
fi

# Execute the container command (default: trackora-gui)
exec "$@"
