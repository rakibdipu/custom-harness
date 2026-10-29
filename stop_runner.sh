#!/bin/bash
# Stop auto_runner daemon cleanly
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$DIR/runner.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "⚠️ Auto-runner is not running (no PID file found)."
    exit 0
fi

PID=$(cat "$PID_FILE")
if ps -p "$PID" > /dev/null 2>&1; then
    echo "⏹️ Stopping Auto-runner (PID $PID)..."
    kill "$PID"
    sleep 1
    if ps -p "$PID" > /dev/null 2>&1; then
        kill -9 "$PID"
    fi
    rm -f "$PID_FILE"
    echo "✅ Auto-runner stopped."
else
    echo "⚠️ Process $PID not found. Cleaning up stale PID file."
    rm -f "$PID_FILE"
fi
