#!/bin/bash
# Chart Analysis Bot Management Script
# Usage: ./start_chart_bot.sh [start|stop|restart|status]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BOT_SCRIPT="$PROJECT_DIR/src/chart_analysis_bot.py"
PID_FILE="$PROJECT_DIR/logs/chart_bot.pid"
LOG_FILE="$PROJECT_DIR/chart_analysis_bot.log"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

start_bot() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Chart analysis bot is already running (PID: $PID)${NC}"
            return 1
        else
            echo -e "${YELLOW}⚠️  Removing stale PID file${NC}"
            rm "$PID_FILE"
        fi
    fi

    if [ ! -f "$BOT_SCRIPT" ]; then
        echo -e "${RED}❌ Error: Bot script not found at $BOT_SCRIPT${NC}"
        echo -e "${YELLOW}   This script will be implemented in Phase 2 of the roadmap${NC}"
        return 1
    fi

    echo -e "${GREEN}🚀 Starting Chart Analysis Bot...${NC}"

    # Activate virtual environment if it exists
    if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
        source "$PROJECT_DIR/venv/bin/activate"
    fi

    # Start bot in background
    cd "$PROJECT_DIR"
    nohup python3 "$BOT_SCRIPT" >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 2

    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Chart analysis bot started successfully (PID: $(cat "$PID_FILE"))${NC}"
        echo -e "${GREEN}   Logs: $LOG_FILE${NC}"
    else
        echo -e "${RED}❌ Failed to start chart analysis bot. Check logs:${NC}"
        echo -e "${RED}   $LOG_FILE${NC}"
        rm "$PID_FILE"
        return 1
    fi
}

stop_bot() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}⚠️  Chart analysis bot is not running${NC}"
        return 1
    fi

    PID=$(cat "$PID_FILE")

    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Chart analysis bot is not running (removing stale PID file)${NC}"
        rm "$PID_FILE"
        return 1
    fi

    echo -e "${YELLOW}🛑 Stopping Chart Analysis Bot (PID: $PID)...${NC}"
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
    echo -e "${GREEN}✅ Chart analysis bot stopped successfully${NC}"
}

restart_bot() {
    echo -e "${YELLOW}🔄 Restarting Chart Analysis Bot...${NC}"
    stop_bot
    sleep 2
    start_bot
}

status_bot() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${RED}❌ Chart analysis bot is NOT running${NC}"
        return 1
    fi

    PID=$(cat "$PID_FILE")

    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Chart analysis bot is RUNNING${NC}"
        echo -e "   PID: $PID"
        echo -e "   Log: $LOG_FILE"

        # Show bot info if available
        if [ -f "$LOG_FILE" ]; then
            echo -e "\n📊 Recent activity:"
            tail -n 5 "$LOG_FILE"
        fi
    else
        echo -e "${RED}❌ Chart analysis bot is NOT running (stale PID file)${NC}"
        rm "$PID_FILE"
        return 1
    fi
}

# Main command handler
case "$1" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        status_bot
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the chart analysis bot"
        echo "  stop    - Stop the chart analysis bot"
        echo "  restart - Restart the chart analysis bot"
        echo "  status  - Check bot status"
        exit 1
        ;;
esac

exit 0