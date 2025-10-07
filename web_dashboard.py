"""
AI-Driven Cryptocurrency Trading Bot - Web Dashboard
Flask-based web interface for monitoring and controlling the trading bot
"""

import os
import json
import sqlite3
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import hashlib
import psutil
import logging

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web_dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BOT_CONTROL_PIN = os.getenv('BOT_CONTROL_PIN', '123456')
DATABASE_PATH = 'trading_bot.db'
SESSION_TIMEOUT = 1800  # 30 minutes in seconds

# In-memory storage for bot status (would be in database in production)
bot_status = {
    'running': True,
    'pid': os.getpid(),
    'last_update': datetime.now().isoformat(),
    'trade_execution': True,
    'trading_mode': 'auto',  # auto, manual, paper
    'paused': False
}

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))

        # Check session timeout
        last_activity = session.get('last_activity')
        if last_activity:
            last_activity_time = datetime.fromisoformat(last_activity)
            if (datetime.now() - last_activity_time).total_seconds() > SESSION_TIMEOUT:
                session.clear()
                return redirect(url_for('login'))

        session['last_activity'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function

def get_db_connection():
    """Create database connection"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pin = request.form.get('pin')

        if pin == BOT_CONTROL_PIN:
            session['authenticated'] = True
            session['last_activity'] = datetime.now().isoformat()
            session['login_time'] = datetime.now().isoformat()
            logger.info("User authenticated successfully")
            return redirect(url_for('dashboard'))
        else:
            logger.warning(f"Failed login attempt from {request.remote_addr}")
            return render_template('login.html', error='Invalid PIN')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/change-pin', methods=['GET', 'POST'])
@login_required
def change_pin():
    if request.method == 'POST':
        current_pin = request.form.get('current_pin')
        new_pin = request.form.get('new_pin')
        confirm_pin = request.form.get('confirm_pin')

        if current_pin != BOT_CONTROL_PIN:
            return render_template('change_pin.html', error='Invalid current PIN')

        if new_pin != confirm_pin:
            return render_template('change_pin.html', error='New PINs do not match')

        if len(new_pin) != 6 or not new_pin.isdigit():
            return render_template('change_pin.html', error='PIN must be exactly 6 digits')

        # In production, this should update the .env file
        global BOT_CONTROL_PIN
        BOT_CONTROL_PIN = new_pin
        logger.info("PIN changed successfully")

        return render_template('change_pin.html', success='PIN changed successfully')

    return render_template('change_pin.html')

# Main Dashboard Route
@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

# API Endpoints
@app.route('/api/bot-status')
@login_required
def api_bot_status():
    """Get current bot status"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        # Get latest signal
        signal = conn.execute('''
            SELECT * FROM signals
            ORDER BY timestamp DESC
            LIMIT 1
        ''').fetchone()

        # Get open positions count
        positions = conn.execute('''
            SELECT COUNT(*) as count FROM trades
            WHERE status = 'OPEN'
        ''').fetchone()

        conn.close()

        return jsonify({
            'status': 'RUNNING' if bot_status['running'] else 'STOPPED',
            'pid': bot_status['pid'],
            'last_update': bot_status['last_update'],
            'trade_execution': bot_status['trade_execution'],
            'trading_mode': bot_status['trading_mode'],
            'paused': bot_status['paused'],
            'total_signals': signal['id'] if signal else 0,
            'open_positions': positions['count'] if positions else 0
        })
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-data')
@login_required
def api_market_data():
    """Get current market data"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        # Get latest signal with indicators
        signal = conn.execute('''
            SELECT * FROM signals
            ORDER BY timestamp DESC
            LIMIT 1
        ''').fetchone()

        conn.close()

        if not signal:
            return jsonify({'error': 'No market data available'}), 404

        return jsonify({
            'price': signal['price'],
            'rsi': signal['rsi'],
            'vwap': signal['vwap'],
            'signal': signal['signal'],
            'signal_strength': signal['signal_strength'],
            'timestamp': signal['timestamp']
        })
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance-metrics')
@login_required
def api_performance_metrics():
    """Get performance metrics"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        # Get trade statistics
        stats = conn.execute('''
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(pnl) as total_pnl,
                AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
                AVG(CASE WHEN pnl <= 0 THEN pnl END) as avg_loss,
                MIN(pnl) as max_loss
            FROM trades
            WHERE status = 'CLOSED'
        ''').fetchone()

        conn.close()

        total_trades = stats['total_trades'] or 0
        winning_trades = stats['winning_trades'] or 0
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        return jsonify({
            'win_rate': round(win_rate, 2),
            'total_pnl': round(stats['total_pnl'] or 0, 2),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': stats['losing_trades'] or 0,
            'avg_win': round(stats['avg_win'] or 0, 2),
            'avg_loss': round(stats['avg_loss'] or 0, 2),
            'max_loss': round(stats['max_loss'] or 0, 2)
        })
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-trades')
@login_required
def api_recent_trades():
    """Get recent trades"""
    try:
        limit = request.args.get('limit', 20, type=int)

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        trades = conn.execute('''
            SELECT * FROM trades
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,)).fetchall()

        conn.close()

        return jsonify({
            'trades': [dict(trade) for trade in trades]
        })
    except Exception as e:
        logger.error(f"Error getting recent trades: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-signals')
@login_required
def api_recent_signals():
    """Get recent signals"""
    try:
        limit = request.args.get('limit', 20, type=int)

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        signals = conn.execute('''
            SELECT * FROM signals
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,)).fetchall()

        conn.close()

        return jsonify({
            'signals': [dict(signal) for signal in signals]
        })
    except Exception as e:
        logger.error(f"Error getting recent signals: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/open-positions')
@login_required
def api_open_positions():
    """Get open positions"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        positions = conn.execute('''
            SELECT * FROM trades
            WHERE status = 'OPEN'
            ORDER BY timestamp DESC
        ''').fetchall()

        conn.close()

        return jsonify({
            'positions': [dict(pos) for pos in positions]
        })
    except Exception as e:
        logger.error(f"Error getting open positions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-health')
@login_required
def api_system_health():
    """Get system health metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return jsonify({
            'cpu_usage': cpu_percent,
            'memory_usage': memory.percent,
            'memory_available': round(memory.available / (1024**3), 2),  # GB
            'memory_total': round(memory.total / (1024**3), 2),  # GB
            'disk_usage': disk.percent,
            'disk_available': round(disk.free / (1024**3), 2),  # GB
            'disk_total': round(disk.total / (1024**3), 2)  # GB
        })
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chart-analysis')
@login_required
def api_chart_analysis():
    """Get latest chart analysis from OpenAI"""
    try:
        # In production, this would read from the chart analysis bot's output
        # For now, return mock data structure
        return jsonify({
            'recommendation': 'HOLD',
            'confidence': 'Medium',
            'price': 0.0,
            'change_24h': 0.0,
            'key_observations': ['Sample observation'],
            'risk_factors': ['Sample risk factor'],
            'analysis': 'Chart analysis will be available when chart bot is running',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting chart analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-context')
@login_required
def api_market_context():
    """Get market context data (BTC, ETH, Fear & Greed)"""
    try:
        # In production, this would fetch from external APIs or database
        # For now, return structure that frontend expects
        return jsonify({
            'btc_price': 0.0,
            'btc_change': 0.0,
            'eth_price': 0.0,
            'eth_change': 0.0,
            'btc_dominance': 0.0,
            'fear_greed_index': 50,
            'market_trend': 'Neutral',
            'btc_trend': 'Sideways',
            'market_regime': 'Risk neutral'
        })
    except Exception as e:
        logger.error(f"Error getting market context: {e}")
        return jsonify({'error': str(e)}), 500

# Bot Control Endpoints
@app.route('/api/control/pause', methods=['POST'])
@login_required
def api_control_pause():
    """Pause/resume trading"""
    try:
        bot_status['paused'] = not bot_status['paused']
        bot_status['last_update'] = datetime.now().isoformat()

        logger.info(f"Trading {'paused' if bot_status['paused'] else 'resumed'}")

        return jsonify({
            'success': True,
            'paused': bot_status['paused']
        })
    except Exception as e:
        logger.error(f"Error toggling pause: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/control/emergency-close', methods=['POST'])
@login_required
def api_control_emergency_close():
    """Emergency close all positions"""
    try:
        # In production, this would trigger the bot to close all positions
        logger.warning("Emergency close triggered")

        return jsonify({
            'success': True,
            'message': 'Emergency close initiated'
        })
    except Exception as e:
        logger.error(f"Error in emergency close: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/control/trading-mode', methods=['POST'])
@login_required
def api_control_trading_mode():
    """Change trading mode (auto/manual/paper)"""
    try:
        mode = request.json.get('mode')

        if mode not in ['auto', 'manual', 'paper']:
            return jsonify({'error': 'Invalid trading mode'}), 400

        bot_status['trading_mode'] = mode
        bot_status['last_update'] = datetime.now().isoformat()

        logger.info(f"Trading mode changed to: {mode}")

        return jsonify({
            'success': True,
            'mode': mode
        })
    except Exception as e:
        logger.error(f"Error changing trading mode: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
@login_required
def api_logs():
    """Get recent log entries"""
    try:
        log_type = request.args.get('type', 'main')
        lines = request.args.get('lines', 100, type=int)

        log_files = {
            'main': 'trading_bot.log',
            'chart': 'chart_analysis_bot.log',
            'web': 'web_dashboard.log',
            'rl': 'logs/rl_bot_main.log'
        }

        log_file = log_files.get(log_type, 'trading_bot.log')

        if not os.path.exists(log_file):
            return jsonify({'logs': []})

        with open(log_file, 'r') as f:
            logs = f.readlines()[-lines:]

        return jsonify({
            'logs': [log.strip() for log in logs]
        })
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create templates and static directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)

    logger.info("Starting Web Dashboard...")
    logger.info(f"Dashboard will be available at http://localhost:5000")

    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
