# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**AI-Driven Cryptocurrency Binance Futures Trading System**

A 4-component trading bot system combining:
- Q-Learning reinforcement learning for adaptive decisions
- OpenAI GPT-4o for chart analysis
- Technical indicators (MACD, RSI, VWAP, EMAs, Bollinger Bands)
- Real-time web dashboard with 22+ components

**Current Status**: 30% complete (foundation implemented)
**Total Scope**: 2469-line PRP document with 8 implementation phases

---

## Architecture

### Four-Component Design

1. **RL Trading Bot** (`src/trading_bot.py`) - Main execution engine
   - Q-Learning model with experience replay
   - Weighted signal system (11+ indicators)
   - Safety-first position management
   - 60-second check interval

2. **Chart Analysis Bot** (`src/chart_analysis_bot.py`) - AI intelligence
   - Generates candlestick charts every 15 minutes
   - OpenAI GPT-4o Vision API for analysis
   - Extracts: trend, support/resistance, recommendations

3. **Web Dashboard** (`src/web_dashboard.py`) - Flask monitoring UI
   - 22+ components (charts, performance, RL decisions, news)
   - Real-time updates (30-second refresh)
   - PIN authentication
   - Port 5000

4. **MCP Server** (`src/mcp_server.py`) - Database API layer
   - RESTful API for database queries
   - Query optimization
   - Connection pooling
   - Port 3000

### Database Schema (SQLite)

**Core Tables**:
- `signals` - Trading signals with all indicators
- `trades` - Executed trades with PnL
- `bot_status` - System health metrics
- `model_checkpoints` - RL model versions

**Enhanced Tables**:
- `market_context` - BTC/ETH prices, Fear & Greed Index
- `chart_analyses` - OpenAI analysis history
- `performance_metrics` - Historical stats
- `correlation_data` - Cross-asset correlations
- `cost_analytics` - API usage tracking
- `news_cache` - Cached sentiment analysis

---

## Key Implementation Files

### ✅ Completed (30%)
- `src/database.py` - Complete database layer with 10 tables
- `src/rl_model.py` - Q-Learning agent with enhanced state representation
- `src/indicators.py` - Technical indicators + signal generation
- `requirements.txt` - All Python dependencies
- `.env.example` - Configuration template
- `IMPLEMENTATION_ROADMAP.md` - Detailed 8-phase implementation plan
- `PRPs/ai-crypto-trading-bot.md` - Full requirements (2469 lines)

### ⏳ TODO (70%)
- `src/binance_client.py` - Binance Futures API wrapper
- `src/market_context.py` - BTC correlation, Fear & Greed
- `src/trading_bot.py` - Main trading bot with safety-first logic
- `src/chart_generator.py` - mplfinance chart rendering
- `src/openai_analyzer.py` - GPT-4o Vision integration
- `src/chart_analysis_bot.py` - 15-minute analysis cycles
- `src/sentiment_local.py` - FREE local sentiment analysis
- `src/cache_manager.py` - 1h-24h persistent caching
- `src/news_fetcher.py` - NewsAPI integration
- `src/news_sentiment.py` - Dual-mode sentiment (OpenAI vs Local)
- `src/web_dashboard.py` - Flask app with 22+ components
- `src/mcp_server.py` - Database API server (port 3000)
- `retrain_rl_model.py` - RL retraining system with analytics
- `configure_costs.py` - CLI tool for cost mode switching
- `scripts/start_rl_bot.sh` - Bot management (start/stop/restart/status/logs)
- `scripts/start_chart_bot.sh` - Chart bot management
- `scripts/start_web_dashboard.sh` - Dashboard management
- `scripts/restart_all.sh` - Master restart script
- `install.sh` - One-command installation

---

## Development Commands

### Setup & Testing
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with API keys

# Test existing modules
python3 src/database.py       # Test database
python3 src/rl_model.py        # Test RL agent
python3 src/indicators.py      # Test indicators
```

### Future Commands (Once Implemented)
```bash
# Install everything
./install.sh

# Start all services
./scripts/restart_all.sh

# Manage individual services
./scripts/start_rl_bot.sh start|stop|restart|status|logs
./scripts/start_chart_bot.sh start|stop|restart|status
./scripts/start_web_dashboard.sh start|stop|restart

# Retrain RL model (after 2000+ signals)
python3 retrain_rl_model.py

# Switch cost modes
python3 configure_costs.py premium       # OpenAI GPT-4o-mini
python3 configure_costs.py cost-saving   # FREE local sentiment
python3 configure_costs.py status        # Check current mode

# View dashboard
open http://localhost:5000
```

---

## Key Patterns & Conventions

### Code Organization
- All source code in `src/` directory
- Management scripts in `scripts/` directory
- RL models stored in `models/` with backups
- Charts saved to `charts/` directory
- Logs in `logs/` with component-specific files
- Sentiment cache in `cache/` directory

### Naming Conventions
- Classes: PascalCase (e.g., `TradingDatabase`, `QLearningAgent`)
- Functions: snake_case (e.g., `calculate_rsi`, `generate_signal`)
- Constants: UPPER_SNAKE_CASE (e.g., `ACTION_BUY`, `MIN_THRESHOLD`)
- Private methods: `_leading_underscore` (e.g., `_discretize`)

### Database Operations
- Always use `TradingDatabase` class from `src/database.py`
- Never direct SQL queries outside database module
- Use prepared statements for all queries
- Close connections properly with `close_connection()`

### RL Model Usage
```python
from src.rl_model import QLearningAgent

# Initialize
agent = QLearningAgent(learning_rate=0.1, epsilon=0.1)

# Load existing model (if available)
agent.load_model("models/rl_trading_model.pkl")

# Get action with confidence
action, confidence = agent.get_action_confidence(state_dict)

# Update Q-values after trade
agent.update_q_value(state, action, reward, next_state, done)

# Save periodically
agent.save_model("models/rl_trading_model.pkl")
```

### Signal Generation
```python
from src.indicators import TechnicalIndicators, SignalGenerator

# Calculate all indicators
indicators = TechnicalIndicators.calculate_all_indicators(df)

# Generate signal
signal_gen = SignalGenerator(min_threshold=3)
signal_type, signal_strength = signal_gen.generate_signal(indicators)
# Returns: 'BUY', 'SELL', or 'HOLD' with strength integer
```

### Logging Standards
- Use emoji-rich logging for better readability:
  - 🚀 System startup
  - 💲 Price information
  - 📈 Technical indicators
  - 🔍 Signal analysis
  - ✅ Successful operations
  - ❌ Failed operations
  - ⚠️ Warnings
  - 🧠 RL decisions
  - 🌐 Market context
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Component-specific log files (e.g., `logs/rl_bot_main.log`)

---

## Critical Safety Rules

1. **ALWAYS TEST ON TESTNET FIRST**
   - Set `USE_TESTNET=true` in .env
   - Never test on live with real money

2. **Start with Small Positions**
   - Use `POSITION_PERCENTAGE=0.05` (5%)
   - Never exceed 50% of balance
   - 50x leverage is EXTREMELY risky

3. **Cost Optimization**
   - Use `USE_LOCAL_SENTIMENT=true` during development
   - Switch to premium only when needed
   - Monitor OpenAI API usage

4. **RL Model Training**
   - Needs 2000+ signals (24-48 hours) for good performance
   - Win rate starts at 0% - this is normal
   - Retrain weekly/bi-weekly

5. **API Key Security**
   - Never commit .env file
   - Use IP whitelist on Binance
   - Enable only "Futures" permission
   - Disable withdrawals

---

## Next Implementation Steps

**Priority Order** (see IMPLEMENTATION_ROADMAP.md for details):

1. **Phase 1**: Binance Futures Integration (2-3 days)
   - Implement `src/binance_client.py`
   - Test on testnet
   - Verify order placement

2. **Phase 2**: Chart Analysis Bot (1-2 days)
   - Implement chart generation
   - OpenAI GPT-4o integration
   - 15-minute analysis cycles

3. **Phase 3**: Cost Optimization (1 day)
   - Local sentiment analysis
   - Caching system
   - Configuration utility

4. **Phase 4**: News Integration (1 day)
   - NewsAPI integration
   - Dual-mode sentiment

5. **Phase 5**: Web Dashboard (3-4 days)
   - Flask backend + 22 components
   - Real-time updates
   - PIN authentication

6. **Phase 6**: MCP Server (1 day)
   - Database API layer
   - Query optimization

7. **Phase 7**: RL Retraining (2 days)
   - Complete retraining workflow
   - Analytics and backups

8. **Phase 8**: Deployment (1 day)
   - Startup scripts
   - Installation automation

**Total Estimated Time**: 10-14 days full-time development

---

## Troubleshooting Common Issues

### "TA-Lib not available"
- This is normal - system falls back to pandas
- Optional: Install TA-Lib for faster calculations
- macOS: `brew install ta-lib`
- Linux: Build from source (see IMPLEMENTATION_ROADMAP.md)

### "Database locked"
- Stop all bots before retraining
- Only one process should write to database at a time
- MCP server helps prevent this

### "API permission denied"
- Enable "Futures" permission in Binance API settings
- Check IP whitelist
- Verify API key and secret in .env

### "Model file not found"
- First time setup - model created automatically
- If corrupted, restore from `models/*_backup_*.pkl`

---

## Resources

- **PRP Document**: `PRPs/ai-crypto-trading-bot.md` (2469 lines - comprehensive spec)
- **Roadmap**: `IMPLEMENTATION_ROADMAP.md` (8 phases, detailed steps)
- **README**: `README.md` (project overview, quick start)
- **Binance API**: https://binance-docs.github.io/apidocs/futures/en/
- **OpenAI Vision**: https://platform.openai.com/docs/guides/vision
- **Q-Learning**: https://en.wikipedia.org/wiki/Q-learning

---

**Last Updated**: 2025-09-30
**Implementation Progress**: 30% (Foundation Complete)