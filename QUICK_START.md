# AI Crypto Trading Bot - Quick Start Guide

**Version**: 3.0 - Production Ready
**Last Updated**: 2025-10-03
**Status**: 100% Complete - Ready for Testnet Deployment

---

## 🚀 Quick Installation (5 Minutes)

### Prerequisites
- **Python 3.9+** installed
- **Git** installed
- **Binance Futures Testnet Account** (free)
- **OpenAI API Key** (optional, can use free local mode)
- **NewsAPI Key** (optional, free tier available)

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/ai-crypto-trader.git
cd ai-crypto-trader
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected installation time**: 2-3 minutes

### Step 4: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit with your API keys
nano .env  # or use any text editor
```

**Required configuration** in `.env`:

```env
# ============================================
# BINANCE FUTURES API (TESTNET)
# ============================================
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_SECRET_KEY=your_testnet_secret_key_here
USE_TESTNET=true  # ALWAYS use testnet first!

# ============================================
# TRADING PARAMETERS
# ============================================
SYMBOL=BTCUSDT
LEVERAGE=10
POSITION_PERCENTAGE=0.05  # 5% of balance (start small!)
CHECK_INTERVAL=60  # seconds
MIN_SIGNAL_THRESHOLD=3

STOP_LOSS_PERCENTAGE=2.0
TAKE_PROFIT_PERCENTAGE=5.0

# ============================================
# OPENAI API (Optional - can use local mode)
# ============================================
OPENAI_API_KEY=your_openai_key_here  # Optional
USE_LOCAL_SENTIMENT=true  # Use FREE local sentiment

# ============================================
# NEWS API (Optional - Free tier: 1000/day)
# ============================================
NEWS_API_KEY=your_newsapi_key_here  # Optional

# ============================================
# WEB DASHBOARD
# ============================================
DASHBOARD_PORT=5000
DASHBOARD_HOST=0.0.0.0
BOT_CONTROL_PIN=123456  # Change this!

# ============================================
# MCP SERVER
# ============================================
MCP_PORT=3000
MCP_HOST=0.0.0.0
```

### Step 5: Get API Keys

#### 1. Binance Testnet (Required)

1. Go to https://testnet.binancefuture.com
2. Click "Login" → "Sign Up"
3. Create account (uses GitHub/Google login)
4. Go to API Management
5. Create new API key
6. **Enable only "Futures" permission**
7. Save API Key and Secret to `.env`

#### 2. OpenAI API (Optional)

1. Go to https://platform.openai.com
2. Create account
3. Add payment method ($5 minimum)
4. Create API key
5. Save to `.env`

**Note**: You can skip OpenAI and use FREE local sentiment analysis!

#### 3. NewsAPI (Optional)

1. Go to https://newsapi.org
2. Sign up for free account
3. Get API key (1000 requests/day FREE)
4. Save to `.env`

### Step 6: Choose Cost Mode

```bash
# Option 1: Cost-Saving Mode (FREE local sentiment)
python3 configure_costs.py cost-saving

# Option 2: Premium Mode (OpenAI GPT-4o-mini)
python3 configure_costs.py premium

# Check current mode
python3 configure_costs.py status
```

**Recommended**: Start with `cost-saving` mode (FREE)

### Step 7: Start All Services

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Start all 4 services
./scripts/restart_all.sh
```

This starts:
1. ✅ RL Trading Bot (60-second cycles)
2. ✅ Chart Analysis Bot (15-minute analysis)
3. ✅ Web Dashboard (port 5000)
4. ✅ MCP API Server (port 3000)

### Step 8: Access the System

#### Web Dashboard
```
http://localhost:5000
```

Features:
- Real-time bot status
- Live market data
- Performance metrics
- Recent trades
- AI chart analysis
- News sentiment
- Auto-refresh every 30 seconds

#### MCP API
```
http://localhost:3000/api/v1/info
```

Test endpoints:
```bash
curl http://localhost:3000/api/v1/health
curl http://localhost:3000/api/v1/bot-status
curl "http://localhost:3000/api/v1/trades/performance?hours=24"
```

---

## 📊 Monitoring & Management

### Check Service Status

```bash
# Check all services
./scripts/start_rl_bot.sh status
./scripts/start_chart_bot.sh status
./scripts/start_web_dashboard.sh status
./scripts/start_mcp_server.sh status
```

### View Logs

```bash
# Follow RL bot logs in real-time
./scripts/start_rl_bot.sh logs

# Follow chart analysis logs
./scripts/start_chart_bot.sh logs

# View specific log files
tail -f logs/rl_bot_main.log
tail -f logs/chart_bot_main.log
tail -f logs/web_dashboard.log
tail -f logs/mcp_server.log
```

### Manage Individual Services

```bash
# RL Trading Bot
./scripts/start_rl_bot.sh start
./scripts/start_rl_bot.sh stop
./scripts/start_rl_bot.sh restart

# Chart Analysis Bot
./scripts/start_chart_bot.sh start
./scripts/start_chart_bot.sh stop

# Web Dashboard
./scripts/start_web_dashboard.sh start
./scripts/start_web_dashboard.sh stop

# MCP Server
./scripts/start_mcp_server.sh start
./scripts/start_mcp_server.sh stop
```

### Restart All Services

```bash
./scripts/restart_all.sh
```

---

## 🧠 RL Model Retraining

### When to Retrain

**Minimum Requirements**:
- At least **50 signals** collected (2-3 hours runtime)
- Optimal: **2000+ signals** (24-48 hours runtime)

**Check signal count**:
```bash
sqlite3 trading_bot.db "SELECT COUNT(*) FROM signals"
```

### How to Retrain

```bash
# 1. Stop trading bot (prevents database locks)
./scripts/start_rl_bot.sh stop

# 2. Run retraining
python3 retrain_rl_model.py

# 3. Restart trading bot with new model
./scripts/start_rl_bot.sh start
```

### Retraining Output

```
🧠 RL MODEL RETRAINING SYSTEM
================================================================================
📊 Checking data requirements...
   Signals: 2458 (min: 50, optimal: 2000)
   Trades: 45
   Date range: 2025-10-01 to 2025-10-03
✅ Sufficient data available for retraining

💾 Creating backup...
💾 Model backed up to: models/rl_trading_model_backup_20251003_103045.pkl

🧠 Loading RL agent...
   Loaded existing model from models/rl_trading_model.pkl

📥 Loading training data from database...
✅ Loaded 2458 training samples

🎓 Starting training: 150 episodes...
================================================================================
Episode 10/150 | Win Rate: 52.3% | Trades: 42 | Best: 54.1% (ep 8)
Episode 20/150 | Win Rate: 55.7% | Trades: 43 | Best: 56.2% (ep 18)
...
Episode 150/150 | Win Rate: 64.8% | Trades: 45 | Best: 68.5% (ep 127)

================================================================================
📊 RETRAINING ANALYTICS
================================================================================

🏆 Best Performance:
   Episode: 127
   Win Rate: 68.5%
   Avg Reward: 12.34

📈 Recent Performance (Last 50 Episodes):
   Avg Win Rate: 64.2%
   Avg Trades/Episode: 45

🎯 Learning Progress:
   Early Win Rate: 52.1%
   Recent Win Rate: 64.2%
   Improvement: +23.2%

✅ Retraining completed successfully!
```

---

## 🔍 Database Queries

### Useful SQL Queries

```bash
# Enter SQLite shell
sqlite3 trading_bot.db

# View recent signals
SELECT * FROM signals ORDER BY timestamp DESC LIMIT 10;

# View recent trades
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;

# Count signals by type
SELECT signal_type, COUNT(*) FROM signals GROUP BY signal_type;

# Calculate win rate
SELECT
  COUNT(*) as total_trades,
  SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
  ROUND(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_rate
FROM trades
WHERE pnl IS NOT NULL;

# Total PnL
SELECT SUM(pnl) as total_pnl FROM trades WHERE pnl IS NOT NULL;

# Exit SQLite
.quit
```

---

## 🎯 Success Metrics

### After 24 Hours (Day 1)

**Expected Results**:
- ✅ Bot running without crashes
- ✅ 50-100 signals generated
- ✅ Charts created every 15 minutes
- ✅ Database growing with data
- ⚠️ Win rate may be 0-30% (normal, needs training)

**Actions**:
- Monitor logs for errors
- Check dashboard regularly
- No retraining yet (insufficient data)

### After 3 Days (72 Hours)

**Expected Results**:
- ✅ 500-1000 signals collected
- ✅ 10-30 trades executed
- ✅ First retraining possible
- ⚠️ Win rate improving (30-45%)

**Actions**:
- Run first retraining: `python3 retrain_rl_model.py`
- Review performance metrics
- Adjust parameters if needed

### After 1 Week (7 Days)

**Expected Results**:
- ✅ 2000+ signals collected
- ✅ Multiple retraining cycles
- ✅ Win rate 45-60%
- ✅ Positive total PnL (hopefully!)

**Actions**:
- Continue retraining weekly
- Monitor long-term trends
- Consider live trading preparation

### After 2-4 Weeks

**Ready for Live Trading Evaluation**:
- ✅ Win rate >50%
- ✅ Consistent positive PnL
- ✅ No critical errors
- ✅ Multiple market conditions tested

⚠️ **IMPORTANT**: Even with good testnet results, start live trading with **very small positions** (1% of balance)

---

## 🐛 Troubleshooting

### Bot Won't Start

**Check virtual environment**:
```bash
which python3  # Should show venv/bin/python3
source venv/bin/activate
```

**Check dependencies**:
```bash
pip install -r requirements.txt
```

**Check .env file**:
```bash
cat .env | grep BINANCE_API_KEY
```

### "Permission Denied" Error

**Enable Futures permission**:
1. Go to Binance Testnet
2. API Management
3. Edit API Key
4. Enable "Futures" permission
5. Save

### Database Locked Error

**Stop all services before retraining**:
```bash
./scripts/start_rl_bot.sh stop
./scripts/start_chart_bot.sh stop
python3 retrain_rl_model.py
./scripts/restart_all.sh
```

### High API Costs

**Switch to cost-saving mode**:
```bash
python3 configure_costs.py cost-saving
./scripts/restart_all.sh
```

### No Trades Executed

**Check signal threshold** (may be too high):
```bash
# Edit .env
MIN_SIGNAL_THRESHOLD=2  # Lower from 3 to 2

# Restart bot
./scripts/start_rl_bot.sh restart
```

### Win Rate at 0%

**This is NORMAL for new bots!**

The RL model needs training data:
1. Let bot run for 24-48 hours
2. Collect 500-2000 signals
3. Run retraining: `python3 retrain_rl_model.py`
4. Win rate will improve over time

---

## 🔐 Security Best Practices

### API Key Security

1. ✅ **Use testnet first** - Never test with real money
2. ✅ **Enable IP whitelist** - Restrict API access to your server
3. ✅ **Futures permission only** - Disable spot, margin, withdrawals
4. ✅ **Never commit .env** - Already in .gitignore
5. ✅ **Rotate keys regularly** - Change every 30-90 days

### Dashboard Access

1. ✅ **Change default PIN** - Edit `BOT_CONTROL_PIN` in .env
2. ✅ **Use firewall** - Restrict port 5000 access
3. ✅ **HTTPS in production** - Use reverse proxy (nginx)
4. ✅ **Strong passwords** - Use password manager

### Server Security

1. ✅ **Keep system updated** - `sudo apt update && sudo apt upgrade`
2. ✅ **Use SSH keys** - Disable password auth
3. ✅ **Enable firewall** - `sudo ufw enable`
4. ✅ **Monitor logs** - Check for suspicious activity
5. ✅ **Backup database** - Regular backups of trading_bot.db

---

## 📈 Performance Optimization

### Increase Trading Frequency

**Lower signal threshold** (more trades, lower quality):
```env
MIN_SIGNAL_THRESHOLD=2  # Default: 3
```

**Reduce check interval** (more frequent checks):
```env
CHECK_INTERVAL=30  # Default: 60 seconds
```

### Reduce Risk

**Lower position size**:
```env
POSITION_PERCENTAGE=0.03  # 3% instead of 5%
```

**Tighter stop loss**:
```env
STOP_LOSS_PERCENTAGE=1.0  # 1% instead of 2%
```

**Lower leverage**:
```env
LEVERAGE=5  # Default: 10x
```

### Improve Win Rate

1. **Collect more data** - Run for 1-2 weeks
2. **Retrain frequently** - Every 2-3 days
3. **Test different thresholds** - Try MIN_SIGNAL_THRESHOLD 2-4
4. **Use premium mode** - OpenAI analysis (costs ~$3/month)
5. **Monitor market conditions** - Avoid high volatility periods

---

## 📚 Additional Resources

### Documentation

- **MAIN_PRP_STATUS.md** - Complete implementation status
- **IMPLEMENTATION_SUMMARY.md** - High-level overview
- **PRPs/ai-crypto-trading-bot.md** - Full requirements (2468 lines)
- **IMPLEMENTATION_ROADMAP.md** - 8-phase roadmap

### Logs Directory

```
logs/
├── rl_bot.pid              # RL bot process ID
├── rl_bot_main.log         # RL bot main log
├── rl_bot_error.log        # RL bot errors
├── chart_bot.pid           # Chart bot process ID
├── chart_bot_main.log      # Chart analysis log
├── chart_bot_error.log     # Chart analysis errors
├── web_dashboard.pid       # Dashboard process ID
├── web_dashboard.log       # Dashboard log
├── mcp_server.pid          # MCP server process ID
├── mcp_server.log          # MCP server log
└── rl_retraining.log       # Retraining log
```

### Database Schema

14 tables:
- `signals` - Trading signals with indicators
- `trades` - Executed trades with PnL
- `bot_status` - System health metrics
- `model_checkpoints` - RL model versions
- `market_context` - BTC/ETH/Fear & Greed
- `chart_analyses` - AI chart analysis
- `performance_metrics` - Historical stats
- `correlation_data` - Cross-asset correlations
- `cost_analytics` - API usage tracking
- `news_cache` - Cached sentiment analysis
- And 4 more...

---

## 🎉 Next Steps

### Immediate (First 24 Hours)

1. ✅ Start all services: `./scripts/restart_all.sh`
2. ✅ Access dashboard: http://localhost:5000
3. ✅ Monitor logs: `./scripts/start_rl_bot.sh logs`
4. ✅ Check for errors in logs
5. ✅ Verify signals being generated

### Short-term (First Week)

1. ✅ Collect 500-2000 signals
2. ✅ Run first retraining
3. ✅ Monitor win rate improvement
4. ✅ Adjust parameters if needed
5. ✅ Test cost-saving vs premium mode

### Medium-term (First Month)

1. ✅ Achieve 50%+ win rate
2. ✅ Retrain weekly or bi-weekly
3. ✅ Test different trading pairs
4. ✅ Optimize parameters
5. ✅ Prepare for live trading evaluation

### Long-term (2-3 Months)

1. ⚠️ Consider live trading (start VERY small)
2. ⚠️ Implement additional safety checks
3. ⚠️ Monitor live performance closely
4. ⚠️ Scale up gradually
5. ⚠️ Continue learning and improving

---

## 💰 Cost Breakdown

### Testnet (FREE)

- Binance Testnet: **FREE**
- Local Sentiment: **FREE**
- NewsAPI (1000/day): **FREE**
- **Total: $0/month**

### Testnet with OpenAI (Premium)

- Binance Testnet: **FREE**
- OpenAI GPT-4o-mini: **~$2.50-3.00/month**
- NewsAPI (1000/day): **FREE**
- **Total: ~$3/month**

### Live Trading (Recommended Start)

- Binance Futures: **0.02-0.04% per trade**
- OpenAI GPT-4o-mini: **~$2.50-3.00/month**
- NewsAPI: **FREE**
- **Total: ~$3/month + trading fees**

---

## ⚠️ Risk Warning

**IMPORTANT DISCLAIMERS**:

1. ⚠️ **Cryptocurrency trading is risky** - You can lose all your capital
2. ⚠️ **Leverage amplifies losses** - 10x leverage = 10x risk
3. ⚠️ **Bot is not perfect** - No guaranteed profits
4. ⚠️ **Test thoroughly** - Use testnet for 2-4 weeks minimum
5. ⚠️ **Start small** - Use 1-5% position sizes
6. ⚠️ **Never invest more than you can afford to lose**
7. ⚠️ **Past performance ≠ future results**
8. ⚠️ **This is experimental software** - Use at your own risk

**This bot is for educational and research purposes. Trading cryptocurrency carries substantial risk of loss.**

---

## 🆘 Support

### Common Issues

1. Check logs: `./scripts/start_rl_bot.sh logs`
2. Review troubleshooting section above
3. Check database: `sqlite3 trading_bot.db`
4. Verify .env configuration
5. Restart services: `./scripts/restart_all.sh`

### Report Issues

- GitHub Issues: https://github.com/yourusername/ai-crypto-trader/issues
- Include logs, error messages, and system info
- Describe steps to reproduce

---

**Ready to start trading? Run `./scripts/restart_all.sh` and visit http://localhost:5000!** 🚀

**Last Updated**: 2025-10-03
**Version**: 3.0
**Status**: Production Ready (Testnet)
