#!/usr/bin/env python3
"""
MCP (Model-Context-Protocol) Server for AI Crypto Trading Bot
RESTful API layer for optimized database queries
Port: 3000 (default)
"""

import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import TradingDatabase

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JSON_SORT_KEYS'] = False

# Initialize database with connection pooling
db = TradingDatabase()

# Configuration
MCP_PORT = int(os.getenv('MCP_PORT', 3000))
MCP_HOST = os.getenv('MCP_HOST', '0.0.0.0')


# ============================================================================
# SIGNAL ENDPOINTS
# ============================================================================

@app.route('/api/v1/signals', methods=['GET'])
def get_signals():
    """
    Get trading signals with optional filters

    Query params:
        - limit: Max results (default: 100, max: 1000)
        - offset: Pagination offset (default: 0)
        - signal_type: Filter by BUY/SELL/HOLD
        - min_strength: Minimum signal strength
        - start_date: Start timestamp (ISO format)
        - end_date: End timestamp (ISO format)
    """
    try:
        limit = min(int(request.args.get('limit', 100)), 1000)
        offset = int(request.args.get('offset', 0))
        signal_type = request.args.get('signal_type')
        min_strength = request.args.get('min_strength', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        conn = db.get_connection()
        cursor = conn.cursor()

        # Build dynamic query
        query = 'SELECT * FROM signals WHERE 1=1'
        params = []

        if signal_type:
            query += ' AND signal_type = ?'
            params.append(signal_type)

        if min_strength:
            query += ' AND signal_strength >= ?'
            params.append(min_strength)

        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)

        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date)

        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        signals = cursor.fetchall()

        # Convert to list of dicts
        result = []
        for signal in signals:
            result.append({
                'id': signal['id'],
                'timestamp': signal['timestamp'],
                'price': float(signal['price']),
                'rsi': float(signal['rsi']) if signal['rsi'] else None,
                'macd': float(signal['macd']) if signal['macd'] else None,
                'macd_signal': float(signal['macd_signal']) if signal['macd_signal'] else None,
                'vwap': float(signal['vwap']) if signal['vwap'] else None,
                'ema_9': float(signal['ema_9']) if signal['ema_9'] else None,
                'ema_21': float(signal['ema_21']) if signal['ema_21'] else None,
                'sma_50': float(signal['sma_50']) if signal['sma_50'] else None,
                'bb_upper': float(signal['bb_upper']) if signal['bb_upper'] else None,
                'bb_lower': float(signal['bb_lower']) if signal['bb_lower'] else None,
                'signal_type': signal['signal_type'],
                'signal_strength': int(signal['signal_strength'])
            })

        return jsonify({
            'success': True,
            'count': len(result),
            'limit': limit,
            'offset': offset,
            'data': result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/signals/stats', methods=['GET'])
def get_signal_stats():
    """Get aggregated signal statistics"""
    try:
        hours = int(request.args.get('hours', 24))
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        conn = db.get_connection()
        cursor = conn.cursor()

        # Count by signal type
        cursor.execute('''
            SELECT signal_type, COUNT(*) as count
            FROM signals
            WHERE timestamp >= ?
            GROUP BY signal_type
        ''', (start_time,))

        type_counts = {row['signal_type']: row['count'] for row in cursor.fetchall()}

        # Average signal strength
        cursor.execute('''
            SELECT AVG(signal_strength) as avg_strength
            FROM signals
            WHERE timestamp >= ?
        ''', (start_time,))

        avg_strength = cursor.fetchone()['avg_strength']

        return jsonify({
            'success': True,
            'period_hours': hours,
            'total_signals': sum(type_counts.values()),
            'buy_signals': type_counts.get('BUY', 0),
            'sell_signals': type_counts.get('SELL', 0),
            'hold_signals': type_counts.get('HOLD', 0),
            'avg_signal_strength': round(avg_strength, 2) if avg_strength else 0
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# TRADE ENDPOINTS
# ============================================================================

@app.route('/api/v1/trades', methods=['GET'])
def get_trades():
    """
    Get trades with optional filters

    Query params:
        - limit: Max results (default: 100, max: 1000)
        - offset: Pagination offset
        - status: open/closed
        - side: BUY/SELL
        - min_pnl: Minimum PnL
        - max_pnl: Maximum PnL
    """
    try:
        limit = min(int(request.args.get('limit', 100)), 1000)
        offset = int(request.args.get('offset', 0))
        status = request.args.get('status')  # open/closed
        side = request.args.get('side')
        min_pnl = request.args.get('min_pnl', type=float)
        max_pnl = request.args.get('max_pnl', type=float)

        conn = db.get_connection()
        cursor = conn.cursor()

        # Build query
        query = 'SELECT * FROM trades WHERE 1=1'
        params = []

        if status == 'open':
            query += ' AND exit_price IS NULL'
        elif status == 'closed':
            query += ' AND exit_price IS NOT NULL'

        if side:
            query += ' AND side = ?'
            params.append(side)

        if min_pnl is not None:
            query += ' AND pnl >= ?'
            params.append(min_pnl)

        if max_pnl is not None:
            query += ' AND pnl <= ?'
            params.append(max_pnl)

        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        trades = cursor.fetchall()

        result = []
        for trade in trades:
            result.append({
                'id': trade['id'],
                'timestamp': trade['timestamp'],
                'side': trade['side'],
                'entry_price': float(trade['entry_price']),
                'exit_price': float(trade['exit_price']) if trade['exit_price'] else None,
                'quantity': float(trade['quantity']),
                'leverage': int(trade['leverage']) if trade['leverage'] else 1,
                'pnl': float(trade['pnl']) if trade['pnl'] else None,
                'pnl_percentage': float(trade['pnl_percentage']) if trade['pnl_percentage'] else None,
                'exit_reason': trade['exit_reason'],
                'signal_id': trade['signal_id']
            })

        return jsonify({
            'success': True,
            'count': len(result),
            'limit': limit,
            'offset': offset,
            'data': result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/trades/performance', methods=['GET'])
def get_trade_performance():
    """Get comprehensive trade performance metrics"""
    try:
        hours = int(request.args.get('hours', 0))  # 0 = all time

        conn = db.get_connection()
        cursor = conn.cursor()

        # Build time filter
        time_filter = ''
        params = []
        if hours > 0:
            start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            time_filter = 'AND timestamp >= ?'
            params.append(start_time)

        # Get all closed trades
        cursor.execute(f'''
            SELECT * FROM trades
            WHERE exit_price IS NOT NULL
            {time_filter}
            ORDER BY timestamp DESC
        ''', params)

        trades = cursor.fetchall()

        if not trades:
            return jsonify({
                'success': True,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'max_win': 0,
                'max_loss': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0
            })

        # Calculate metrics
        winning_trades = [t for t in trades if t['pnl'] and t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] and t['pnl'] < 0]

        total_wins = sum(t['pnl'] for t in winning_trades)
        total_losses = abs(sum(t['pnl'] for t in losing_trades))
        total_pnl = sum(t['pnl'] for t in trades if t['pnl'])

        # Calculate Sharpe ratio (simplified)
        pnl_values = [t['pnl'] for t in trades if t['pnl']]
        if len(pnl_values) > 1:
            import statistics
            mean_pnl = statistics.mean(pnl_values)
            std_pnl = statistics.stdev(pnl_values)
            sharpe_ratio = (mean_pnl / std_pnl) if std_pnl > 0 else 0
        else:
            sharpe_ratio = 0

        return jsonify({
            'success': True,
            'period_hours': hours if hours > 0 else 'all_time',
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round((len(winning_trades) / len(trades)) * 100, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_pnl': round(total_pnl / len(trades), 2),
            'avg_win': round(total_wins / len(winning_trades), 2) if winning_trades else 0,
            'avg_loss': round(total_losses / len(losing_trades), 2) if losing_trades else 0,
            'max_win': round(max((t['pnl'] for t in winning_trades), default=0), 2),
            'max_loss': round(abs(min((t['pnl'] for t in losing_trades), default=0)), 2),
            'profit_factor': round(total_wins / total_losses, 2) if total_losses > 0 else 0,
            'sharpe_ratio': round(sharpe_ratio, 2)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# MARKET CONTEXT ENDPOINTS
# ============================================================================

@app.route('/api/v1/market-context', methods=['GET'])
def get_market_context():
    """Get current market context"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM market_context
            ORDER BY timestamp DESC
            LIMIT 1
        ''')

        context = cursor.fetchone()

        if context:
            return jsonify({
                'success': True,
                'data': {
                    'timestamp': context['timestamp'],
                    'btc_price': float(context['btc_price']),
                    'eth_price': float(context['eth_price']),
                    'fear_greed_index': int(context['fear_greed_index']),
                    'market_trend': context['market_trend'],
                    'btc_dominance': float(context['btc_dominance']) if context['btc_dominance'] else None,
                    'total_market_cap': float(context['total_market_cap']) if context['total_market_cap'] else None
                }
            })
        else:
            return jsonify({'success': False, 'error': 'No market context available'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/market-context/history', methods=['GET'])
def get_market_context_history():
    """Get historical market context"""
    try:
        hours = int(request.args.get('hours', 24))
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM market_context
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        ''', (start_time,))

        contexts = cursor.fetchall()

        result = []
        for ctx in contexts:
            result.append({
                'timestamp': ctx['timestamp'],
                'btc_price': float(ctx['btc_price']),
                'eth_price': float(ctx['eth_price']),
                'fear_greed_index': int(ctx['fear_greed_index']),
                'market_trend': ctx['market_trend']
            })

        return jsonify({
            'success': True,
            'period_hours': hours,
            'count': len(result),
            'data': result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# CHART ANALYSIS ENDPOINTS
# ============================================================================

@app.route('/api/v1/chart-analysis', methods=['GET'])
def get_chart_analysis():
    """Get latest chart analysis"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM chart_analyses
            ORDER BY timestamp DESC
            LIMIT 1
        ''')

        analysis = cursor.fetchone()

        if analysis:
            ai_analysis = json.loads(analysis['ai_analysis']) if analysis['ai_analysis'] else {}

            return jsonify({
                'success': True,
                'data': {
                    'timestamp': analysis['timestamp'],
                    'recommendation': analysis['recommendation'],
                    'confidence': analysis['confidence'],
                    'ai_analysis': ai_analysis,
                    'support_levels': json.loads(analysis['support_levels']) if analysis['support_levels'] else [],
                    'resistance_levels': json.loads(analysis['resistance_levels']) if analysis['resistance_levels'] else [],
                    'chart_path': analysis['chart_image_path']
                }
            })
        else:
            return jsonify({'success': False, 'error': 'No chart analysis available'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# BOT STATUS ENDPOINTS
# ============================================================================

@app.route('/api/v1/bot-status', methods=['GET'])
def get_bot_status():
    """Get current bot status"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM bot_status
            ORDER BY timestamp DESC
            LIMIT 1
        ''')

        status = cursor.fetchone()

        # Check PID files
        rl_bot_running = os.path.exists('logs/rl_bot.pid')
        chart_bot_running = os.path.exists('logs/chart_bot.pid')

        if status:
            return jsonify({
                'success': True,
                'data': {
                    'rl_bot_running': rl_bot_running,
                    'chart_bot_running': chart_bot_running,
                    'balance': float(status['balance']),
                    'total_pnl': float(status['total_pnl']),
                    'win_rate': float(status['win_rate']),
                    'total_trades': int(status['total_trades']),
                    'timestamp': status['timestamp']
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'rl_bot_running': rl_bot_running,
                    'chart_bot_running': chart_bot_running,
                    'balance': 0,
                    'total_pnl': 0,
                    'win_rate': 0,
                    'total_trades': 0,
                    'timestamp': None
                }
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.route('/api/v1/analytics/summary', methods=['GET'])
def get_analytics_summary():
    """Get comprehensive analytics summary"""
    try:
        hours = int(request.args.get('hours', 24))
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        conn = db.get_connection()
        cursor = conn.cursor()

        # Signal count
        cursor.execute('''
            SELECT COUNT(*) as count FROM signals
            WHERE timestamp >= ?
        ''', (start_time,))
        signal_count = cursor.fetchone()['count']

        # Trade count
        cursor.execute('''
            SELECT COUNT(*) as count FROM trades
            WHERE timestamp >= ?
        ''', (start_time,))
        trade_count = cursor.fetchone()['count']

        # PnL sum
        cursor.execute('''
            SELECT SUM(pnl) as total_pnl FROM trades
            WHERE timestamp >= ? AND pnl IS NOT NULL
        ''', (start_time,))
        total_pnl = cursor.fetchone()['total_pnl'] or 0

        # Win rate
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins
            FROM trades
            WHERE timestamp >= ? AND pnl IS NOT NULL
        ''', (start_time,))

        trade_stats = cursor.fetchone()
        win_rate = (trade_stats['wins'] / trade_stats['total'] * 100) if trade_stats['total'] > 0 else 0

        return jsonify({
            'success': True,
            'period_hours': hours,
            'signals_generated': signal_count,
            'trades_executed': trade_count,
            'total_pnl': round(total_pnl, 2),
            'win_rate': round(win_rate, 2)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM signals')
        signal_count = cursor.fetchone()[0]

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'total_signals': signal_count
        })

    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'disconnected',
            'error': str(e)
        }), 500


@app.route('/api/v1/info', methods=['GET'])
def get_server_info():
    """Get MCP server information"""
    return jsonify({
        'name': 'AI Crypto Trading Bot - MCP Server',
        'version': '1.0.0',
        'api_version': 'v1',
        'endpoints': {
            'signals': '/api/v1/signals',
            'signal_stats': '/api/v1/signals/stats',
            'trades': '/api/v1/trades',
            'trade_performance': '/api/v1/trades/performance',
            'market_context': '/api/v1/market-context',
            'market_history': '/api/v1/market-context/history',
            'chart_analysis': '/api/v1/chart-analysis',
            'bot_status': '/api/v1/bot-status',
            'analytics': '/api/v1/analytics/summary',
            'health': '/api/v1/health',
            'info': '/api/v1/info'
        },
        'documentation': 'https://github.com/yourusername/ai-crypto-trader/wiki/MCP-API'
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested API endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': str(error)
    }), 500


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the MCP server"""
    print("=" * 60)
    print("🌐 AI CRYPTO TRADING BOT - MCP SERVER")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 URL: http://{MCP_HOST}:{MCP_PORT}")
    print(f"📚 API Docs: http://{MCP_HOST}:{MCP_PORT}/api/v1/info")
    print("=" * 60)
    print()

    # Run Flask app
    app.run(
        host=MCP_HOST,
        port=MCP_PORT,
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )


if __name__ == '__main__':
    main()
