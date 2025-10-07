# AI Crypto Trading Bot - Web Dashboard

A comprehensive, real-time web dashboard for monitoring and controlling the AI-driven cryptocurrency trading bot.

## Features Implemented

### Core Dashboard Components

#### FR-WD-001: Live Chart Display
- Real-time market data visualization
- 30-second auto-refresh
- Technical indicator overlays (EMA 9, EMA 21, SMA 50)
- Bollinger Bands visualization
- Volume bars with color coding
- RSI and MACD subplots

#### FR-WD-002: Analysis Results Panel
- Latest OpenAI recommendations (HOLD/BUY/SELL)
- Confidence score visualization
- Current price and 24h change percentage
- Key observations from technical analysis
- Risk factors section
- AI analysis narrative

#### FR-WD-003: Multi-Bot Status Monitoring
- Real-time bot status (RUNNING/STOPPED)
- Process ID (PID) display
- Last update timestamp
- Trade execution status
- Trading mode indicator
- Signal counter

#### FR-WD-005: Manual Control Panel
- Trading pair selector
- Trading mode selection (Auto/Manual/Paper)
- Refresh button
- Logs viewer button
- Pause/Resume button
- Emergency close button

#### FR-WD-006: Market Context & Cross-Asset Analysis
- BTC price with 24h percentage change
- ETH price with 24h percentage change
- BTC Dominance percentage
- Fear & Greed Index (0-100 scale)
- Market Trend indicator
- BTC Trend strength
- Market Regime indicator

#### FR-WD-007: RL Bot Status Panel
- Bot running status with color indicator
- Process ID display
- Last update timestamp
- Trade execution toggle
- Real-time status updates

#### FR-WD-009: Live Market Data Panel
- Current price (4 decimal precision)
- RSI value
- VWAP value
- Current signal with strength

#### FR-WD-010: Live Position Display
- Position side (LONG/SHORT)
- Position size
- Entry price
- Real-time updates

#### FR-WD-012: Performance Metrics Dashboard
- Win rate percentage
- Total PnL with color coding
- Average win amount
- Average loss amount
- Risk-reward ratio
- Total trades count

#### FR-WD-013: Trade Breakdown Panel
- Total trades
- Winning trades (green)
- Losing trades (red)
- Max loss amount

#### FR-WD-014: Open Positions Table
- Entry price
- Current price
- Unrealized PnL
- Position size
- Side (LONG/SHORT)

#### FR-WD-018: Cumulative PnL Chart
- Time-series line chart
- Historical profit/loss visualization
- Interactive Chart.js implementation

#### FR-WD-019: Signal Strength Visualization
- Dual histogram chart
- Buy signals in green
- Sell signals in red

#### FR-WD-020: Recent Signals Table
- Time column
- Signal type (HOLD/BUY/SELL)
- Strength value
- Price at signal time

#### FR-WD-021: Recent Trades Table
- Time with date
- Side (BUY/SELL) with color coding
- Entry price
- PnL with color coding
- Status (CLOSED/OPEN)

#### FR-WD-022: Market News Section
- News article display
- Pagination support
- Timestamp and source attribution

### Security Features (FR-WD-023)

#### Authentication System
- 6-digit PIN login
- Session-based authentication
- Session timeout (30 minutes)
- PIN change functionality
- Auto-submit on 6-digit entry

### Advanced Features

#### FR-WD-026: Advanced Bot Controls
- Emergency position close button
- Trading mode selection (Auto/Manual/Paper)
- Pause/Resume controls
- Confirmation dialogs for critical actions

#### FR-WD-027: Log Streaming Interface
- Real-time log display
- Log type filtering (Main/Chart/Web/RL)
- Search functionality
- Auto-scroll with pause option
- Log export/download

#### FR-WD-029: System Health Monitoring
- CPU usage with progress bar
- Memory usage with available/total display
- Disk usage with available/total display
- API rate limit indicators
- Color-coded health status

#### FR-WD-030: Risk Management UI
- Stop loss display (default 2%)
- Take profit targets (3%, 5%, 10%)
- Leverage indicator (50x CROSS)
- Position mode display (Hedge/One-way)
- Risk exposure percentage

## Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   cd ai-crypto-trader
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-dashboard.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys and configuration
   ```

5. **Initialize database** (if not already created)
   The dashboard expects a SQLite database at `trading_bot.db` with the following tables:
   - signals
   - trades
   - bot_status
   - model_checkpoints

## Running the Dashboard

### Using the startup script (Recommended)

```bash
# Start the dashboard
./start_web_dashboard.sh start

# Stop the dashboard
./start_web_dashboard.sh stop

# Restart the dashboard
./start_web_dashboard.sh restart

# Check status
./start_web_dashboard.sh status

# View logs
./start_web_dashboard.sh logs
```

### Manual start

```bash
python3 web_dashboard.py
```

The dashboard will be available at: **http://localhost:5000**

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here
FLASK_DEBUG=False

# Bot Control PIN (must be 6 digits)
BOT_CONTROL_PIN=123456

# Binance API Keys
BINANCE_API_KEY=your-api-key
BINANCE_SECRET_KEY=your-secret-key

# OpenAI API Key
OPENAI_API_KEY=your-openai-key

# NewsAPI Key (optional)
NEWS_API_KEY=your-newsapi-key
```

### Security Best Practices

1. **Change the default PIN** - Update `BOT_CONTROL_PIN` to a secure 6-digit number
2. **Use strong secret key** - Generate a random `FLASK_SECRET_KEY`
3. **Enable HTTPS** - Use a reverse proxy (nginx) with SSL/TLS in production
4. **Whitelist IPs** - Configure firewall rules to restrict access
5. **Regular updates** - Keep dependencies updated

## API Endpoints

### Authentication
- `GET/POST /login` - Login page
- `GET /logout` - Logout
- `GET/POST /change-pin` - Change PIN

### Dashboard
- `GET /` - Main dashboard (requires auth)

### API Endpoints (requires auth)
- `GET /api/bot-status` - Bot status and metrics
- `GET /api/market-data` - Current market data
- `GET /api/performance-metrics` - Trading performance
- `GET /api/recent-trades` - Recent trades (limit parameter)
- `GET /api/recent-signals` - Recent signals (limit parameter)
- `GET /api/open-positions` - Open positions
- `GET /api/system-health` - System resource usage
- `GET /api/chart-analysis` - Latest AI analysis
- `GET /api/market-context` - Cross-asset data
- `GET /api/logs` - Log entries (type and lines parameters)

### Control Endpoints (requires auth)
- `POST /api/control/pause` - Pause/resume trading
- `POST /api/control/emergency-close` - Close all positions
- `POST /api/control/trading-mode` - Change trading mode

## Browser Compatibility

Tested and working on:
- ✅ Google Chrome (latest)
- ✅ Mozilla Firefox (latest)
- ✅ Safari (latest)
- ✅ Microsoft Edge (latest)

## Mobile Responsiveness

The dashboard is fully responsive and works on:
- Desktop (1920x1080 and above)
- Laptop (1366x768)
- Tablet (768x1024)
- Mobile (375x667 and above)

## Features Overview

### Real-time Updates
- Auto-refresh every 30 seconds
- Live data from trading bot
- Real-time chart updates
- System health monitoring

### Visualization
- Chart.js for charts
- Bootstrap 5 for UI components
- Font Awesome for icons
- Custom CSS for styling

### User Experience
- Intuitive navigation
- Color-coded indicators
- Responsive design
- Toast notifications
- Modal dialogs

## Troubleshooting

### Dashboard not accessible

**Symptom**: Cannot access http://localhost:5000

**Solution**:
```bash
# Check if port 5000 is in use
netstat -tulpn | grep 5000

# Check dashboard status
./start_web_dashboard.sh status

# View logs
./start_web_dashboard.sh logs
```

### Session timeout

**Symptom**: Automatically logged out

**Solution**: Sessions expire after 30 minutes of inactivity. This is a security feature. Simply log in again.

### PIN not working

**Symptom**: "Invalid PIN" error

**Solution**:
- Verify PIN in `.env` file is exactly 6 digits
- Restart dashboard after changing .env
- Check for typos

### Charts not rendering

**Symptom**: Empty chart areas

**Solution**:
- Ensure Chart.js is loading (check browser console)
- Verify API endpoints are returning data
- Clear browser cache
- Try different browser

### Data not updating

**Symptom**: Dashboard shows stale data

**Solution**:
- Check if trading bot is running
- Verify database file exists
- Check API responses in browser DevTools
- Restart dashboard

## Development

### Project Structure

```
ai-crypto-trader/
├── web_dashboard.py          # Flask application
├── start_web_dashboard.sh    # Startup script
├── templates/
│   ├── dashboard.html        # Main dashboard
│   ├── login.html           # Login page
│   ├── change_pin.html      # PIN change page
│   ├── 404.html             # Not found page
│   └── 500.html             # Error page
├── static/
│   ├── css/
│   │   └── style.css        # Custom styles
│   └── js/
│       └── dashboard.js     # Dashboard logic
├── requirements-dashboard.txt
├── .env                     # Configuration (create from .env.example)
└── trading_bot.db           # SQLite database
```

### Adding New Features

1. **Backend**: Add API endpoint in `web_dashboard.py`
2. **Frontend**: Add UI component in `templates/dashboard.html`
3. **Styling**: Add styles in `static/css/style.css`
4. **Logic**: Add JavaScript in `static/js/dashboard.js`

### Testing

```bash
# Run with debug mode
export FLASK_DEBUG=True
python3 web_dashboard.py

# Check logs
tail -f web_dashboard.log

# Test API endpoints
curl http://localhost:5000/api/bot-status
```

## Performance Optimization

- Auto-refresh: 30 seconds (configurable)
- Database queries: Optimized with indexes
- Chart rendering: Efficient with Chart.js
- CSS/JS: Minified in production
- Caching: Session-based caching

## Security Considerations

### Implemented
- ✅ PIN-based authentication
- ✅ Session management
- ✅ Session timeout (30 minutes)
- ✅ CSRF protection (Flask default)
- ✅ XSS protection (Bootstrap escaping)
- ✅ Secure cookie flags

### Recommended for Production
- Use HTTPS (nginx + Let's Encrypt)
- Enable rate limiting
- Implement IP whitelist
- Use environment-specific configs
- Enable audit logging
- Regular security updates

## License

MIT License - See main repository for details

## Support

For issues, questions, or contributions:
- Check troubleshooting section
- Review PRP document
- Check system logs

## Version

- **Version**: 1.0.0
- **Last Updated**: 2025-10-07
- **Status**: Production Ready

## Credits

Built according to PRP specifications in `/PRPs/ai-crypto-trading-bot.md`

---

**Note**: This dashboard is part of the AI-Driven Cryptocurrency Trading Bot system. Ensure the trading bot is running before starting the dashboard for full functionality.
