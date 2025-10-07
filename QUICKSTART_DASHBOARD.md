# Quick Start Guide - Web Dashboard

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements-dashboard.txt
```

### Step 2: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
nano .env
```

**Minimum required settings:**
```env
BOT_CONTROL_PIN=123456    # Change this!
FLASK_SECRET_KEY=your-random-secret-key
```

### Step 3: Start the Dashboard
```bash
./start_web_dashboard.sh start
```

### Step 4: Access Dashboard
Open your browser and navigate to:
```
http://localhost:5000
```

**Default Login**: PIN `123456`

### Step 5: Change PIN Immediately
1. Login with default PIN
2. Click "Change PIN" in top navigation
3. Set a secure 6-digit PIN

---

## 📋 Essential Commands

```bash
# Start dashboard
./start_web_dashboard.sh start

# Stop dashboard
./start_web_dashboard.sh stop

# Restart dashboard
./start_web_dashboard.sh restart

# Check status
./start_web_dashboard.sh status

# View logs
./start_web_dashboard.sh logs
```

---

## 🎯 What You'll See

### Main Dashboard
- **Bot Status**: Current bot state and metrics
- **Market Data**: Real-time price, RSI, VWAP
- **Performance**: Win rate, PnL, trades
- **Charts**: Cumulative PnL, signal strength
- **Tables**: Recent trades, signals, positions
- **Controls**: Pause, emergency close, mode selection

### System Health
- CPU usage
- Memory usage
- Disk usage
- API rate limits

### Risk Management
- Stop loss levels
- Take profit targets
- Leverage settings
- Position mode

---

## ⚙️ Configuration Options

### .env File
```env
# Flask Settings
FLASK_SECRET_KEY=change-this-to-random-string
FLASK_DEBUG=False

# Security
BOT_CONTROL_PIN=123456

# Trading Bot (if integrated)
BINANCE_API_KEY=your-api-key
BINANCE_SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key
```

---

## 🔧 Troubleshooting

### Dashboard won't start
```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill process if needed
kill -9 $(lsof -t -i:5000)

# Try starting again
./start_web_dashboard.sh start
```

### No data showing
- Dashboard needs `trading_bot.db` database file
- Ensure trading bot is running
- Check API endpoints return data

### Can't login
- Verify PIN in .env file
- Restart dashboard after .env changes
- Check web_dashboard.log for errors

---

## 📊 Features Overview

### Real-time Updates
- Auto-refreshes every 30 seconds
- Manual refresh button available
- Live data from trading bot

### Interactive Controls
- Pause/resume trading
- Emergency close positions
- Change trading mode
- View system logs

### Visualization
- PnL charts (Chart.js)
- Signal strength graphs
- Performance metrics
- Market context data

---

## 🔒 Security

### Production Checklist
- [ ] Change default PIN
- [ ] Use strong secret key
- [ ] Deploy with HTTPS
- [ ] Enable IP whitelist
- [ ] Regular security updates

---

## 📱 Mobile Access

Dashboard is fully responsive:
- Works on phones
- Works on tablets
- Works on desktop

Access from any device on your network:
```
http://YOUR_SERVER_IP:5000
```

---

## 🆘 Need Help?

### Documentation
- `WEB_DASHBOARD_README.md` - Full documentation
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `/PRPs/ai-crypto-trading-bot.md` - Requirements

### Logs
```bash
# View dashboard logs
tail -f web_dashboard.log

# View all logs
./start_web_dashboard.sh logs
```

### Common Issues
1. **Port already in use**: Change port in web_dashboard.py
2. **Permission denied**: Run `chmod +x start_web_dashboard.sh`
3. **Module not found**: Install requirements again

---

## 🎓 Next Steps

1. ✅ Start dashboard
2. ✅ Login and change PIN
3. ✅ Explore interface
4. ✅ Check all panels
5. ✅ Test controls
6. ⬜ Integrate with trading bot
7. ⬜ Configure alerts
8. ⬜ Set up monitoring

---

## 📞 Support

Check the logs first:
```bash
./start_web_dashboard.sh logs
```

Review documentation:
- Technical: `IMPLEMENTATION_SUMMARY.md`
- User guide: `WEB_DASHBOARD_README.md`

---

**Version**: 1.0.0
**Last Updated**: 2025-10-07
**Status**: Production Ready ✅
