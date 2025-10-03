#!/bin/bash
# Master Script to Restart All Services
# Usage: ./restart_all.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AI Crypto Trading Bot - Master Restart Script   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to display status
display_status() {
    local service=$1
    local status=$2

    if [ "$status" == "success" ]; then
        echo -e "${GREEN}✅ $service${NC}"
    elif [ "$status" == "warning" ]; then
        echo -e "${YELLOW}⚠️  $service${NC}"
    else
        echo -e "${RED}❌ $service${NC}"
    fi
}

# Stop all services
echo -e "${YELLOW}🛑 Stopping all services...${NC}"
echo ""

echo -e "1️⃣  Stopping RL Trading Bot..."
"$SCRIPT_DIR/start_rl_bot.sh" stop
RL_STOP=$?

echo ""
echo -e "2️⃣  Stopping Chart Analysis Bot..."
"$SCRIPT_DIR/start_chart_bot.sh" stop
CHART_STOP=$?

echo ""
echo -e "3️⃣  Stopping Web Dashboard..."
"$SCRIPT_DIR/start_web_dashboard.sh" stop
WEB_STOP=$?

echo ""
echo -e "4️⃣  Stopping MCP Server..."
"$SCRIPT_DIR/start_mcp_server.sh" stop
MCP_STOP=$?

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Wait for clean shutdown
echo -e "${YELLOW}⏳ Waiting for clean shutdown...${NC}"
sleep 3
echo ""

# Start all services
echo -e "${GREEN}🚀 Starting all services...${NC}"
echo ""

echo -e "1️⃣  Starting RL Trading Bot..."
"$SCRIPT_DIR/start_rl_bot.sh" start
RL_START=$?

echo ""
echo -e "2️⃣  Starting Chart Analysis Bot..."
"$SCRIPT_DIR/start_chart_bot.sh" start
CHART_START=$?

echo ""
echo -e "3️⃣  Starting Web Dashboard..."
"$SCRIPT_DIR/start_web_dashboard.sh" start
WEB_START=$?

echo ""
echo -e "4️⃣  Starting MCP Server..."
"$SCRIPT_DIR/start_mcp_server.sh" start
MCP_START=$?

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Summary
echo -e "${BLUE}📊 Service Status Summary:${NC}"
echo ""

if [ $RL_START -eq 0 ]; then
    display_status "RL Trading Bot" "success"
else
    display_status "RL Trading Bot" "error"
fi

if [ $CHART_START -eq 0 ]; then
    display_status "Chart Analysis Bot" "success"
else
    display_status "Chart Analysis Bot" "error"
fi

if [ $WEB_START -eq 0 ]; then
    display_status "Web Dashboard" "success"
else
    display_status "Web Dashboard" "error"
fi

if [ $MCP_START -eq 0 ]; then
    display_status "MCP Server" "success"
else
    display_status "MCP Server" "error"
fi

# Get ports from .env
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
if [ -f "$PROJECT_DIR/.env" ]; then
    DASHBOARD_PORT=$(grep DASHBOARD_PORT "$PROJECT_DIR/.env" | cut -d '=' -f2)
    DASHBOARD_PORT=${DASHBOARD_PORT:-5000}
    MCP_PORT=$(grep MCP_PORT "$PROJECT_DIR/.env" | cut -d '=' -f2)
    MCP_PORT=${MCP_PORT:-3000}

    echo ""
    echo -e "${GREEN}🌐 Dashboard URL: http://localhost:$DASHBOARD_PORT${NC}"
    echo -e "${GREEN}🔌 MCP API URL: http://localhost:$MCP_PORT/api/v1/info${NC}"
fi

echo ""
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Exit with error if any service failed
if [ $RL_START -ne 0 ] || [ $CHART_START -ne 0 ] || [ $WEB_START -ne 0 ] || [ $MCP_START -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Some services failed to start. Check logs for details.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All services restarted successfully!${NC}"
exit 0