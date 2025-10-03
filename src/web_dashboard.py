#!/usr/bin/env python3
"""
Web Dashboard for AI Crypto Trading Bot
Flask-based real-time monitoring interface
Port: 5000 (default)
"""

import os
import sys
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import TradingDatabase

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize Flask app
app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database
db = TradingDatabase()

# Configuration
DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', 5000))
DASHBOARD_HOST = os.getenv('DASHBOARD_HOST', '0.0.0.0')
DASHBOARD_PIN = os.getenv('BOT_CONTROL_PIN', '123456')


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/bot-status')
def get_bot_status():
    """Get current bot status"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get latest bot status
        cursor.execute('''
            SELECT * FROM bot_status
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        status = cursor.fetchone()

        # Get PID file status
        rl_bot_running = os.path.exists('logs/rl_bot.pid')
        chart_bot_running = os.path.exists('logs/chart_bot.pid')

        if status:
            return jsonify({
                'success': True,
                'rl_bot_running': rl_bot_running,
                'chart_bot_running': chart_bot_running,
                'balance': float(status['balance']),
                'total_pnl': float(status['total_pnl']),
                'win_rate': float(status['win_rate']),
                'total_trades': int(status['total_trades']),
                'last_update': status['timestamp']
            })
        else:
            return jsonify({
                'success': True,
                'rl_bot_running': rl_bot_running,
                'chart_bot_running': chart_bot_running,
                'balance': 0,
                'total_pnl': 0,
                'win_rate': 0,
                'total_trades': 0,
                'last_update': None
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/market-data')
def get_market_data():
    """Get current market data"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get latest signal
        cursor.execute('''
            SELECT * FROM signals
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        signal = cursor.fetchone()

        # Get latest market context
        cursor.execute('''
            SELECT * FROM market_context
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        context = cursor.fetchone()

        if signal:
            data = {
                'success': True,
                'price': float(signal['price']),
                'rsi': float(signal['rsi']) if signal['rsi'] else None,
                'macd': float(signal['macd']) if signal['macd'] else None,
                'vwap': float(signal['vwap']) if signal['vwap'] else None,
                'signal_type': signal['signal_type'],
                'signal_strength': int(signal['signal_strength']),
                'timestamp': signal['timestamp']
            }

            if context:
                data['btc_price'] = float(context['btc_price'])
                data['eth_price'] = float(context['eth_price'])
                data['fear_greed_index'] = int(context['fear_greed_index'])
                data['market_trend'] = context['market_trend']
                data['btc_dominance'] = float(context['btc_dominance']) if context['btc_dominance'] else None

            return jsonify(data)
        else:
            return jsonify({'success': False, 'error': 'No market data available'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/chart-analysis')
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
            # Parse JSON fields
            ai_analysis = json.loads(analysis['ai_analysis']) if analysis['ai_analysis'] else {}

            return jsonify({
                'success': True,
                'recommendation': analysis['recommendation'],
                'confidence': analysis['confidence'],
                'trend': ai_analysis.get('trend', 'N/A'),
                'trend_strength': ai_analysis.get('trend_strength', 'N/A'),
                'overall_score': ai_analysis.get('overall_score', 0),
                'key_observations': ai_analysis.get('key_observations', []),
                'risk_factors': ai_analysis.get('risk_factors', []),
                'support_levels': json.loads(analysis['support_levels']) if analysis['support_levels'] else [],
                'resistance_levels': json.loads(analysis['resistance_levels']) if analysis['resistance_levels'] else [],
                'timestamp': analysis['timestamp'],
                'chart_path': analysis['chart_image_path']
            })
        else:
            return jsonify({'success': False, 'error': 'No chart analysis available'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/trades')
def get_trades():
    """Get recent trades"""
    try:
        limit = request.args.get('limit', 20, type=int)

        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT * FROM trades
            ORDER BY timestamp DESC
            LIMIT {limit}
        ''')
        trades = cursor.fetchall()

        trades_list = []
        for trade in trades:
            trades_list.append({
                'id': trade['id'],
                'timestamp': trade['timestamp'],
                'side': trade['side'],
                'entry_price': float(trade['entry_price']),
                'exit_price': float(trade['exit_price']) if trade['exit_price'] else None,
                'quantity': float(trade['quantity']),
                'pnl': float(trade['pnl']) if trade['pnl'] else None,
                'pnl_percentage': float(trade['pnl_percentage']) if trade['pnl_percentage'] else None,
                'exit_reason': trade['exit_reason']
            })

        return jsonify({'success': True, 'trades': trades_list})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/performance')
def get_performance():
    """Get performance metrics"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        # Get all trades
        cursor.execute('SELECT * FROM trades WHERE pnl IS NOT NULL')
        trades = cursor.fetchall()

        if not trades:
            return jsonify({
                'success': True,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'max_win': 0,
                'max_loss': 0,
                'profit_factor': 0
            })

        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] < 0]

        total_wins = sum(t['pnl'] for t in winning_trades)
        total_losses = abs(sum(t['pnl'] for t in losing_trades))

        return jsonify({
            'success': True,
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round((len(winning_trades) / len(trades)) * 100, 2) if trades else 0,
            'total_pnl': round(sum(t['pnl'] for t in trades), 2),
            'avg_win': round(total_wins / len(winning_trades), 2) if winning_trades else 0,
            'avg_loss': round(total_losses / len(losing_trades), 2) if losing_trades else 0,
            'max_win': round(max((t['pnl'] for t in winning_trades), default=0), 2),
            'max_loss': round(abs(min((t['pnl'] for t in losing_trades), default=0)), 2),
            'profit_factor': round(total_wins / total_losses, 2) if total_losses > 0 else 0
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/positions')
def get_positions():
    """Get open positions"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM trades
            WHERE exit_price IS NULL
            ORDER BY timestamp DESC
        ''')
        positions = cursor.fetchall()

        positions_list = []
        for pos in positions:
            positions_list.append({
                'id': pos['id'],
                'timestamp': pos['timestamp'],
                'side': pos['side'],
                'entry_price': float(pos['entry_price']),
                'quantity': float(pos['quantity']),
                'leverage': int(pos['leverage']) if pos['leverage'] else 1
            })

        return jsonify({'success': True, 'positions': positions_list})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/signals')
def get_signals():
    """Get recent signals"""
    try:
        limit = request.args.get('limit', 10, type=int)

        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute(f'''
            SELECT * FROM signals
            ORDER BY timestamp DESC
            LIMIT {limit}
        ''')
        signals = cursor.fetchall()

        signals_list = []
        for signal in signals:
            signals_list.append({
                'timestamp': signal['timestamp'],
                'price': float(signal['price']),
                'signal_type': signal['signal_type'],
                'signal_strength': int(signal['signal_strength']),
                'rsi': float(signal['rsi']) if signal['rsi'] else None,
                'macd': float(signal['macd']) if signal['macd'] else None
            })

        return jsonify({'success': True, 'signals': signals_list})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/news')
def get_news():
    """Get recent news sentiment"""
    try:
        # This would integrate with news_fetcher and news_sentiment
        # For now, return placeholder
        return jsonify({
            'success': True,
            'overall_sentiment': 'neutral',
            'bullish_count': 0,
            'bearish_count': 0,
            'neutral_count': 0,
            'articles': []
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if db else 'disconnected'
    })


def main():
    """Run the dashboard"""
    print("=" * 60)
    print("🌐 AI CRYPTO TRADING BOT - WEB DASHBOARD")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 URL: http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    print(f"🔐 PIN: {DASHBOARD_PIN}")
    print("=" * 60)
    print()

    # Run Flask app
    app.run(
        host=DASHBOARD_HOST,
        port=DASHBOARD_PORT,
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )


if __name__ == '__main__':
    main()
