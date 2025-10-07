#!/bin/bash

###############################################################################
# MCP Server Startup Script
# AI Crypto Trading Bot - Backend Infrastructure
# Version: 1.0
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Configuration
MCP_PORT="${MCP_SERVER_PORT:-3000}"
PID_FILE="backend/mcp_server.pid"
LOG_FILE="logs/mcp_server.log"
ERROR_LOG_FILE="logs/mcp_server_error.log"

# Create logs directory
mkdir -p logs
mkdir -p backend/database

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if server is running
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

# Start server
start_server() {
    print_info "Starting MCP Server..."

    # Check if already running
    if is_running; then
        print_warning "MCP Server is already running (PID: $(cat $PID_FILE))"
        return 1
    fi

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Creating..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install/update dependencies
    print_info "Installing dependencies..."
    pip install -q -r backend/requirements.txt

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Using .env.example as template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "Please update .env with your configuration"
        else
            print_error ".env.example not found. Please create .env manually"
            return 1
        fi
    fi

    # Load environment variables
    export $(grep -v '^#' .env | xargs)

    # Run migrations
    print_info "Running database migrations..."
    python3 backend/database/migrations.py

    # Start server in background
    print_info "Starting MCP Server on port $MCP_PORT..."
    nohup python3 backend/mcp_server.py > "$LOG_FILE" 2> "$ERROR_LOG_FILE" &

    # Save PID
    echo $! > "$PID_FILE"

    # Wait a moment to check if it started successfully
    sleep 2

    if is_running; then
        print_success "MCP Server started successfully (PID: $(cat $PID_FILE))"
        print_info "Log file: $LOG_FILE"
        print_info "Error log: $ERROR_LOG_FILE"
        print_info "Health check: http://localhost:$MCP_PORT/health"
    else
        print_error "Failed to start MCP Server"
        print_error "Check logs: $ERROR_LOG_FILE"
        return 1
    fi
}

# Stop server
stop_server() {
    print_info "Stopping MCP Server..."

    if ! is_running; then
        print_warning "MCP Server is not running"
        return 1
    fi

    PID=$(cat "$PID_FILE")
    kill "$PID"

    # Wait for process to stop
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    # Force kill if still running
    if ps -p "$PID" > /dev/null 2>&1; then
        print_warning "Process didn't stop gracefully, force killing..."
        kill -9 "$PID"
    fi

    rm -f "$PID_FILE"
    print_success "MCP Server stopped"
}

# Restart server
restart_server() {
    print_info "Restarting MCP Server..."
    stop_server || true
    sleep 2
    start_server
}

# Show server status
show_status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        print_success "MCP Server is RUNNING (PID: $PID)"

        # Check if port is listening
        if command -v lsof &> /dev/null; then
            if lsof -i :"$MCP_PORT" > /dev/null 2>&1; then
                print_success "Port $MCP_PORT is listening"
            else
                print_warning "Port $MCP_PORT is NOT listening"
            fi
        fi

        # Try health check
        if command -v curl &> /dev/null; then
            print_info "Checking health endpoint..."
            curl -s "http://localhost:$MCP_PORT/health" | python3 -m json.tool || true
        fi
    else
        print_warning "MCP Server is NOT running"
    fi
}

# Show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        print_error "Log file not found: $LOG_FILE"
    fi
}

# Show error logs
show_error_logs() {
    if [ -f "$ERROR_LOG_FILE" ]; then
        tail -f "$ERROR_LOG_FILE"
    else
        print_error "Error log file not found: $ERROR_LOG_FILE"
    fi
}

# Test endpoints
test_endpoints() {
    print_info "Testing MCP Server endpoints..."

    if ! is_running; then
        print_error "MCP Server is not running"
        return 1
    fi

    BASE_URL="http://localhost:$MCP_PORT"

    # Test health endpoint
    print_info "Testing /health..."
    curl -s "$BASE_URL/health" | python3 -m json.tool

    # Test bot status
    print_info "Testing /api/bot-status..."
    curl -s "$BASE_URL/api/bot-status" | python3 -m json.tool

    # Test signals endpoint
    print_info "Testing /api/signals/latest..."
    curl -s "$BASE_URL/api/signals/latest" | python3 -m json.tool

    print_success "Endpoint tests complete"
}

# Main script
case "${1:-}" in
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
    errors)
        show_error_logs
        ;;
    test)
        test_endpoints
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|errors|test}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the MCP Server"
        echo "  stop     - Stop the MCP Server"
        echo "  restart  - Restart the MCP Server"
        echo "  status   - Show server status and health"
        echo "  logs     - Tail server logs"
        echo "  errors   - Tail error logs"
        echo "  test     - Test API endpoints"
        exit 1
        ;;
esac

exit 0
