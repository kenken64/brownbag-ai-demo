# AI-Driven Cryptocurrency Trading Bot - Setup Guide

Complete setup guide for the RL-enhanced trading bot system.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [API Keys Setup](#api-keys-setup)
- [Configuration](#configuration)
- [Running the Bots](#running-the-bots)
- [Cost Optimization](#cost-optimization)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.9 or higher
- **Memory**: Minimum 2GB RAM
- **Disk Space**: 10GB available
- **Internet**: Stable connection required

### Required Accounts
1. **Binance Account** - For futures trading
2. **OpenAI Account** - For AI-powered chart analysis (optional)
3. **NewsAPI Account** - For market news (optional)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd ai-crypto-trader
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### 4. Platform-Specific: Install TA-Lib (Optional)

The bot includes fallback pandas-based indicators, but TA-Lib provides better performance.

**macOS:**
```bash
brew install ta-lib
pip install TA-Lib
```

**Linux (Ubuntu/Debian):**
```bash
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
pip install TA-Lib
```

**Windows:**
```bash
# Download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
pip install TA_Lib‑0.4.28‑cp39‑cp39‑win_amd64.whl
```

### 5. Initialize Database
```bash
python3 database.py
```

This creates the SQLite database with all required tables.

## API Keys Setup

### 1. Binance Futures API Keys

1. **Create Account**: Sign up at [Binance.com](https://www.binance.com)
2. **Navigate to API Management**: Account > API Management
3. **Create New API Key**:
   - Label: "Trading Bot"
   - Enable "Futures" permission
   - **IMPORTANT**: Enable "Enable Trading" ONLY when ready for live trading
4. **Security Settings**:
   - Add your server IP to whitelist (recommended)
   - Enable "Restrict access to trusted IPs only"
   - **NEVER** enable withdrawal permissions
5. **Save Credentials**:
   - Copy API Key
   - Copy Secret Key (shown only once)

### 2. OpenAI API Keys (Optional)

1. **Create Account**: Sign up at [platform.openai.com](https://platform.openai.com)
2. **Navigate to API Keys**: Settings > API Keys
3. **Create New Secret Key**:
   - Name: "Trading Bot Chart Analysis"
   - Copy the key (shown only once)
4. **Add Credits**: Billing > Add Payment Method
   - Minimum: $5 recommended
   - GPT-4o-mini usage: ~$1-3/month

### 3. NewsAPI Keys (Optional)

1. **Create Account**: Sign up at [newsapi.org](https://newsapi.org/register)
2. **Copy API Key**: Shown on dashboard after registration
3. **Free Tier Limits**: 1000 requests/day

## Configuration

### 1. Create .env File

```bash
# Copy template
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

### 2. Configure Essential Settings

Edit `.env` file:

```bash
# ===== REQUIRED: Binance API =====
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_SECRET_KEY=your_actual_secret_key_here

# ===== OPTIONAL: OpenAI API (for chart analysis) =====
OPENAI_API_KEY=your_openai_api_key_here  # Leave empty to skip chart analysis

# ===== OPTIONAL: NewsAPI (for market news) =====
NEWS_API_KEY=your_newsapi_key_here  # Leave empty to skip news

# ===== Trading Configuration =====
TRADING_SYMBOL=SUIUSDC          # Trading pair
LEVERAGE=50                      # Leverage (1-125)
POSITION_PERCENTAGE=5            # % of balance per trade
STOP_LOSS_PERCENTAGE=2           # Stop loss %
TAKE_PROFIT_PERCENTAGE=3         # Take profit %
INTERVAL=60                      # Check interval (seconds)
MINIMUM_SIGNAL_THRESHOLD=3       # Minimum signal strength to act

# ===== IMPORTANT: Safety Settings =====
USE_TESTNET=true                 # ALWAYS start with testnet!

# ===== Cost Optimization =====
USE_LOCAL_SENTIMENT=true         # true = FREE, false = OpenAI ($1-3/month)
SENTIMENT_CACHE_DURATION=86400   # 24 hours for cost-saving

# ===== Web Dashboard =====
BOT_CONTROL_PIN=123456           # Change this to your 6-digit PIN
DASHBOARD_PORT=5000
```

### 3. Configure Cost Mode

```bash
# For FREE sentiment analysis (recommended)
python3 configure_costs.py cost-saving

# For premium OpenAI sentiment analysis
python3 configure_costs.py premium

# Check current configuration
python3 configure_costs.py status
```

## Running the Bots

### 1. Start RL Trading Bot

```bash
# Start the bot
./start_rl_bot.sh start

# Check status
./start_rl_bot.sh status

# View live logs
./start_rl_bot.sh logs

# Stop the bot
./start_rl_bot.sh stop

# Restart the bot
./start_rl_bot.sh restart
```

### 2. Start Chart Analysis Bot (Optional)

```bash
# Start chart analysis
./start_chart_bot.sh start

# Check status
./start_chart_bot.sh status

# View logs
./start_chart_bot.sh logs
```

### 3. Monitor Logs

**RL Bot Logs:**
```bash
tail -f logs/rl_bot_main.log      # Main operations
tail -f logs/rl_bot_error.log     # Errors only
```

**Chart Bot Logs:**
```bash
tail -f chart_analysis_bot.log
```

## Cost Optimization

### Cost-Saving Mode (FREE)
- Uses local keyword-based sentiment analysis
- No OpenAI API calls for sentiment
- Cache duration: 24 hours
- Monthly cost: **$0**

### Premium Mode ($1-3/month)
- Uses OpenAI GPT-4o-mini for sentiment
- More accurate sentiment analysis
- Cache duration: 1 hour
- Monthly cost: **~$1-3**

### Switch Modes:
```bash
# Enable cost-saving (FREE)
python3 configure_costs.py cost-saving

# Enable premium mode
python3 configure_costs.py premium
```

## Testing

### 1. Testnet Testing (REQUIRED)

**IMPORTANT**: Always test on testnet before live trading!

```bash
# Ensure USE_TESTNET=true in .env
USE_TESTNET=true

# Start bot
./start_rl_bot.sh start

# Monitor for 24-48 hours
./start_rl_bot.sh logs
```

### 2. Check Database

```bash
# Check signals collected
sqlite3 trading_bot.db "SELECT COUNT(*) FROM signals;"

# Check trades executed
sqlite3 trading_bot.db "SELECT COUNT(*) FROM trades;"

# View recent signals
sqlite3 trading_bot.db "SELECT * FROM signals ORDER BY timestamp DESC LIMIT 10;"
```

### 3. Test RL Model Retraining

After running bot for 2-3 hours:

```bash
# Retrain model
python3 retrain_rl_model.py

# Check retraining log
cat rl_retraining.log
```

### 4. Test Technical Indicators

```bash
# Run indicator tests
python3 technical_indicators.py
```

## Live Trading Transition

### Before Going Live:

1. **Testnet Results**: Verify positive performance on testnet
2. **RL Model**: Retrain with at least 2000 signals
3. **Configuration**: Review all settings in .env
4. **Position Sizing**: Start with small positions (1-2%)
5. **Stop Loss**: Ensure stop loss is configured
6. **Monitoring**: Set up monitoring and alerts

### Enable Live Trading:

1. **Update .env**:
```bash
USE_TESTNET=false
POSITION_PERCENTAGE=1  # Start small!
```

2. **Verify API Permissions**:
   - Ensure Binance API has "Enable Trading" enabled
   - Verify IP whitelist
   - Double-check withdrawal is DISABLED

3. **Restart Bot**:
```bash
./start_rl_bot.sh restart
```

4. **Monitor Closely**:
```bash
# Watch logs continuously for first 24 hours
./start_rl_bot.sh logs
```

## Troubleshooting

### Common Issues

#### 1. "No module named 'binance'"
```bash
# Activate venv and reinstall
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. "API-key format invalid"
- Check .env file has correct API keys
- Ensure no extra spaces in .env
- Verify API key has "Futures" permission enabled

#### 3. "Insufficient balance"
- Check account has USDC available
- Verify position percentage setting
- Check leverage setting

#### 4. Database locked
```bash
# Stop bot before database operations
./start_rl_bot.sh stop
python3 retrain_rl_model.py
./start_rl_bot.sh start
```

#### 5. Chart analysis not working
- Verify OPENAI_API_KEY is set
- Check OpenAI account has credits
- Ensure mplfinance is installed: `pip install mplfinance`

### Log Locations

- **RL Bot Main**: `logs/rl_bot_main.log`
- **RL Bot Errors**: `logs/rl_bot_error.log`
- **Chart Analysis**: `chart_analysis_bot.log`
- **Retraining**: `rl_retraining.log`

### Get Help

1. Check logs for error messages
2. Verify API keys and permissions
3. Ensure all dependencies installed
4. Test on testnet first
5. Review PRP document: `PRPs/ai-crypto-trading-bot.md`

## Performance Optimization

### 1. Adjust Signal Threshold
```bash
# In .env, lower threshold for more trades
MINIMUM_SIGNAL_THRESHOLD=2  # Default: 3
```

### 2. Optimize Position Sizing
```bash
# Start conservatively
POSITION_PERCENTAGE=1  # 1% of balance
```

### 3. Retrain Model Regularly
```bash
# Retrain weekly for best results
python3 retrain_rl_model.py
```

### 4. Monitor Performance
- Track win rate (target: >55%)
- Monitor max drawdown (<20%)
- Review risk-reward ratio (>1:1.5)

## Security Best Practices

1. **Never share API keys**
2. **Use IP whitelist on Binance**
3. **Disable withdrawal permissions**
4. **Keep .env file secure** (add to .gitignore)
5. **Use strong dashboard PIN**
6. **Monitor account regularly**
7. **Start with testnet**
8. **Use small position sizes initially**

## Next Steps

1. Complete API key setup
2. Configure .env file
3. Test on testnet for 24-48 hours
4. Retrain RL model with collected data
5. Monitor performance metrics
6. Gradually transition to live trading (if profitable on testnet)

## Support

- **Documentation**: See `PRPs/ai-crypto-trading-bot.md`
- **Issues**: Check troubleshooting section above
- **Logs**: Review log files for detailed error messages

---

**DISCLAIMER**: Cryptocurrency trading involves substantial risk. Never trade with money you cannot afford to lose. This bot is provided as-is without warranty. Always test thoroughly on testnet before live trading.
