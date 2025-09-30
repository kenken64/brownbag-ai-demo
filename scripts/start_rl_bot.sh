#!/bin/bash
# RL Trading Bot Management Script
# Usage: ./start_rl_bot.sh [start|stop|restart|status|logs]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BOT_SCRIPT="$PROJECT_DIR/src/trading_bot.py"
PID_FILE="$PROJECT_DIR/logs/rl_bot.pid"
LOG_FILE="$PROJECT_DIR/logs/rl_bot_main.log"
ERROR_LOG="$PROJECT_DIR/logs/rl_bot_error.log"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

start_bot() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  RL bot is already running (PID: $PID)${NC}"
            return 1
        else
            echo -e "${YELLOW}⚠️  Removing stale PID file${NC}"
            rm "$PID_FILE"
        fi
    fi

    if [ ! -f "$BOT_SCRIPT" ]; then
        echo -e "${RED}❌ Error: Bot script not found at $BOT_SCRIPT${NC}"
        echo -e "${YELLOW}   This script will be implemented in Phase 1 of the roadmap${NC}"
        return 1
    fi

    echo -e "${GREEN}🚀 Starting RL Trading Bot...${NC}"

    # Activate virtual environment if it exists
    if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
        source "$PROJECT_DIR/venv/bin/activate"
    fi

    # Start bot in background
    cd "$PROJECT_DIR"
    nohup python3 "$BOT_SCRIPT" >> "$LOG_FILE" 2>> "$ERROR_LOG" &
    echo $! > "$PID_FILE"

    sleep 2

    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo -e "${GREEN}✅ RL bot started successfully (PID: $(cat "$PID_FILE"))${NC}"
        echo -e "${GREEN}   Logs: $LOG_FILE${NC}"
    else
        echo -e "${RED}❌ Failed to start RL bot. Check logs:${NC}"
        echo -e "${RED}   $ERROR_LOG${NC}"
        rm "$PID_FILE"
        return 1
    fi
}

stop_bot() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}⚠️  RL bot is not running${NC}"
        return 1
    fi

    PID=$(cat "$PID_FILE")

    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  RL bot is not running (removing stale PID file)${NC}"
        rm "$PID_FILE"
        return 1
    fi

    echo -e "${YELLOW}🛑 Stopping RL Trading Bot (PID: $PID)...${NC}"
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
    echo -e "${GREEN}✅ RL bot stopped successfully${NC}"
}

restart_bot() {
    echo -e "${YELLOW}🔄 Restarting RL Trading Bot...${NC}"
    stop_bot
    sleep 2
    start_bot
}

status_bot() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${RED}❌ RL bot is NOT running${NC}"
        return 1
    fi

    PID=$(cat "$PID_FILE")

    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ RL bot is RUNNING${NC}"
        echo -e "   PID: $PID"
        echo -e "   Log: $LOG_FILE"

        # Show bot info if available
        if [ -f "$LOG_FILE" ]; then
            echo -e "\n📊 Recent activity:"
            tail -n 5 "$LOG_FILE"
        fi
    else
        echo -e "${RED}❌ RL bot is NOT running (stale PID file)${NC}"
        rm "$PID_FILE"
        return 1
    fi
}

show_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${YELLOW}⚠️  No log file found${NC}"
        return 1
    fi

    echo -e "${GREEN}📋 RL Bot Logs (tail -f):${NC}"
    echo -e "${GREEN}   Press Ctrl+C to exit${NC}\n"
    tail -f "$LOG_FILE"
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
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the RL trading bot"
        echo "  stop    - Stop the RL trading bot"
        echo "  restart - Restart the RL trading bot"
        echo "  status  - Check bot status"
        echo "  logs    - Tail the bot logs"
        exit 1
        ;;
esac

exit 0