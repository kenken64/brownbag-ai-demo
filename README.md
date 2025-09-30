# AI-Driven Cryptocurrency Binance Futures Trading System

**Status**: 🚧 Foundation Complete (30% implementation)
**Version**: 3.0
**Last Updated**: 2025-09-30

An intelligent, automated cryptocurrency futures trading system that combines reinforcement learning, AI-powered technical analysis, and real-time monitoring to execute profitable trading strategies on Binance Futures.

---

## 🎯 Project Vision

Create a production-ready trading bot that:
- Uses Q-Learning reinforcement learning for adaptive decision-making
- Analyzes charts with OpenAI GPT-4o for market intelligence
- Implements safety-first risk management
- Provides real-time web dashboard monitoring
- Achieves 95% API cost reduction through intelligent caching

---

## ✅ Current Implementation Status (30%)

### Completed Components
- ✅ **Project Structure** - Organized directory layout (src/, logs/, models/, charts/)
- ✅ **Database Layer** - Complete SQLite schema with 10 tables
- ✅ **Q-Learning RL Model** - Enhanced state representation with experience replay
- ✅ **Technical Indicators** - MACD, RSI, VWAP, EMA, SMA, Bollinger Bands
- ✅ **Signal Generation** - Weighted multi-indicator system (threshold: 3)
- ✅ **Configuration** - Environment variables, API key management
- ✅ **Documentation** - Comprehensive PRP (2469 lines), implementation roadmap

### Pending Components (70%)
- ⏳ Binance Futures API integration
- ⏳ Market context awareness (BTC correlation, Fear & Greed)
- ⏳ Main RL trading bot with safety-first logic
- ⏳ Chart analysis bot (OpenAI GPT-4o)
- ⏳ Cost optimization system (local sentiment analysis)
- ⏳ News integration (NewsAPI)
- ⏳ Web dashboard (Flask + 22 components)
- ⏳ MCP server (database API layer)
- ⏳ RL retraining system
- ⏳ Deployment scripts

**See**: `IMPLEMENTATION_ROADMAP.md` for detailed breakdown

---

## 🏗️ System Architecture

### Four-Component Design

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Dashboard (Flask)                    │
│  Live Charts │ Performance │ RL Decisions │ News Feed        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌──────────┐
│  RL Trading Bot     │◄─┤  Chart Analysis Bot │  │   MCP    │
│  - Q-Learning       │  │  - OpenAI GPT-4o    │  │  Server  │
│  - Signal Gen       │  │  - 15min cycles     │  │  (Port   │
│  - Position Mgmt    │  │  - Chart rendering  │  │  3000)   │
│  - Safety-first     │  └─────────────────────┘  └──────────┘
└─────────────────────┘              │                   │
          │                          │                   │
          └──────────────┬───────────┴───────────────────┘
                         ▼
                ┌────────────────────┐
                │  SQLite Database   │
                │  - 10 tables       │
                │  - Historical data │
                └────────────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- Binance Futures account (testnet recommended)
- OpenAI API key (optional with cost-saving mode)
- NewsAPI key (optional)

### 2. Installation

```bash
# Clone repository
git clone https://github.com/kenken64/brownbag-ai-demo.git
cd brownbag-ai-demo

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install TA-Lib for faster indicators
# macOS: brew install ta-lib
# Linux: See IMPLEMENTATION_ROADMAP.md for build instructions
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**Required Configuration**:
```env
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret
USE_TESTNET=true  # Start with testnet!

OPENAI_API_KEY=your_openai_key  # Optional with cost-saving mode
NEWS_API_KEY=your_newsapi_key  # Optional

USE_LOCAL_SENTIMENT=true  # Use FREE sentiment analysis
POSITION_PERCENTAGE=0.05  # 5% position size (start small!)
```

### 4. Test Existing Modules

```bash
# Test database
python3 src/database.py

# Test RL model
python3 src/rl_model.py

# Test technical indicators
python3 src/indicators.py
```

---

## 📁 Project Structure

```
ai-crypto-trader/
├── src/                       # Source code
│   ├── database.py           ✅ Database operations
│   ├── rl_model.py           ✅ Q-Learning agent
│   ├── indicators.py         ✅ Technical indicators
│   ├── binance_client.py     ⏳ TODO: Binance API
│   ├── market_context.py     ⏳ TODO: BTC/Fear & Greed
│   ├── trading_bot.py        ⏳ TODO: Main bot
│   ├── chart_generator.py    ⏳ TODO: Chart rendering
│   ├── openai_analyzer.py    ⏳ TODO: GPT-4o analysis
│   ├── chart_analysis_bot.py ⏳ TODO: Analysis bot
│   ├── sentiment_local.py    ⏳ TODO: Local sentiment
│   ├── news_fetcher.py       ⏳ TODO: NewsAPI
│   ├── web_dashboard.py      ⏳ TODO: Flask app
│   └── mcp_server.py         ⏳ TODO: Database API
├── scripts/                   # Management scripts
│   ├── start_rl_bot.sh       ⏳ TODO
│   ├── start_chart_bot.sh    ⏳ TODO
│   ├── start_web_dashboard.sh ⏳ TODO
│   └── restart_all.sh        ⏳ TODO
├── models/                    # RL model storage
├── charts/                    # Generated charts
├── logs/                      # Log files
├── cache/                     # Sentiment cache
├── tests/                     # Unit tests
├── PRPs/                      # Product requirements
│   └── ai-crypto-trading-bot.md  # Main PRP (2469 lines)
├── .claude/commands/          # Custom Claude commands
│   └── execute-prp.md
├── requirements.txt           ✅ Python dependencies
├── .env.example               ✅ Configuration template
├── CLAUDE.md                  # Claude Code context
├── IMPLEMENTATION_ROADMAP.md  ✅ Detailed implementation plan
└── README.md                  # This file
```

---

## 🧠 Key Features

### Reinforcement Learning (Q-Learning)
- Enhanced state representation (indicators + market context)
- Experience replay buffer (10,000 samples)
- Epsilon-greedy exploration
- PnL-based reward system
- Model persistence and backup

### Technical Analysis
- 11+ indicators: MACD, RSI, VWAP, EMA (9,21), SMA (50), Bollinger Bands
- Weighted signal system (±1, ±2, ±3 points)
- Minimum threshold: 3 points
- Real-time calculation

### Safety-First Logic
- Confidence thresholding
- PnL-based position management
- Cut losses early (negative PnL + HOLD = close)
- Let winners run (positive PnL + HOLD = keep)
- Market context confirmation

### Cost Optimization
- **Premium Mode**: OpenAI GPT-4o-mini ($1-3/month)
- **Cost-Saving Mode**: FREE local sentiment analysis
- Aggressive caching (1h-24h duration)
- 90-95% API cost reduction

---

## 📊 Database Schema

**Core Tables**:
- `signals` - All generated trading signals with indicators
- `trades` - Executed trades with PnL tracking
- `bot_status` - System health and metrics
- `model_checkpoints` - RL model versions

**Enhanced Tables**:
- `market_context` - BTC/ETH data, Fear & Greed Index
- `chart_analyses` - AI analysis history
- `performance_metrics` - Historical performance
- `correlation_data` - Cross-asset correlations
- `cost_analytics` - API usage tracking
- `news_cache` - Cached sentiment analysis

---

## 🎓 Development Workflow

### Context Engineering Setup
This project uses **Claude Code** with custom PRP execution:

1. **Custom Command**: `/execute-prp PRPs/ai-crypto-trading-bot.md`
2. **Structured Workflow**:
   - Load PRP → ULTRATHINK → Execute → Validate → Complete
3. **Configuration**: `.claude/commands/execute-prp.md`
4. **Permissions**: `settings.local.json`

### Next Steps for Developers

1. **Phase 1: Binance Integration** (2-3 days)
   - Implement `src/binance_client.py`
   - Test on testnet
   - See: IMPLEMENTATION_ROADMAP.md § Phase 1

2. **Phase 2: Chart Analysis** (1-2 days)
   - Implement chart generation
   - OpenAI GPT-4o integration
   - See: IMPLEMENTATION_ROADMAP.md § Phase 2

3. **Phase 3-8**: Continue with roadmap phases

---

## ⚠️ Critical Warnings

1. **🚨 ALWAYS TEST ON TESTNET FIRST** - Set `USE_TESTNET=true`
2. **💸 Start with small positions** - Use 1-5% of balance
3. **⚡ 50x leverage is RISKY** - Monitor liquidation prices
4. **🧠 Retrain RL model** - After 2000+ signals (24-48 hours)
5. **💰 Enable cost-saving mode** - During development/testing
6. **📊 0% win rate initially** - Model needs training data
7. **🔐 Secure API keys** - Never commit .env file
8. **🚦 Use IP whitelist** - On Binance API settings

---

## 📚 Key Resources

- **PRP Document**: `PRPs/ai-crypto-trading-bot.md` (comprehensive requirements)
- **Roadmap**: `IMPLEMENTATION_ROADMAP.md` (step-by-step implementation)
- **Binance API**: https://binance-docs.github.io/apidocs/futures/en/
- **OpenAI Vision**: https://platform.openai.com/docs/guides/vision
- **Q-Learning**: https://en.wikipedia.org/wiki/Q-learning

---

## 🤝 Contributing

This is a demonstration project for context engineering with Claude Code. See `IMPLEMENTATION_ROADMAP.md` for contribution opportunities.

---

## 📄 License

MIT

---

## 🙏 Acknowledgments

- **Context Engineering**: Claude Code PRP execution framework
- **Architecture**: 4-component modular design
- **AI Integration**: OpenAI GPT-4o for chart analysis
- **Trading Platform**: Binance Futures API

---

**⚠️ Disclaimer**: This is educational software. Cryptocurrency trading carries significant risk. Use at your own risk. The authors are not responsible for any financial losses.