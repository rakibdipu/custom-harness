#!/bin/bash
# Start auto_runner daemon in the background
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

PID_FILE="$DIR/runner.pid"
LOG_FILE="$DIR/logs/auto_runner.log"

mkdir -p "$DIR/logs"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️ Auto-runner is already running with PID $PID"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

echo "🚀 Starting Auto-Runner (30-min lead time scheduler) in background..."
nohup "$DIR/.venv/bin/python" "$DIR/auto_runner.py" "$@" < /dev/null >> "$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

sleep 1
if ps -p "$PID" > /dev/null 2>&1; then
    echo "✅ Auto-runner started successfully! (PID: $PID)"
    echo "📄 Logs: tail -f $LOG_FILE"
    echo "⏹️ Stop anytime with: ./stop_runner.sh"
else
    echo "❌ Failed to start auto-runner. Check $LOG_FILE for details."
    exit 1
fi
