#!/bin/bash

# AI Crypto Trading Bot - Installation Script
# Automated setup for all dependencies and configuration

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   AI-Driven Cryptocurrency Trading Bot - Setup          ║"
echo "║   Automated Installation Script                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo -e "${GREEN}✅ Python $PYTHON_VERSION detected${NC}"
else
    echo -e "${RED}❌ Python 3.9 or higher required. Current: $PYTHON_VERSION${NC}"
    exit 1
fi

# Create virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists. Skipping.${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Upgrade pip
echo -e "\n${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✅ pip upgraded${NC}"

# Install dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create necessary directories
echo -e "\n${YELLOW}Creating required directories...${NC}"
mkdir -p logs
mkdir -p charts
mkdir -p backups
echo -e "${GREEN}✅ Directories created${NC}"

# Initialize database
echo -e "\n${YELLOW}Initializing database...${NC}"
python3 database.py
echo -e "${GREEN}✅ Database initialized${NC}"

# Create .env if it doesn't exist
echo -e "\n${YELLOW}Checking configuration file...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created from template${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env file with your API keys!${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists. Skipping.${NC}"
fi

# Make scripts executable
echo -e "\n${YELLOW}Making scripts executable...${NC}"
chmod +x start_rl_bot.sh
chmod +x start_chart_bot.sh
chmod +x setup.sh
echo -e "${GREEN}✅ Scripts are now executable${NC}"

# Platform-specific notes
echo -e "\n${YELLOW}Platform-specific setup notes:${NC}"
OS_TYPE=$(uname -s)
case "$OS_TYPE" in
    Darwin*)
        echo -e "${BLUE}macOS detected${NC}"
        echo -e "  Optional: Install TA-Lib for better performance:"
        echo -e "    brew install ta-lib"
        echo -e "    pip install TA-Lib"
        ;;
    Linux*)
        echo -e "${BLUE}Linux detected${NC}"
        echo -e "  Optional: Install TA-Lib for better performance:"
        echo -e "    See SETUP.md for Linux installation instructions"
        ;;
    *)
        echo -e "${BLUE}$OS_TYPE detected${NC}"
        echo -e "  See SETUP.md for platform-specific instructions"
        ;;
esac

# Summary
echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Installation Complete!                                 ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${YELLOW}📋 NEXT STEPS:${NC}"
echo -e "${BLUE}1.${NC} Configure your API keys:"
echo -e "   ${YELLOW}nano .env${NC}  # or use your favorite editor"
echo -e ""
echo -e "${BLUE}2.${NC} Set required environment variables:"
echo -e "   - BINANCE_API_KEY (required)"
echo -e "   - BINANCE_SECRET_KEY (required)"
echo -e "   - OPENAI_API_KEY (optional, for chart analysis)"
echo -e "   - NEWS_API_KEY (optional, for market news)"
echo -e ""
echo -e "${BLUE}3.${NC} Choose cost optimization mode:"
echo -e "   ${YELLOW}python3 configure_costs.py cost-saving${NC}  # FREE mode"
echo -e "   ${YELLOW}python3 configure_costs.py premium${NC}       # OpenAI mode ($1-3/month)"
echo -e ""
echo -e "${BLUE}4.${NC} Test on testnet first (IMPORTANT!):"
echo -e "   Ensure ${YELLOW}USE_TESTNET=true${NC} in .env"
echo -e ""
echo -e "${BLUE}5.${NC} Start the RL Trading Bot:"
echo -e "   ${YELLOW}./start_rl_bot.sh start${NC}"
echo -e ""
echo -e "${BLUE}6.${NC} (Optional) Start Chart Analysis Bot:"
echo -e "   ${YELLOW}./start_chart_bot.sh start${NC}"
echo -e ""
echo -e "${BLUE}7.${NC} Monitor the logs:"
echo -e "   ${YELLOW}./start_rl_bot.sh logs${NC}"
echo -e ""

echo -e "${YELLOW}📚 For detailed setup instructions, see:${NC}"
echo -e "   ${BLUE}SETUP.md${NC}"
echo -e ""

echo -e "${YELLOW}⚠️  IMPORTANT SAFETY REMINDERS:${NC}"
echo -e "   ${RED}• ALWAYS test on testnet first${NC}"
echo -e "   ${RED}• Start with small position sizes (1-2%)${NC}"
echo -e "   ${RED}• Never trade with money you can't afford to lose${NC}"
echo -e "   ${RED}• Disable withdrawal permissions on Binance API${NC}"
echo -e "   ${RED}• Use IP whitelist for additional security${NC}"
echo -e ""

echo -e "${GREEN}Good luck with your trading! 🚀${NC}"
