# Backend Infrastructure - AI Crypto Trading Bot

Complete backend implementation including MCP Server, database management, authentication, and API layer.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running the Server](#running-the-server)
7. [API Endpoints](#api-endpoints)
8. [Database Management](#database-management)
9. [Security](#security)
10. [Monitoring & Logging](#monitoring--logging)
11. [Backup & Recovery](#backup--recovery)
12. [Testing](#testing)
13. [Troubleshooting](#troubleshooting)

---

## Overview

The backend infrastructure provides:
- **MCP Server**: RESTful API layer on port 3000
- **Database Management**: SQLite with connection pooling and transaction management
- **Authentication**: PIN-based authentication with JWT tokens
- **Security**: Rate limiting, CORS, input validation
- **Monitoring**: Health checks, comprehensive logging
- **Backup System**: Automated database backups with retention policies

---

## Architecture

```
backend/
├── mcp_server.py           # Main Flask application
├── requirements.txt        # Python dependencies
├── .env.example           # Configuration template
├── API_DOCUMENTATION.md   # Complete API reference
├── database/
│   ├── db_manager.py      # Database connection & query manager
│   ├── migrations.py      # Database schema migrations
│   └── backup.py          # Automated backup system
└── middleware/
    └── auth.py            # Authentication & authorization
```

---

## Features

### MCP Server (Port 3000)

- **15+ API Endpoints** for signals, trades, performance, market context
- **RESTful Design** following industry best practices
- **Rate Limiting** to prevent abuse
- **CORS Support** for cross-origin requests
- **Health Checks** at `/health` and `/api/bot-status`

### Database Layer

- **Thread-Safe Connection Pooling**
- **Transaction Management** with automatic rollback
- **Query Optimization** with proper indexing
- **Data Aggregation** for performance metrics
- **Retention Policies** for data cleanup

### Security

- **PIN-Based Authentication** (6-digit)
- **JWT Token** support with expiration
- **Session Management** with timeout
- **Rate Limiting** per endpoint
- **Input Validation** on all endpoints
- **HTTPS Ready** for production

### Monitoring

- **JSON Structured Logging**
- **Separate Error Logs**
- **Health Check Endpoints**
- **Performance Metrics Tracking**
- **API Usage Analytics**

### Backup System

- **Automated Daily Backups** at 2 AM
- **Gzip Compression** to save space
- **Retention Policy** (default: 30 backups)
- **Backup Verification** integrity checks
- **One-Command Restoration**

---

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Virtual environment (recommended)

### Step 1: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy example configuration
cp .env.example ../.env

# Edit configuration with your values
nano ../.env
```

### Step 4: Initialize Database

```bash
# Run migrations to set up database schema
python3 database/migrations.py
```

---

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Server Configuration
MCP_SERVER_PORT=3000
FLASK_ENV=development

# Security
BOT_CONTROL_PIN=123456          # Change to your 6-digit PIN
FLASK_SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_PATH=trading_bot.db

# Session
SESSION_TIMEOUT_MINUTES=30

# Rate Limiting
RATE_LIMIT_PER_DAY=200
RATE_LIMIT_PER_HOUR=50

# Backups
ENABLE_AUTO_BACKUP=true
BACKUP_SCHEDULE_HOUR=2
MAX_BACKUPS=30
```

See `backend/.env.example` for complete configuration options.

---

## Running the Server

### Quick Start

Use the provided startup script:

```bash
# Start the MCP Server
./start_mcp_server.sh start

# Check status
./start_mcp_server.sh status

# View logs
./start_mcp_server.sh logs

# Stop server
./start_mcp_server.sh stop

# Restart server
./start_mcp_server.sh restart
```

### Manual Start

```bash
cd backend
source ../venv/bin/activate
python3 mcp_server.py
```

### Verify Server is Running

```bash
# Check health endpoint
curl http://localhost:3000/health

# Test bot status endpoint
curl http://localhost:3000/api/bot-status
```

---

## API Endpoints

### Quick Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/api/auth/login` | POST | No | Login with PIN |
| `/api/auth/logout` | POST | No | Logout |
| `/api/bot-status` | GET | No | Bot status |
| `/api/signals` | GET | Optional | Get signals |
| `/api/signals/latest` | GET | No | Latest signal |
| `/api/signals` | POST | Yes | Create signal |
| `/api/trades` | GET | Optional | Get trades |
| `/api/trades/open` | GET | No | Open trades |
| `/api/trades` | POST | Yes | Create trade |
| `/api/performance` | GET | No | Performance metrics |
| `/api/market-context` | GET | No | Market context |
| `/api/analysis/latest` | GET | No | Latest analysis |
| `/api/analysis` | POST | Yes | Store analysis |
| `/api/correlation` | GET | No | Correlation data |
| `/api/cost-analytics` | GET | No | Cost analytics |

### Authentication

#### Login

```bash
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"pin": "123456"}'
```

Response:
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800
}
```

#### Using JWT Token

```bash
curl http://localhost:3000/api/signals \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Example Requests

See `API_DOCUMENTATION.md` for complete API reference with all parameters and response formats.

---

## Database Management

### Schema

The database includes these tables:

**Core Tables:**
- `signals` - Trading signals with indicators
- `trades` - Trade execution records
- `bot_status` - Bot operational status
- `model_checkpoints` - RL model versions

**Enhanced Tables:**
- `market_context` - Cross-asset market data
- `chart_analyses` - AI analysis results
- `performance_metrics` - Performance tracking
- `correlation_data` - Asset correlations
- `cost_analytics` - API usage tracking
- `news_cache` - Cached news sentiment
- `spike_events` - Market spike detection
- `circuit_breaker_events` - Circuit breaker triggers
- `agent_decisions` - Agent decision logs
- `agent_performance` - Agent performance metrics

### Migrations

Run database migrations:

```bash
python3 backend/database/migrations.py
```

### Data Cleanup

Remove old data based on retention policies:

```bash
python3 -c "from backend.database.migrations import cleanup_old_data; cleanup_old_data()"
```

### Database Optimization

Optimize database (VACUUM):

```bash
python3 -c "from backend.database.migrations import vacuum_database; vacuum_database()"
```

---

## Security

### Authentication Setup

1. Set a secure 6-digit PIN in `.env`:
   ```bash
   BOT_CONTROL_PIN=987654
   ```

2. Change secret keys:
   ```bash
   FLASK_SECRET_KEY=$(openssl rand -hex 32)
   JWT_SECRET_KEY=$(openssl rand -hex 32)
   ```

3. Enable HTTPS in production:
   ```bash
   FORCE_HTTPS=true
   ```

### Rate Limiting

Default limits:
- 200 requests per day
- 50 requests per hour
- Login: 5 attempts per 15 minutes

Customize in `.env`:
```bash
RATE_LIMIT_PER_DAY=500
RATE_LIMIT_PER_HOUR=100
```

### Security Best Practices

1. Use HTTPS in production
2. Set strong secret keys
3. Change default PIN
4. Enable IP whitelisting (if applicable)
5. Monitor authentication logs
6. Regularly update dependencies

---

## Monitoring & Logging

### Log Files

- **Main Log**: `logs/mcp_server.log`
- **Error Log**: `logs/mcp_server_error.log`

### View Logs

```bash
# Tail main log
./start_mcp_server.sh logs

# Tail error log
./start_mcp_server.sh errors

# View logs directly
tail -f logs/mcp_server.log
```

### Health Monitoring

Check system health:

```bash
curl http://localhost:3000/health | jq
```

Check bot status:

```bash
curl http://localhost:3000/api/bot-status | jq
```

### Performance Metrics

Get performance analytics:

```bash
curl http://localhost:3000/api/performance | jq
```

Get cost analytics:

```bash
curl http://localhost:3000/api/cost-analytics | jq
```

---

## Backup & Recovery

### Automated Backups

Backups run automatically at 2 AM daily (configurable).

Start backup service:

```bash
python3 backend/database/backup.py service
```

### Manual Backup

Create backup immediately:

```bash
python3 backend/database/backup.py backup
```

### List Backups

```bash
python3 backend/database/backup.py list
```

### Restore from Backup

Restore latest backup:

```bash
python3 backend/database/backup.py restore
```

### Verify Backups

Check backup integrity:

```bash
python3 backend/database/backup.py verify
```

### Backup Location

Backups are stored in `backups/` directory with format:
- `trading_bot_backup_YYYYMMDD_HHMMSS.db.gz` (compressed)
- `trading_bot_backup_YYYYMMDD_HHMMSS.db` (uncompressed)

---

## Testing

### Test Endpoints

Use the built-in test command:

```bash
./start_mcp_server.sh test
```

### Manual Testing with curl

```bash
# Health check
curl http://localhost:3000/health

# Get latest signal
curl http://localhost:3000/api/signals/latest

# Get performance metrics
curl http://localhost:3000/api/performance

# Login
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"pin": "123456"}'
```

### Test with Postman

Import the API documentation into Postman for interactive testing.

---

## Troubleshooting

### Server Won't Start

**Issue**: Port already in use

```bash
# Find process using port 3000
lsof -i :3000

# Kill process if needed
kill -9 <PID>
```

**Issue**: Missing dependencies

```bash
pip install -r backend/requirements.txt
```

**Issue**: Database locked

```bash
# Stop all services accessing the database
./start_mcp_server.sh stop

# Wait a moment, then restart
./start_mcp_server.sh start
```

### Authentication Issues

**Issue**: Invalid PIN

- Check `.env` file has correct `BOT_CONTROL_PIN`
- PIN must be exactly 6 digits
- Restart server after changing PIN

**Issue**: Token expired

- Tokens expire after 30 minutes (configurable)
- Login again to get new token

### Database Issues

**Issue**: Schema mismatch

```bash
# Run migrations
python3 backend/database/migrations.py
```

**Issue**: Corrupted database

```bash
# Restore from backup
python3 backend/database/backup.py restore
```

### Performance Issues

**Issue**: Slow queries

```bash
# Optimize database
python3 -c "from backend.database.migrations import vacuum_database; vacuum_database()"
```

**Issue**: Too many logs

```bash
# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete
```

### Check Logs

Always check logs for detailed error messages:

```bash
tail -100 logs/mcp_server_error.log
```

---

## Integration Points

### Trading Bot Integration

The trading bot can use these endpoints:

1. **Store Signals**: POST `/api/signals`
2. **Store Trades**: POST `/api/trades`
3. **Update Status**: POST `/api/bot-status` (via db_manager)

### Frontend Dashboard Integration

The dashboard can consume:

1. **Get Status**: GET `/api/bot-status`
2. **Get Signals**: GET `/api/signals`
3. **Get Trades**: GET `/api/trades`
4. **Get Performance**: GET `/api/performance`
5. **Get Market Context**: GET `/api/market-context`

### Chart Analysis Bot Integration

The chart bot can:

1. **Store Analysis**: POST `/api/analysis`
2. **Get Latest Analysis**: GET `/api/analysis/latest`

---

## Production Deployment

### Checklist

- [ ] Change all secret keys in `.env`
- [ ] Set secure 6-digit PIN
- [ ] Enable HTTPS (`FORCE_HTTPS=true`)
- [ ] Set `FLASK_ENV=production`
- [ ] Configure proper CORS origins
- [ ] Set up automated backups
- [ ] Configure log rotation
- [ ] Set up monitoring/alerts
- [ ] Enable firewall rules
- [ ] Test all endpoints

### Recommended Stack

- **Reverse Proxy**: Nginx or Apache
- **Process Manager**: systemd or supervisor
- **SSL/TLS**: Let's Encrypt certificates
- **Monitoring**: Prometheus + Grafana (optional)
- **Logging**: Centralized logging (optional)

---

## Support

For issues or questions:

1. Check this README
2. Review `API_DOCUMENTATION.md`
3. Check logs in `logs/` directory
4. Review PRP file at `PRPs/ai-crypto-trading-bot.md`

---

## License

Part of AI-Driven Cryptocurrency Trading Bot project.
