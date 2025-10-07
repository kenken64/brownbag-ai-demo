#!/bin/bash

# RL Trading Bot Management Script

PID_FILE="rl_bot.pid"
LOG_DIR="logs"
VENV_PATH="venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to check if bot is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to start the bot
start_bot() {
    if is_running; then
        echo -e "${YELLOW}⚠️  RL Bot is already running (PID: $(cat $PID_FILE))${NC}"
        return 1
    fi

    echo -e "${GREEN}🚀 Starting RL Trading Bot...${NC}"

    # Activate virtual environment if it exists
    if [ -d "$VENV_PATH" ]; then
        source "$VENV_PATH/bin/activate"
    fi

    # Start the bot in background
    nohup python3 rl_trading_bot.py > "$LOG_DIR/rl_bot_output.log" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 2

    if is_running; then
        echo -e "${GREEN}✅ RL Bot started successfully (PID: $(cat $PID_FILE))${NC}"
        echo -e "   View logs: tail -f $LOG_DIR/rl_bot_main.log"
    else
        echo -e "${RED}❌ Failed to start RL Bot${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to stop the bot
stop_bot() {
    if ! is_running; then
        echo -e "${YELLOW}⚠️  RL Bot is not running${NC}"
        return 1
    fi

    PID=$(cat "$PID_FILE")
    echo -e "${YELLOW}⏹️  Stopping RL Bot (PID: $PID)...${NC}"

    kill "$PID"
    sleep 2

    # Force kill if still running
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Forcing shutdown...${NC}"
        kill -9 "$PID"
        sleep 1
    fi

    rm -f "$PID_FILE"
    echo -e "${GREEN}✅ RL Bot stopped${NC}"
}

# Function to restart the bot
restart_bot() {
    echo -e "${GREEN}🔄 Restarting RL Bot...${NC}"
    stop_bot
    sleep 1
    start_bot
}

# Function to show bot status
show_status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✅ RL Bot is running${NC}"
        echo -e "   PID: $PID"
        echo -e "   Uptime: $(ps -p $PID -o etime= | tr -d ' ')"
        echo -e "   Memory: $(ps -p $PID -o rss= | awk '{print int($1/1024)" MB"}')"
        echo -e "   Log: $LOG_DIR/rl_bot_main.log"
    else
        echo -e "${RED}❌ RL Bot is not running${NC}"
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_DIR/rl_bot_main.log" ]; then
        tail -f "$LOG_DIR/rl_bot_main.log"
    else
        echo -e "${RED}❌ Log file not found${NC}"
    fi
}

# Main command handling
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
        show_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the RL Trading Bot"
        echo "  stop    - Stop the RL Trading Bot"
        echo "  restart - Restart the RL Trading Bot"
        echo "  status  - Show bot status"
        echo "  logs    - Show live logs"
        exit 1
        ;;
esac

exit 0
