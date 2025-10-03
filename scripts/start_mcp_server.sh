#!/bin/bash

#############################################################################
# MCP Server Management Script
# Manages the Model-Context-Protocol API server
# Commands: start, stop, restart, status, logs
#############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
PID_FILE="$PROJECT_DIR/logs/mcp_server.pid"
LOG_FILE="$PROJECT_DIR/logs/mcp_server.log"
PYTHON_SCRIPT="$PROJECT_DIR/src/mcp_server.py"

# Ensure logs directory exists
mkdir -p "$PROJECT_DIR/logs"

#############################################################################
# Functions
#############################################################################

print_banner() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  🌐 MCP Server Management${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${RED}❌ Virtual environment not found!${NC}"
        echo "   Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # Running
        else
            rm -f "$PID_FILE"  # Stale PID file
            return 1  # Not running
        fi
    fi
    return 1  # Not running
}

start_server() {
    print_banner

    if is_running; then
        echo -e "${YELLOW}⚠️  MCP Server is already running (PID: $(cat $PID_FILE))${NC}"
        exit 0
    fi

    echo -e "${GREEN}🚀 Starting MCP Server...${NC}"

    # Check environment
    check_venv

    if [ ! -f "$PROJECT_DIR/.env" ]; then
        echo -e "${YELLOW}⚠️  No .env file found. Using defaults.${NC}"
    fi

    # Activate virtual environment and start server
    source "$VENV_DIR/bin/activate"

    echo -e "${BLUE}📝 Log file: $LOG_FILE${NC}"

    # Start MCP server in background
    nohup python3 "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1 &

    # Save PID
    echo $! > "$PID_FILE"

    # Wait a moment to check if it started successfully
    sleep 2

    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✅ MCP Server started successfully!${NC}"
        echo -e "${GREEN}   PID: $PID${NC}"
        echo -e "${GREEN}   Port: 3000 (default)${NC}"
        echo -e "${GREEN}   API: http://localhost:3000/api/v1/info${NC}"
        echo ""
        echo -e "${BLUE}💡 Useful commands:${NC}"
        echo "   ./scripts/start_mcp_server.sh status    # Check status"
        echo "   ./scripts/start_mcp_server.sh logs      # View logs"
        echo "   ./scripts/start_mcp_server.sh stop      # Stop server"
    else
        echo -e "${RED}❌ Failed to start MCP Server${NC}"
        echo -e "${YELLOW}Check logs: tail -f $LOG_FILE${NC}"
        rm -f "$PID_FILE"
        exit 1
    fi
}

stop_server() {
    print_banner

    if ! is_running; then
        echo -e "${YELLOW}⚠️  MCP Server is not running${NC}"
        rm -f "$PID_FILE"
        exit 0
    fi

    PID=$(cat "$PID_FILE")
    echo -e "${YELLOW}🛑 Stopping MCP Server (PID: $PID)...${NC}"

    # Graceful shutdown
    kill "$PID" 2>/dev/null || true

    # Wait for shutdown (max 10 seconds)
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    # Force kill if still running
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Forcing shutdown...${NC}"
        kill -9 "$PID" 2>/dev/null || true
    fi

    rm -f "$PID_FILE"
    echo -e "${GREEN}✅ MCP Server stopped${NC}"
}

restart_server() {
    print_banner
    echo -e "${BLUE}🔄 Restarting MCP Server...${NC}"
    echo ""

    stop_server
    sleep 1
    start_server
}

show_status() {
    print_banner

    if is_running; then
        PID=$(cat "$PID_FILE")

        # Get memory usage
        MEM=$(ps -o rss= -p "$PID" | awk '{printf "%.1f MB", $1/1024}')

        # Get CPU usage
        CPU=$(ps -o %cpu= -p "$PID" | awk '{print $1"%"}')

        # Get uptime
        START_TIME=$(ps -o lstart= -p "$PID")

        echo -e "${GREEN}✅ MCP Server is RUNNING${NC}"
        echo ""
        echo -e "${BLUE}Process Information:${NC}"
        echo "   PID:        $PID"
        echo "   Memory:     $MEM"
        echo "   CPU:        $CPU"
        echo "   Started:    $START_TIME"
        echo ""
        echo -e "${BLUE}Configuration:${NC}"
        echo "   Port:       3000 (default)"
        echo "   Log File:   $LOG_FILE"
        echo "   PID File:   $PID_FILE"
        echo ""
        echo -e "${BLUE}API Endpoints:${NC}"
        echo "   Info:       http://localhost:3000/api/v1/info"
        echo "   Health:     http://localhost:3000/api/v1/health"
        echo "   Signals:    http://localhost:3000/api/v1/signals"
        echo "   Trades:     http://localhost:3000/api/v1/trades"
        echo ""

        # Test API
        if command -v curl &> /dev/null; then
            echo -e "${BLUE}Testing API connection...${NC}"
            if curl -s http://localhost:3000/api/v1/health > /dev/null 2>&1; then
                echo -e "${GREEN}✅ API is responding${NC}"
            else
                echo -e "${YELLOW}⚠️  API not responding (server may still be starting)${NC}"
            fi
        fi

    else
        echo -e "${RED}❌ MCP Server is NOT running${NC}"
        echo ""
        echo -e "${YELLOW}💡 Start it with:${NC}"
        echo "   ./scripts/start_mcp_server.sh start"
    fi
}

show_logs() {
    print_banner

    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${YELLOW}⚠️  No log file found${NC}"
        exit 1
    fi

    echo -e "${BLUE}📋 MCP Server Logs (last 50 lines):${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    tail -n 50 "$LOG_FILE"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}💡 Follow live logs:${NC}"
    echo "   tail -f $LOG_FILE"
}

show_help() {
    print_banner
    echo ""
    echo -e "${BLUE}Usage:${NC}"
    echo "   ./scripts/start_mcp_server.sh [command]"
    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo "   start     - Start MCP Server"
    echo "   stop      - Stop MCP Server"
    echo "   restart   - Restart MCP Server"
    echo "   status    - Show server status"
    echo "   logs      - Show recent logs"
    echo "   help      - Show this help message"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "   ./scripts/start_mcp_server.sh start"
    echo "   ./scripts/start_mcp_server.sh status"
    echo "   ./scripts/start_mcp_server.sh logs"
    echo ""
}

#############################################################################
# Main Script
#############################################################################

case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
