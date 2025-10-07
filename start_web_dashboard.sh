#!/bin/bash

# AI Crypto Trading Bot - Web Dashboard Startup Script

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PID_FILE="web_dashboard.pid"
LOG_FILE="web_dashboard.log"

# Function to start the dashboard
start_dashboard() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}Web dashboard is already running (PID: $PID)${NC}"
            return 1
        else
            rm "$PID_FILE"
        fi
    fi

    echo -e "${GREEN}Starting web dashboard...${NC}"

    # Check if virtual environment exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    # Start the dashboard in the background
    nohup python3 web_dashboard.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 2

    # Verify it's running
    if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo -e "${GREEN}Web dashboard started successfully!${NC}"
        echo -e "${GREEN}PID: $(cat $PID_FILE)${NC}"
        echo -e "${GREEN}Access dashboard at: http://localhost:5000${NC}"
        echo -e "${YELLOW}Check logs: tail -f $LOG_FILE${NC}"
    else
        echo -e "${RED}Failed to start web dashboard${NC}"
        echo -e "${YELLOW}Check logs: tail $LOG_FILE${NC}"
        rm "$PID_FILE"
        return 1
    fi
}

# Function to stop the dashboard
stop_dashboard() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}Web dashboard is not running${NC}"
        return 1
    fi

    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping web dashboard (PID: $PID)...${NC}"
        kill "$PID"
        sleep 2

        # Force kill if still running
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}Force killing process...${NC}"
            kill -9 "$PID"
        fi

        rm "$PID_FILE"
        echo -e "${GREEN}Web dashboard stopped${NC}"
    else
        echo -e "${YELLOW}Process not found, cleaning up PID file${NC}"
        rm "$PID_FILE"
    fi
}

# Function to restart the dashboard
restart_dashboard() {
    echo -e "${YELLOW}Restarting web dashboard...${NC}"
    stop_dashboard
    sleep 2
    start_dashboard
}

# Function to check status
status_dashboard() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}Web dashboard is running (PID: $PID)${NC}"
            echo -e "${GREEN}URL: http://localhost:5000${NC}"
        else
            echo -e "${RED}Web dashboard is not running (stale PID file)${NC}"
            rm "$PID_FILE"
        fi
    else
        echo -e "${RED}Web dashboard is not running${NC}"
    fi
}

# Function to view logs
view_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo -e "${RED}Log file not found${NC}"
    fi
}

# Main script logic
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
    status)
        status_dashboard
        ;;
    logs)
        view_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the web dashboard"
        echo "  stop    - Stop the web dashboard"
        echo "  restart - Restart the web dashboard"
        echo "  status  - Check dashboard status"
        echo "  logs    - View dashboard logs (tail -f)"
        exit 1
        ;;
esac

exit 0
