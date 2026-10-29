#!/bin/bash
# Check status of auto_runner daemon
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$DIR/runner.pid"
LOG_FILE="$DIR/logs/auto_runner.log"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        MEM=$(ps -o rss= -p "$PID" | awk '{printf "%.1f MB", $1/1024}')
        TIME=$(ps -o etime= -p "$PID" | tr -d ' ')
        echo "🟢 Auto-Runner is ACTIVE"
        echo "   PID: $PID"
        echo "   RAM: $MEM"
        echo "   Uptime: $TIME"
        echo ""
        echo "📋 Latest Logs (tail -n 12):"
        echo "----------------------------------------------------"
        tail -n 12 "$LOG_FILE" 2>/dev/null
        exit 0
    fi
fi

echo "🔴 Auto-Runner is NOT running."
echo "   Start it with: ./start_runner.sh"
