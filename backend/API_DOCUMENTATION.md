# MCP Server API Documentation

Version: 1.0
Base URL: `http://localhost:3000`
Protocol: HTTP/HTTPS
Authentication: JWT Bearer Token or Session-based

---

## Table of Contents

1. [Authentication](#authentication)
2. [Health & Status](#health--status)
3. [Signals](#signals)
4. [Trades](#trades)
5. [Performance Metrics](#performance-metrics)
6. [Market Context](#market-context)
7. [Analysis](#analysis)
8. [Correlation Data](#correlation-data)
9. [Cost Analytics](#cost-analytics)
10. [Error Codes](#error-codes)

---

## Authentication

### POST /api/auth/login

Authenticate with PIN and receive JWT token.

**Request Body:**
```json
{
  "pin": "123456"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Authentication successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800
}
```

**Rate Limit:** 5 requests per 15 minutes

---

### POST /api/auth/logout

Logout and clear session.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

### GET /api/auth/check

Check current authentication status.

**Response (200 OK):**
```json
{
  "authenticated": true,
  "expires_in": 1234
}
```

---

## Health & Status

### GET /health

System health check endpoint.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "MCP Server",
  "version": "1.0",
  "timestamp": "2025-10-07T12:00:00.000Z",
  "database": "connected"
}
```

**No Rate Limit**

---

### GET /api/bot-status

Get current bot status.

**Query Parameters:**
- `bot_name` (optional): Name of bot to query (default: "rl_trading_bot")

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "timestamp": "2025-10-07T12:00:00",
    "bot_name": "rl_trading_bot",
    "status": "running",
    "pid": 12345,
    "balance": 1000.50,
    "open_positions": 1,
    "total_trades": 50,
    "win_rate": 65.5,
    "total_pnl": 150.25
  }
}
```

**Rate Limit:** 100 requests per minute

---

## Signals

### GET /api/signals

Get recent signal history with optional filtering.

**Query Parameters:**
- `limit` (optional): Number of signals (default: 50, max: 500)
- `trading_pair` (optional): Filter by trading pair
- `signal_type` (optional): Filter by type (BUY, SELL, HOLD)
- `from_date` (optional): Start date (ISO format)
- `to_date` (optional): End date (ISO format)

**Response (200 OK):**
```json
{
  "success": true,
  "count": 10,
  "data": [
    {
      "id": 1,
      "timestamp": "2025-10-07T12:00:00",
      "trading_pair": "SUI/USDC",
      "signal_type": "BUY",
      "signal_strength": 5,
      "price": 1.234,
      "rsi": 45.5,
      "macd": 0.0123,
      "macd_signal": 0.0100,
      "macd_histogram": 0.0023,
      "vwap": 1.235,
      "ema9": 1.230,
      "ema21": 1.225,
      "sma50": 1.220,
      "bb_upper": 1.250,
      "bb_middle": 1.235,
      "bb_lower": 1.220,
      "volume": 123456.78,
      "status": "pending"
    }
  ]
}
```

**Rate Limit:** 200 requests per minute

---

### GET /api/signals/latest

Get the latest signal.

**Query Parameters:**
- `trading_pair` (optional): Filter by trading pair

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "timestamp": "2025-10-07T12:00:00",
    "trading_pair": "SUI/USDC",
    "signal_type": "BUY",
    "signal_strength": 5,
    "price": 1.234
  }
}
```

**Rate Limit:** 300 requests per minute

---

### POST /api/signals

Create a new signal (requires authentication).

**Request Body:**
```json
{
  "trading_pair": "SUI/USDC",
  "signal_type": "BUY",
  "signal_strength": 5,
  "price": 1.234,
  "rsi": 45.5,
  "macd": 0.0123,
  "vwap": 1.235
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Signal created successfully",
  "signal_id": 123
}
```

**Rate Limit:** 100 requests per minute
**Authentication Required:** Yes

---

## Trades

### GET /api/trades

Get trade execution history.

**Query Parameters:**
- `limit` (optional): Number of trades (default: 50, max: 500)
- `trading_pair` (optional): Filter by trading pair
- `status` (optional): Filter by status (open, closed)
- `from_date` (optional): Start date (ISO format)
- `to_date` (optional): End date (ISO format)

**Response (200 OK):**
```json
{
  "success": true,
  "count": 5,
  "data": [
    {
      "id": 1,
      "timestamp": "2025-10-07T12:00:00",
      "trading_pair": "SUI/USDC",
      "side": "BUY",
      "entry_price": 1.234,
      "exit_price": 1.250,
      "quantity": 100.0,
      "pnl": 1.60,
      "status": "closed",
      "signal_id": 123,
      "leverage": 50,
      "position_mode": "one-way",
      "stop_loss": 1.210,
      "take_profit": 1.270,
      "closed_at": "2025-10-07T13:00:00"
    }
  ]
}
```

**Rate Limit:** 200 requests per minute

---

### GET /api/trades/open

Get all open trades.

**Query Parameters:**
- `trading_pair` (optional): Filter by trading pair

**Response (200 OK):**
```json
{
  "success": true,
  "count": 1,
  "data": [
    {
      "id": 2,
      "timestamp": "2025-10-07T12:30:00",
      "trading_pair": "SUI/USDC",
      "side": "BUY",
      "entry_price": 1.240,
      "quantity": 50.0,
      "status": "open",
      "leverage": 50
    }
  ]
}
```

**Rate Limit:** 300 requests per minute

---

### POST /api/trades

Create a new trade (requires authentication).

**Request Body:**
```json
{
  "trading_pair": "SUI/USDC",
  "side": "BUY",
  "entry_price": 1.234,
  "quantity": 100.0,
  "leverage": 50,
  "position_mode": "one-way",
  "signal_id": 123
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Trade created successfully",
  "trade_id": 456
}
```

**Rate Limit:** 100 requests per minute
**Authentication Required:** Yes

---

## Performance Metrics

### GET /api/performance

Get performance metrics.

**Query Parameters:**
- `period` (optional): Time period (daily, weekly, monthly, all) - default: all

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "total_trades": 100,
    "winning_trades": 60,
    "losing_trades": 40,
    "win_rate": 60.0,
    "total_pnl": 250.50,
    "avg_win": 8.50,
    "avg_loss": -5.25,
    "max_loss": -15.00,
    "max_win": 25.00,
    "risk_reward_ratio": 1.62
  }
}
```

**Rate Limit:** 100 requests per minute

---

## Market Context

### GET /api/market-context

Get latest cross-asset market context data.

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "timestamp": "2025-10-07T12:00:00",
    "btc_price": 65000.50,
    "btc_change_24h": 2.5,
    "eth_price": 3200.25,
    "eth_change_24h": 1.8,
    "btc_dominance": 52.5,
    "fear_greed_index": 65,
    "market_trend": "bullish",
    "btc_trend": "up_strong",
    "market_regime": "risk_on",
    "volatility_level": "medium"
  }
}
```

**Rate Limit:** 200 requests per minute

---

### GET /api/market-context/history

Get historical market context data.

**Query Parameters:**
- `limit` (optional): Number of records (default: 100, max: 500)
- `hours` (optional): Time range in hours (default: 24)

**Response (200 OK):**
```json
{
  "success": true,
  "count": 10,
  "data": [...]
}
```

**Rate Limit:** 100 requests per minute

---

## Analysis

### GET /api/analysis/latest

Get latest chart analysis.

**Query Parameters:**
- `trading_pair` (optional): Filter by trading pair

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "timestamp": "2025-10-07T12:00:00",
    "trading_pair": "SUI/USDC",
    "timeframe": "15m",
    "recommendation": "BUY",
    "confidence": "high",
    "key_observations": "Strong uptrend with volume confirmation",
    "risk_factors": "Overbought RSI levels",
    "ai_analysis": "Market showing bullish momentum...",
    "support_levels": "1.20, 1.18",
    "resistance_levels": "1.35, 1.40",
    "chart_image_path": "/path/to/chart.png"
  }
}
```

**Rate Limit:** 200 requests per minute

---

### POST /api/analysis

Store analysis results (requires authentication).

**Request Body:**
```json
{
  "trading_pair": "SUI/USDC",
  "timeframe": "15m",
  "recommendation": "BUY",
  "confidence": "high",
  "key_observations": "Strong uptrend",
  "risk_factors": "Overbought RSI",
  "ai_analysis": "Market analysis text..."
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Analysis stored successfully",
  "analysis_id": 789
}
```

**Rate Limit:** 100 requests per minute
**Authentication Required:** Yes

---

## Correlation Data

### GET /api/correlation

Get cross-asset correlation data.

**Query Parameters:**
- `asset1` (optional): First asset
- `asset2` (optional): Second asset
- `period_days` (optional): Correlation period in days (default: 7)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "timestamp": "2025-10-07T12:00:00",
    "asset1": "BTC",
    "asset2": "SUI",
    "correlation_value": 0.85,
    "period_days": 7,
    "strength": "strong"
  }
}
```

**Rate Limit:** 100 requests per minute

---

## Cost Analytics

### GET /api/cost-analytics

Get API usage and cost analytics.

**Query Parameters:**
- `api_name` (optional): Filter by API (openai, binance, newsapi)
- `hours` (optional): Time range in hours (default: 24)

**Response (200 OK):**
```json
{
  "success": true,
  "period_hours": 24,
  "data": [
    {
      "api_name": "openai",
      "operation_type": "chat_completion",
      "total_calls": 100,
      "total_cost": 0.50,
      "total_cache_hits": 80,
      "total_cache_misses": 20,
      "cache_hit_rate": 80.0
    }
  ]
}
```

**Rate Limit:** 100 requests per minute

---

## Error Codes

### Standard HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required or failed
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

### Error Response Format

```json
{
  "success": false,
  "error": "Error type",
  "message": "Detailed error message"
}
```

---

## Authentication

All protected endpoints require either:

1. **JWT Bearer Token** in Authorization header:
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. **Session Cookie** (obtained via /api/auth/login)

---

## Rate Limiting

Default rate limits:
- Public endpoints: 200 requests/day, 50 requests/hour
- Per-endpoint limits may vary (see individual endpoints)

Rate limit headers in response:
```
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1633024800
```

---

## CORS

CORS is enabled for all `/api/*` endpoints with the following configuration:
- Origins: Configurable via environment variable
- Methods: GET, POST, PUT, DELETE, OPTIONS
- Headers: Content-Type, Authorization

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- All monetary values are in USDC
- Price values are decimal numbers with up to 8 decimal places
- All endpoints return JSON responses

---

**Support:** For issues or questions, please check the logs at `/logs/mcp_server.log`
