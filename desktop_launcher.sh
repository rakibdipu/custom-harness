#!/bin/bash
# Desktop Launcher for Custom Harness Auto-Runner
DIR="/home/dipu/PROJECT/Github/custom-harness"
cd "$DIR"

clear
echo "========================================================================"
echo "⚡ CUSTOM HARNESS — AUTO-RUNNER DESKTOP MANAGER"
echo "========================================================================"
echo ""

PID_FILE="$DIR/runner.pid"
LOG_FILE="$DIR/logs/auto_runner.log"

is_running=false
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        is_running=true
    fi
fi

if [ "$is_running" = true ]; then
    echo "🟢 Status: ACTIVE & RUNNING in Background (PID: $PID)"
else
    echo "🟡 Status: Not currently running. Starting it now..."
    "$DIR/start_runner.sh"
    echo ""
fi

echo "📅 Today's Automation Schedule:"
echo "------------------------------------------------------------------------"
"$DIR/.venv/bin/python" "$DIR/auto_runner.py" --list 2>/dev/null

echo ""
echo "------------------------------------------------------------------------"
echo "Options:"
echo "  [1] Stream Live Real-Time Logs"
echo "  [2] Post a Reel Right Now (Test/Instant)"
echo "  [3] Pre-bake Buffer Videos Now"
echo "  [4] Restart Auto-Runner"
echo "  [5] Stop Auto-Runner"
echo "  [Enter] Keep running in background and close this window"
echo "------------------------------------------------------------------------"
read -r -p "Enter choice [1-5 or Enter]: " choice

case "$choice" in
    1)
        echo ""
        echo "📋 Streaming live logs (Press Ctrl+C to exit log view)..."
        echo "----------------------------------------------------"
        tail -n 30 -f "$LOG_FILE"
        ;;
    2)
        echo ""
        echo "Select account to post:"
        echo "  [1] StoryVault"
        echo "  [2] MindEdge"
        echo "  [3] TooReal Facts"
        read -r -p "Select [1-3]: " acc_c
        acc="storytelling"
        [ "$acc_c" = "2" ] && acc="psychology_mindset"
        [ "$acc_c" = "3" ] && acc="comic_viral"
        echo "🚀 Posting for $acc now..."
        "$DIR/.venv/bin/python" "$DIR/main.py" --account "$acc"
        read -r -p "Press Enter to finish..."
        ;;
    3)
        echo "📦 Pre-generating buffer videos..."
        "$DIR/.venv/bin/python" "$DIR/main.py" --prebake
        read -r -p "Press Enter to finish..."
        ;;
    4)
        echo "🔄 Restarting..."
        "$DIR/stop_runner.sh"
        sleep 1
        "$DIR/start_runner.sh"
        read -r -p "Press Enter to finish..."
        ;;
    5)
        "$DIR/stop_runner.sh"
        read -r -p "Press Enter to finish..."
        ;;
    *)
        echo "✔ Auto-runner continues to run quietly in background. Goodbye!"
        sleep 1
        ;;
esac
