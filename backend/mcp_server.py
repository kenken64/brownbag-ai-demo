"""
MCP (Model Context Protocol) Server for AI Crypto Trading Bot
RESTful API layer for database operations and data aggregation
Version: 1.0
Port: 3000
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pythonjsonlogger import jsonlogger

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.db_manager import db_manager
from backend.middleware.auth import (
    auth_manager, require_auth, optional_auth,
    login_endpoint, logout_endpoint, check_auth_endpoint
)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default-secret-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configure logging
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s'
)
log_handler.setFormatter(formatter)

logger = logging.getLogger('mcp_server')
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


# ============================================================================
# HEALTH CHECK & STATUS ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
@limiter.exempt
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_manager.execute_query("SELECT 1")

        return jsonify({
            'status': 'healthy',
            'service': 'MCP Server',
            'version': '1.0',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@app.route('/api/bot-status', methods=['GET'])
@limiter.limit("100 per minute")
def get_bot_status():
    """Get current bot status"""
    try:
        bot_name = request.args.get('bot_name', 'rl_trading_bot')
        status = db_manager.get_bot_status(bot_name)

        if not status:
            return jsonify({
                'success': False,
                'error': 'Bot status not found'
            }), 404

        return jsonify({
            'success': True,
            'data': status
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving bot status: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve bot status'
        }), 500


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per 15 minutes")
def login():
    """User login with PIN"""
    return login_endpoint()


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout"""
    return logout_endpoint()


@app.route('/api/auth/check', methods=['GET'])
@limiter.exempt
def check_auth():
    """Check authentication status"""
    return check_auth_endpoint()


# ============================================================================
# SIGNAL ENDPOINTS
# ============================================================================

@app.route('/api/signals', methods=['GET'])
@limiter.limit("200 per minute")
@optional_auth
def get_signals():
    """
    Get recent signal history

    Query parameters:
    - limit: Number of signals to return (default: 50, max: 500)
    - trading_pair: Filter by trading pair (optional)
    - signal_type: Filter by signal type (BUY, SELL, HOLD)
    - from_date: Start date for filtering (ISO format)
    - to_date: End date for filtering (ISO format)
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 500)
        trading_pair = request.args.get('trading_pair')
        signal_type = request.args.get('signal_type')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        # Build query
        query = "SELECT * FROM signals WHERE 1=1"
        params = []

        if trading_pair:
            query += " AND trading_pair = ?"
            params.append(trading_pair)

        if signal_type:
            query += " AND signal_type = ?"
            params.append(signal_type)

        if from_date:
            query += " AND timestamp >= ?"
            params.append(from_date)

        if to_date:
            query += " AND timestamp <= ?"
            params.append(to_date)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        signals = db_manager.execute_query(query, tuple(params))

        return jsonify({
            'success': True,
            'count': len(signals),
            'data': signals
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving signals: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve signals'
        }), 500


@app.route('/api/signals/latest', methods=['GET'])
@limiter.limit("300 per minute")
def get_latest_signal():
    """Get the latest signal"""
    try:
        trading_pair = request.args.get('trading_pair')
        signal = db_manager.get_latest_signal(trading_pair)

        if not signal:
            return jsonify({
                'success': False,
                'error': 'No signals found'
            }), 404

        return jsonify({
            'success': True,
            'data': signal
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving latest signal: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve latest signal'
        }), 500


@app.route('/api/signals', methods=['POST'])
@limiter.limit("100 per minute")
@require_auth
def create_signal():
    """Create a new signal"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        # Validate required fields
        required_fields = ['trading_pair', 'signal_type', 'signal_strength', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Insert signal
        signal_id = db_manager.insert_signal(data)

        return jsonify({
            'success': True,
            'message': 'Signal created successfully',
            'signal_id': signal_id
        }), 201

    except Exception as e:
        logger.error(f"Error creating signal: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create signal'
        }), 500


# ============================================================================
# TRADE ENDPOINTS
# ============================================================================

@app.route('/api/trades', methods=['GET'])
@limiter.limit("200 per minute")
@optional_auth
def get_trades():
    """
    Get trade execution history

    Query parameters:
    - limit: Number of trades to return (default: 50, max: 500)
    - trading_pair: Filter by trading pair (optional)
    - status: Filter by status (open, closed)
    - from_date: Start date for filtering (ISO format)
    - to_date: End date for filtering (ISO format)
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 500)
        trading_pair = request.args.get('trading_pair')
        status = request.args.get('status')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        # Build query
        query = "SELECT * FROM trades WHERE 1=1"
        params = []

        if trading_pair:
            query += " AND trading_pair = ?"
            params.append(trading_pair)

        if status:
            query += " AND status = ?"
            params.append(status)

        if from_date:
            query += " AND timestamp >= ?"
            params.append(from_date)

        if to_date:
            query += " AND timestamp <= ?"
            params.append(to_date)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        trades = db_manager.execute_query(query, tuple(params))

        return jsonify({
            'success': True,
            'count': len(trades),
            'data': trades
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving trades: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve trades'
        }), 500


@app.route('/api/trades/open', methods=['GET'])
@limiter.limit("300 per minute")
def get_open_trades():
    """Get all open trades"""
    try:
        trading_pair = request.args.get('trading_pair')
        trades = db_manager.get_open_trades(trading_pair)

        return jsonify({
            'success': True,
            'count': len(trades),
            'data': trades
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving open trades: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve open trades'
        }), 500


@app.route('/api/trades', methods=['POST'])
@limiter.limit("100 per minute")
@require_auth
def create_trade():
    """Create a new trade"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        # Validate required fields
        required_fields = ['trading_pair', 'side', 'entry_price', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Insert trade
        trade_id = db_manager.insert_trade(data)

        return jsonify({
            'success': True,
            'message': 'Trade created successfully',
            'trade_id': trade_id
        }), 201

    except Exception as e:
        logger.error(f"Error creating trade: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create trade'
        }), 500


# ============================================================================
# PERFORMANCE ENDPOINTS
# ============================================================================

@app.route('/api/performance', methods=['GET'])
@limiter.limit("100 per minute")
def get_performance():
    """
    Get performance metrics

    Query parameters:
    - period: Time period for metrics (daily, weekly, monthly, all)
    """
    try:
        period = request.args.get('period', 'all')

        # Get metrics from database
        metrics = db_manager.get_performance_metrics(period)

        if not metrics:
            return jsonify({
                'success': True,
                'data': {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'max_loss': 0.0,
                    'risk_reward_ratio': 0.0
                }
            }), 200

        return jsonify({
            'success': True,
            'data': metrics
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving performance metrics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve performance metrics'
        }), 500


# ============================================================================
# MARKET CONTEXT ENDPOINTS
# ============================================================================

@app.route('/api/market-context', methods=['GET'])
@limiter.limit("200 per minute")
def get_market_context():
    """
    Get cross-asset market context data

    Returns latest market context including BTC/ETH data, Fear & Greed Index, etc.
    """
    try:
        context = db_manager.get_latest_market_context()

        if not context:
            return jsonify({
                'success': False,
                'error': 'No market context data available'
            }), 404

        return jsonify({
            'success': True,
            'data': context
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving market context: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve market context'
        }), 500


@app.route('/api/market-context/history', methods=['GET'])
@limiter.limit("100 per minute")
def get_market_context_history():
    """Get historical market context data"""
    try:
        limit = min(int(request.args.get('limit', 100)), 500)
        hours = int(request.args.get('hours', 24))

        # Calculate time range
        from_date = datetime.utcnow() - timedelta(hours=hours)

        query = """
            SELECT * FROM market_context
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT ?
        """

        context_history = db_manager.execute_query(query, (from_date.isoformat(), limit))

        return jsonify({
            'success': True,
            'count': len(context_history),
            'data': context_history
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving market context history: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve market context history'
        }), 500


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@app.route('/api/analysis/latest', methods=['GET'])
@limiter.limit("200 per minute")
def get_latest_analysis():
    """Get latest chart analysis"""
    try:
        trading_pair = request.args.get('trading_pair')
        analysis = db_manager.get_latest_chart_analysis(trading_pair)

        if not analysis:
            return jsonify({
                'success': False,
                'error': 'No analysis data available'
            }), 404

        return jsonify({
            'success': True,
            'data': analysis
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving latest analysis: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve latest analysis'
        }), 500


@app.route('/api/analysis', methods=['POST'])
@limiter.limit("100 per minute")
@require_auth
def store_analysis():
    """
    Store analysis results

    Expected JSON body:
    {
        "trading_pair": "SUI/USDC",
        "timeframe": "15m",
        "recommendation": "BUY",
        "confidence": "high",
        "key_observations": "...",
        "risk_factors": "...",
        "ai_analysis": "..."
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        # Validate required fields
        required_fields = ['trading_pair', 'timeframe', 'recommendation']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Insert analysis
        query = """
            INSERT INTO chart_analyses (
                trading_pair, timeframe, recommendation, confidence,
                key_observations, risk_factors, ai_analysis,
                support_levels, resistance_levels, chart_image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            data.get('trading_pair'),
            data.get('timeframe'),
            data.get('recommendation'),
            data.get('confidence'),
            data.get('key_observations'),
            data.get('risk_factors'),
            data.get('ai_analysis'),
            data.get('support_levels'),
            data.get('resistance_levels'),
            data.get('chart_image_path')
        )

        analysis_id = db_manager.execute_insert(query, params)

        return jsonify({
            'success': True,
            'message': 'Analysis stored successfully',
            'analysis_id': analysis_id
        }), 201

    except Exception as e:
        logger.error(f"Error storing analysis: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to store analysis'
        }), 500


# ============================================================================
# CORRELATION DATA ENDPOINTS
# ============================================================================

@app.route('/api/correlation', methods=['GET'])
@limiter.limit("100 per minute")
def get_correlation_data():
    """Get cross-asset correlation data"""
    try:
        asset1 = request.args.get('asset1')
        asset2 = request.args.get('asset2')
        period_days = int(request.args.get('period_days', 7))

        query = "SELECT * FROM correlation_data WHERE 1=1"
        params = []

        if asset1:
            query += " AND asset1 = ?"
            params.append(asset1)

        if asset2:
            query += " AND asset2 = ?"
            params.append(asset2)

        query += " AND period_days = ? ORDER BY timestamp DESC LIMIT 1"
        params.append(period_days)

        correlation = db_manager.execute_query(query, tuple(params))

        return jsonify({
            'success': True,
            'data': correlation[0] if correlation else None
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving correlation data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve correlation data'
        }), 500


# ============================================================================
# COST ANALYTICS ENDPOINTS
# ============================================================================

@app.route('/api/cost-analytics', methods=['GET'])
@limiter.limit("100 per minute")
def get_cost_analytics():
    """Get API usage and cost analytics"""
    try:
        api_name = request.args.get('api_name')
        hours = int(request.args.get('hours', 24))

        from_date = datetime.utcnow() - timedelta(hours=hours)

        query = """
            SELECT
                api_name,
                operation_type,
                SUM(api_calls) as total_calls,
                SUM(estimated_cost) as total_cost,
                SUM(cache_hits) as total_cache_hits,
                SUM(cache_misses) as total_cache_misses
            FROM cost_analytics
            WHERE timestamp >= ?
        """
        params = [from_date.isoformat()]

        if api_name:
            query += " AND api_name = ?"
            params.append(api_name)

        query += " GROUP BY api_name, operation_type"

        analytics = db_manager.execute_query(query, tuple(params))

        # Calculate cache hit rate
        for item in analytics:
            total_requests = item['total_cache_hits'] + item['total_cache_misses']
            item['cache_hit_rate'] = (item['total_cache_hits'] / total_requests * 100) if total_requests > 0 else 0

        return jsonify({
            'success': True,
            'period_hours': hours,
            'data': analytics
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving cost analytics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve cost analytics'
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit errors"""
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': str(e.description)
    }), 429


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('MCP_SERVER_PORT', 3000))
    debug = os.getenv('FLASK_ENV') != 'production'

    logger.info(f"Starting MCP Server on port {port}")
    logger.info(f"Debug mode: {debug}")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
