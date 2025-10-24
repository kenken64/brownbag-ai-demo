# AI Cryptocurrency Trading System - Setup Guide

## Project Overview

This is an AI-powered cryptocurrency trading system targeting Binance Futures. The system consists of multiple components working together to provide automated trading with AI-enhanced decision making and market protection.

## System Architecture

The system uses a **four-component architecture** with distributed AI agent development:

```
┌─────────────────────────────────────────────────────────────┐
│                   MAIN TRADING SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│  1. RL-Enhanced Trading Bot (Q-learning)                    │
│  2. Chart Analysis Bot (OpenAI GPT-4o)                       │
│  3. Web Dashboard (Real-time monitoring)                     │
│  4. MCP Server (Database API layer)                          │
└─────────────────────────────────────────────────────────────┘
                              +
┌─────────────────────────────────────────────────────────────┐
│              CREWAI MARKET SPIKE AGENT (NEW)                 │
├─────────────────────────────────────────────────────────────┤
│  • Market Scanner Agent (Spike detection)                    │
│  • Market Guardian Agent (Circuit breaker)                   │
│  • Context Analyzer Agent (Intelligence)                     │
│  • Risk Assessment Agent (Risk management)                   │
│  • Strategy Executor Agent (Trade execution)                 │
└─────────────────────────────────────────────────────────────┘
```

## Development Team Structure

### 🎨 Frontend Developer Agent
**Assigned Component:** Web Dashboard
**Task Reference:** PRPs/ai-crypto-trading-bot.md (Section 3.3 Web Dashboard)
**Responsibilities:**
- Build real-time web dashboard using Flask
- Implement 22+ UI components for monitoring
- Create responsive mobile-friendly interface
- Integrate WebSocket for live updates
- Build market news section with pagination
- Implement circuit breaker status display

### ⚙️ Backend Developer Agent
**Assigned Component:** MCP Server + Database Layer
**Task Reference:** PRPs/ai-crypto-trading-bot.md (Section 3.4 MCP Server)
**Responsibilities:**
- Build RESTful API layer for database operations
- Implement data aggregation services
- Create query optimization layer
- Build connection pooling and transaction handling
- Implement caching layer
- Database schema design (SQLite)

### 📈 Trading Development Agent
**Assigned Component:** RL-Enhanced Trading Bot + Chart Analysis Bot
**Task Reference:** PRPs/ai-crypto-trading-bot.md (Sections 3.1 & 3.2)
**Responsibilities:**
- Implement Q-learning reinforcement learning model
- Build technical indicator processing (MACD, RSI, VWAP, EMA, etc.)
- Create weighted signal system
- Integrate Binance Futures API
- Implement position management logic
- Build chart analysis with OpenAI GPT-4o
- Create retraining system

### 🤖 AI Developer Agent
**Assigned Component:** CrewAI Market Spike Agent with Circuit Breaker
**Task Reference:** PRPs/crewai-market-spike-agent-circuit-breaker.md
**Responsibilities:**
- Build 5 specialized CrewAI agents
- Implement Market Guardian (circuit breaker) for crash protection
- Create spike detection algorithms
- Build context analysis with news/social sentiment
- Implement risk assessment logic
- Create strategy executor
- Integrate with main trading system

## Technology Stack

### Backend
- **Python 3.9+** (required)
- **Trading & Market Data:**
  - `python-binance` - Binance Futures API
  - `ccxt` - Exchange connectivity
  - `ta-lib` - Technical indicators (with pandas fallback)
- **Machine Learning:**
  - `numpy`, `pandas` - Data processing
  - Custom Q-learning implementation
  - `crewai` - Multi-agent framework (for spike agent)
- **AI Integration:**
  - `openai` - GPT-4o API
  - `anthropic` - Claude API (optional)
- **Web Framework:**
  - `Flask` - Web dashboard
  - `Flask-CORS` - Cross-origin support
- **Database:**
  - `sqlite3` - Primary database
- **Visualization:**
  - `mplfinance` - Candlestick charts
  - `matplotlib` - Chart generation

### Frontend
- Vanilla JavaScript or lightweight framework
- Chart.js or TradingView widgets
- WebSocket (Socket.IO) for real-time updates
- Bootstrap or Tailwind CSS
- Mobile-responsive design

### External APIs
- **Binance Futures API** (required)
- **OpenAI API** - GPT-4o (optional in cost-saving mode)
- **NewsAPI.org** (optional for news feature)
- **CoinGecko API** (FREE - cross-asset data)
- **Fear & Greed Index API** (FREE)

## Prerequisites

### 1. API Keys Required

#### Binance API Keys
1. Create account at [Binance.com](https://www.binance.com)
2. Navigate to API Management page
3. **IMPORTANT:** Enable "Futures" permission
4. Configure IP whitelist (recommended for security)
5. Enable withdrawal lock
6. Store keys in `.env` file

#### OpenAI API Keys (Optional)
1. Create account at [platform.openai.com](https://platform.openai.com)
2. Generate API key
3. Verify GPT-4o access
4. Monitor credit balance
5. Store in `.env` file

#### NewsAPI Keys (Optional)
1. Register at [newsapi.org](https://newsapi.org)
2. Free tier: 1000 requests/day
3. Generate API key
4. Store in `.env` file

### 2. System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Disk: 10GB
- Network: Stable low-latency connection to exchanges

**Recommended:**
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 20GB SSD
- Network: Dedicated connection with <100ms to Binance

### 3. Platform-Specific Setup

#### macOS
```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install TA-Lib
brew install ta-lib

# Install Python 3.9+
brew install python@3.9
```

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt-get update

# Install dependencies
sudo apt-get install python3.9 python3-pip python3-venv build-essential

# Install TA-Lib
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
```

#### Windows
```powershell
# Install Python 3.9+ from python.org

# Download TA-Lib wheel file
# Visit: https://github.com/cgohlke/talib-build/releases
# Download appropriate .whl file for your Python version

# Install TA-Lib
pip install TA_Lib-0.4.XX-cpXX-cpXX-win_amd64.whl
```

## Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd brownbag-ai-demo
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows:
.\venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Install main dependencies
pip install -r requirements.txt

# If TA-Lib installation fails, system will fallback to pandas indicators
```

### 4. Configure Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your API keys
nano .env  # or use your preferred editor
```

### Example `.env` Configuration:
```bash
# Binance API Configuration
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
TESTNET=false  # Set to true for testing

# OpenAI Configuration (Optional)
OPENAI_API_KEY=your_openai_api_key_here

# NewsAPI Configuration (Optional)
NEWS_API_KEY=your_newsapi_key_here

# Cost Optimization
USE_LOCAL_SENTIMENT=true  # true = FREE mode, false = OpenAI mode

# Dashboard Security
BOT_CONTROL_PIN=123456  # 6-digit PIN for dashboard

# Trading Configuration
TRADING_PAIR=SUIUSDC
LEVERAGE=50
POSITION_PERCENTAGE=5  # Start small! 5% recommended
CHECK_INTERVAL=60  # seconds
MIN_SIGNAL_THRESHOLD=3

# Circuit Breaker Configuration (CrewAI Agent)
CIRCUIT_BREAKER_ENABLED=true
BTC_DUMP_THRESHOLD_1H=15.0  # percent
ETH_DUMP_THRESHOLD_1H=15.0
MARKET_DUMP_THRESHOLD_4H=20.0
```

### 5. Initialize Database
```bash
# Database will be created automatically on first run
# Tables: signals, trades, bot_status, market_context, etc.
```

## Project Structure

```
brownbag-ai-demo/
├── PRPs/                          # Product Requirements Documents
│   ├── ai-crypto-trading-bot.md
│   └── crewai-market-spike-agent-circuit-breaker.md
├── venv/                          # Virtual environment
├── trading_bot/                   # Main trading bot (to be created)
│   ├── rl_trading_bot.py         # RL-enhanced trading engine
│   ├── chart_analysis_bot.py     # OpenAI chart analysis
│   ├── retrain_rl_model.py       # Model retraining system
│   └── models/                    # Q-learning models
├── web_dashboard/                 # Web dashboard (to be created)
│   ├── app.py                     # Flask application
│   ├── templates/                 # HTML templates
│   ├── static/                    # CSS/JS/images
│   └── api/                       # REST API endpoints
├── mcp_server/                    # MCP Server (to be created)
│   ├── server.py                  # Database API server
│   ├── routes/                    # API routes
│   └── services/                  # Data aggregation services
├── crewai_agent/                  # CrewAI Spike Agent (to be created)
│   ├── agents/                    # Agent definitions
│   │   ├── market_scanner.py
│   │   ├── market_guardian.py    # Circuit breaker
│   │   ├── context_analyzer.py
│   │   ├── risk_assessor.py
│   │   └── strategy_executor.py
│   ├── tasks/                     # Task definitions
│   ├── tools/                     # Custom tools
│   │   ├── binance_tools.py
│   │   ├── circuit_breaker_tools.py
│   │   └── analysis_tools.py
│   └── crew_config.py             # Crew configuration
├── scripts/                       # Utility scripts (to be created)
│   ├── start_rl_bot.sh
│   ├── start_chart_bot.sh
│   ├── start_web_dashboard.sh
│   ├── restart_all.sh
│   └── configure_costs.py
├── logs/                          # Log files
├── .env                           # Environment variables (create from .env.example)
├── .env.example                   # Example environment file
├── requirements.txt               # Python dependencies
├── trading_bot.db                 # SQLite database (auto-created)
├── CLAUDE.md                      # Project instructions
└── README-SETUP.md                # This file
```

## Running the System

### Option 1: Start Individual Components

#### 1. RL Trading Bot
```bash
./scripts/start_rl_bot.sh start
./scripts/start_rl_bot.sh status   # Check status
./scripts/start_rl_bot.sh logs     # View logs
./scripts/start_rl_bot.sh stop     # Stop bot
```

#### 2. Chart Analysis Bot
```bash
./scripts/start_chart_bot.sh start
./scripts/start_chart_bot.sh status
./scripts/start_chart_bot.sh stop
```

#### 3. Web Dashboard
```bash
./scripts/start_web_dashboard.sh start
# Access at: http://localhost:5000
```

#### 4. MCP Server
```bash
cd mcp_server
python server.py
# Server runs on port 3000
```

#### 5. CrewAI Market Spike Agent
```bash
cd crewai_agent
python main.py
# Runs continuously monitoring for spikes and crashes
```

### Option 2: Start All Components
```bash
./scripts/restart_all.sh
```

## Development Workflow

### Parallel Development with Git Worktrees

The project supports parallel development across multiple components:

```bash
# Setup worktrees (creates separate directories for each component)
./scripts/setup_worktrees.sh

# This creates:
# - services/trading/
# - services/web-dashboard/
# - services/chart-analysis/
# - services/mcp-server/
# - services/crewai-agent/
```

### Running Multiple Claude Code Instances

Open separate terminal windows:

```bash
# Terminal 1: Frontend Development
cd services/web-dashboard
claude code .

# Terminal 2: Backend Development
cd services/mcp-server
claude code .

# Terminal 3: Trading Bot Development
cd services/trading
claude code .

# Terminal 4: AI Agent Development
cd services/crewai-agent
claude code .
```

## Feature Highlights

### ✅ Implemented Features

**Core Trading System:**
- Q-Learning reinforcement learning model
- Technical indicator processing (MACD, RSI, VWAP, EMA, SMA, Bollinger Bands)
- Weighted signal system
- Smart position management with PnL-based decisions
- Binance Futures API integration
- Testnet support

**AI Components:**
- Chart analysis with OpenAI GPT-4o
- RL model retraining system
- Cost optimization (95% API cost reduction)
- Local sentiment analysis (FREE mode)

**Web Dashboard:**
- 22+ UI components
- Real-time monitoring
- Market context display
- Performance metrics
- News integration with sentiment analysis

**NEW: CrewAI Market Spike Agent**
- Multi-agent spike detection
- **Circuit Breaker Protection** (prevents catastrophic losses during market crashes)
- Context-aware trading
- Collaborative decision-making
- Intelligent risk management

### ⚠️ Pending Implementation

**High Priority:**
- PIN-based authentication system
- Emergency position close button
- Real-time log streaming
- System health monitoring UI

**Medium Priority:**
- Multiple timeframe selection
- Historical AI accuracy metrics
- Alert configuration interface
- Chart zoom and pan

## Cost Optimization

### Sentiment Analysis Modes

**Premium Mode** ($1-3/month):
```bash
python3 scripts/configure_costs.py premium
```
- Uses OpenAI GPT-4o-mini
- Higher accuracy sentiment analysis
- 1-hour cache duration

**Cost-Saving Mode** (FREE):
```bash
python3 scripts/configure_costs.py cost-saving
```
- Uses local keyword-based analysis
- No API costs
- 24-hour cache duration
- 80%+ accuracy

**Check Current Mode:**
```bash
python3 scripts/configure_costs.py status
```

## Circuit Breaker Protection

### What is the Circuit Breaker?

The **Market Guardian Agent** continuously monitors market conditions and automatically halts all trading when it detects a market crash (>15% dump). This prevents catastrophic losses during black swan events.

### Activation Triggers

Circuit breaker activates when ANY of these conditions occur:

1. **Bitcoin**: Drops >15% in 1 hour OR >20% in 4 hours
2. **Ethereum**: Drops >15% in 1 hour OR >25% in 4 hours
3. **Market-Wide**: Total crypto market cap drops >20% in 4 hours
4. **Liquidations**: Binance futures liquidations exceed $500M in 1 hour
5. **Stablecoin Depeg**: USDT/USDC depegs >3%

### Actions Taken

When circuit breaker triggers:
1. ✓ Cancels ALL pending orders (within 5 seconds)
2. ✓ Pauses ALL trading strategies
3. ✓ Sets tight stop-losses on existing positions
4. ✓ Sends CRITICAL alerts to user
5. ✓ Logs crash event with full market snapshot
6. ✓ Monitors for recovery conditions

### Recovery

Circuit breaker auto-clears when:
- No further >5% drops for 30 minutes
- Liquidations <$100M/hour
- BTC recovered >50% of initial drop
- Trading volume returns to >70% of average
- User can manually override (with warning)

## Testing

### Testnet Mode

**IMPORTANT:** Always test on testnet before live trading!

```bash
# In .env file
TESTNET=true

# Start bot - it will use Binance Futures Testnet
./scripts/start_rl_bot.sh start
```

### Circuit Breaker Test Mode

```bash
# Test circuit breaker without real market crash
cd crewai_agent
python test_circuit_breaker.py --simulate-crash BTC --dump-percent 18
```

### Paper Trading

```bash
# Run in simulation mode (no real orders)
python3 trading_bot/rl_trading_bot.py --paper-trading
```

## Monitoring & Logs

### Log Files

- **Trading Bot**: `logs/rl_bot_main.log` and `logs/rl_bot_error.log`
- **Chart Analysis**: `chart_analysis_bot.log`
- **Web Dashboard**: `web_dashboard.log`
- **Retraining**: `rl_retraining.log`
- **CrewAI Agent**: `logs/crewai_spike_agent.log`
- **Circuit Breaker**: `logs/circuit_breaker.log`

### View Logs

```bash
# Real-time log monitoring
./scripts/start_rl_bot.sh logs

# Or directly
tail -f logs/rl_bot_main.log

# All error logs
tail -f logs/*_error.log
```

### Web Dashboard

Access comprehensive monitoring at: `http://localhost:5000`

**Dashboard Features:**
- Circuit Breaker Status (top panel)
- Live market data
- Current positions and PnL
- Performance metrics
- Signal history
- Trade history
- Market news with sentiment
- RL decision transparency

## Model Retraining

The RL model learns from historical trading outcomes and improves over time.

### When to Retrain

- After significant market regime changes
- Weekly or bi-weekly maintenance
- When win rate drops below 40%
- After collecting 2000+ signals (24-48 hours)

### Retraining Process

```bash
# Stop bot before retraining
./scripts/start_rl_bot.sh stop

# Run retraining (takes 10-30 minutes)
python3 trading_bot/retrain_rl_model.py

# Restart bot with new model
./scripts/start_rl_bot.sh start
```

### Model Backups

Automatic backups created:
- `rl_trading_model_backup_YYYYMMDD_HHMMSS.pkl` (before retraining)
- `rl_trading_model_episode_XX.pkl` (every 50 episodes)

Restore from backup:
```bash
cp rl_trading_model_backup_20250124_143022.pkl rl_trading_model.pkl
```

## Troubleshooting

### Common Issues

**1. API Permission Error**
```
Error: "Permission denied" or "API-key format invalid"
```
Solution:
- Enable "Futures" permission in Binance API settings
- Verify API key and secret in .env file
- Check IP whitelist

**2. TA-Lib Installation Failed**
```
Error: "ta-lib not found"
```
Solution:
- System will automatically fallback to pandas indicators
- Or manually install TA-Lib (see platform-specific setup)

**3. Circuit Breaker False Triggers**
```
Warning: Circuit breaker triggered during normal volatility
```
Solution:
- Adjust thresholds in .env:
  ```bash
  BTC_DUMP_THRESHOLD_1H=20.0  # Increase from 15.0
  ```

**4. Database Locked Error**
```
Error: "database is locked"
```
Solution:
```bash
# Stop all bots before maintenance
./scripts/start_rl_bot.sh stop
./scripts/start_chart_bot.sh stop

# Then run your operation
python3 trading_bot/retrain_rl_model.py
```

**5. High OpenAI Costs**
```
Warning: OpenAI API usage exceeding budget
```
Solution:
```bash
# Switch to cost-saving mode
python3 scripts/configure_costs.py cost-saving
```

### Getting Help

1. Check logs for error details
2. Review troubleshooting guide in PRD (Section 18)
3. Test on testnet first
4. Join community Discord/Telegram (if available)

## Security Best Practices

### Before Live Trading Checklist

- [ ] Test thoroughly on testnet first
- [ ] Start with small position percentages (1-2%)
- [ ] Enable circuit breaker protection
- [ ] Set up IP whitelist on Binance
- [ ] Enable withdrawal lock
- [ ] Configure tight stop-losses
- [ ] Monitor liquidation prices
- [ ] Have sufficient capital buffer
- [ ] Set up critical alerts (SMS/Telegram)
- [ ] Test emergency stop functionality

### API Key Security

- [ ] Never commit .env file to git
- [ ] Use IP whitelist on Binance
- [ ] Enable 2FA on exchange account
- [ ] Disable withdrawal permissions
- [ ] Rotate API keys regularly
- [ ] Monitor API usage daily

## Performance Expectations

### Target Metrics

**Detection Performance:**
- Spike detection latency: <500ms
- True positive rate: >85%
- False positive rate: <10%
- Circuit breaker reaction: <5 seconds

**Trading Performance:**
- Target win rate: >55%
- Sharpe ratio: >1.5
- Maximum drawdown: <20%
- Risk-reward ratio: >1:1.5

**System Performance:**
- Uptime: >99.5%
- Dashboard load time: <2 seconds
- API response: <500ms
- Memory usage: <2GB per component

## Next Steps

### For Development Team

**Frontend Developer:**
1. Start with basic Flask app structure
2. Implement core dashboard layout
3. Add WebSocket for real-time updates
4. Build circuit breaker status panel
5. Integrate chart visualization

**Backend Developer:**
1. Design database schema
2. Build MCP Server REST API
3. Implement connection pooling
4. Create data aggregation services
5. Add caching layer

**Trading Developer:**
1. Implement Q-learning algorithm
2. Build technical indicators
3. Create Binance API integration
4. Develop position management
5. Build retraining system

**AI Developer:**
1. Set up CrewAI framework
2. Create Market Guardian Agent (priority!)
3. Implement circuit breaker logic
4. Build spike detection
5. Create multi-agent collaboration

### Testing Strategy

1. **Unit Testing**: Each component in isolation
2. **Integration Testing**: Component interactions
3. **Simulation Testing**: Paper trading mode
4. **Testnet Testing**: Safe live testing
5. **Chaos Testing**: Circuit breaker under stress

### Deployment Plan

1. **Alpha (Weeks 1-2)**: Internal testing, 3-5 pairs, small positions
2. **Beta (Weeks 3-6)**: Limited users, 10-20 pairs, medium positions
3. **Production (Week 7+)**: Gradual rollout, all features enabled

## Resources

### Documentation
- [Binance Futures API Docs](https://binance-docs.github.io/apidocs/futures/en/)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [CrewAI Documentation](https://docs.crewai.com/)
- [TA-Lib Documentation](https://ta-lib.org/function.html)

### Community
- Project Discord: [TBD]
- Telegram Group: [TBD]
- GitHub Issues: [repository]/issues

### Support
- Email: [TBD]
- Documentation: README.md files in each component
- PRD: See PRPs/ directory

---

## License

[TBD - Add license information]

## Contributing

[TBD - Add contribution guidelines]

---

**Last Updated:** 2025-01-24
**Version:** 1.0
**Document Owner:** Kenneth Phang
