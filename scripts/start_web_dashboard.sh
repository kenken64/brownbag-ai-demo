#!/bin/bash
# Web Dashboard Management Script
# Usage: ./start_web_dashboard.sh [start|stop|restart]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DASHBOARD_SCRIPT="$PROJECT_DIR/src/web_dashboard.py"
PID_FILE="$PROJECT_DIR/logs/web_dashboard.pid"
LOG_FILE="$PROJECT_DIR/web_dashboard.log"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

start_dashboard() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Web dashboard is already running (PID: $PID)${NC}"
            PORT=$(grep DASHBOARD_PORT "$PROJECT_DIR/.env" | cut -d '=' -f2)
            PORT=${PORT:-5000}
            echo -e "${GREEN}   Access at: http://localhost:$PORT${NC}"
            return 1
        else
            echo -e "${YELLOW}⚠️  Removing stale PID file${NC}"
            rm "$PID_FILE"
        fi
    fi

    if [ ! -f "$DASHBOARD_SCRIPT" ]; then
        echo -e "${RED}❌ Error: Dashboard script not found at $DASHBOARD_SCRIPT${NC}"
        echo -e "${YELLOW}   This script will be implemented in Phase 5 of the roadmap${NC}"
        return 1
    fi

    echo -e "${GREEN}🚀 Starting Web Dashboard...${NC}"

    # Activate virtual environment if it exists
    if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
        source "$PROJECT_DIR/venv/bin/activate"
    fi

    # Start dashboard in background
    cd "$PROJECT_DIR"
    nohup python3 "$DASHBOARD_SCRIPT" >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 3

    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        PORT=$(grep DASHBOARD_PORT "$PROJECT_DIR/.env" | cut -d '=' -f2)
        PORT=${PORT:-5000}

        echo -e "${GREEN}✅ Web dashboard started successfully (PID: $(cat "$PID_FILE"))${NC}"
        echo -e "${GREEN}   Access at: http://localhost:$PORT${NC}"
        echo -e "${GREEN}   Logs: $LOG_FILE${NC}"
    else
        echo -e "${RED}❌ Failed to start web dashboard. Check logs:${NC}"
        echo -e "${RED}   $LOG_FILE${NC}"
        rm "$PID_FILE"
        return 1
    fi
}

stop_dashboard() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}⚠️  Web dashboard is not running${NC}"
        return 1
    fi

    PID=$(cat "$PID_FILE")

    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Web dashboard is not running (removing stale PID file)${NC}"
        rm "$PID_FILE"
        return 1
    fi

    echo -e "${YELLOW}🛑 Stopping Web Dashboard (PID: $PID)...${NC}"
    kill "$PID"

    # Wait for graceful shutdown
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    # Force kill if still running
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Forcing shutdown...${NC}"
        kill -9 "$PID"
    fi

    rm "$PID_FILE"
    echo -e "${GREEN}✅ Web dashboard stopped successfully${NC}"
}

restart_dashboard() {
    echo -e "${YELLOW}🔄 Restarting Web Dashboard...${NC}"
    stop_dashboard
    sleep 2
    start_dashboard
}

# Main command handler
case "$1" in
    start)
        start_dashboard
        ;;
    stop)
        stop_dashboard
        ;;
    restart)
        restart_dashboard
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the web dashboard"
        echo "  stop    - Stop the web dashboard"
        echo "  restart - Restart the web dashboard"
        exit 1
        ;;
esac

exit 0