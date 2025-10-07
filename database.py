"""
Database Management Module
Handles SQLite database initialization and operations for the trading bot
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import json


class TradingDatabase:
    """Manages all database operations for the trading bot"""

    def __init__(self, db_path: str = "trading_bot.db"):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def initialize_tables(self):
        """Create all required database tables"""

        # Core signals table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                signal TEXT NOT NULL,
                strength INTEGER NOT NULL,
                rsi REAL,
                macd REAL,
                macd_signal REAL,
                macd_histogram REAL,
                vwap REAL,
                ema_9 REAL,
                ema_21 REAL,
                sma_50 REAL,
                bb_upper REAL,
                bb_middle REAL,
                bb_lower REAL,
                volume REAL,
                btc_price REAL,
                btc_correlation REAL,
                fear_greed_index INTEGER,
                market_regime TEXT,
                indicators_json TEXT
            )
        """)

        # Trades table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                quantity REAL NOT NULL,
                pnl REAL,
                pnl_percentage REAL,
                status TEXT DEFAULT 'OPEN',
                signal_id INTEGER,
                rl_action TEXT,
                reasoning TEXT,
                closed_at DATETIME,
                FOREIGN KEY (signal_id) REFERENCES signals(id)
            )
        """)

        # Bot status table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                balance REAL,
                total_pnl REAL,
                win_rate REAL,
                total_trades INTEGER,
                open_positions INTEGER,
                message TEXT
            )
        """)

        # Model checkpoints table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                model_version TEXT NOT NULL,
                file_path TEXT NOT NULL,
                episodes_trained INTEGER,
                avg_reward REAL,
                win_rate REAL,
                notes TEXT
            )
        """)

        # Market context table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                btc_price REAL,
                btc_change_24h REAL,
                eth_price REAL,
                eth_change_24h REAL,
                btc_dominance REAL,
                fear_greed_index INTEGER,
                fear_greed_label TEXT,
                market_trend TEXT,
                btc_trend_strength TEXT,
                market_regime TEXT,
                volatility_level TEXT
            )
        """)

        # Chart analyses table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS chart_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                ai_recommendation TEXT,
                confidence REAL,
                key_observations TEXT,
                risk_factors TEXT,
                analysis_text TEXT,
                support_level REAL,
                resistance_level REAL,
                chart_image_path TEXT
            )
        """)

        # Performance metrics table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                period TEXT NOT NULL,
                total_pnl REAL,
                win_rate REAL,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                avg_win REAL,
                avg_loss REAL,
                max_drawdown REAL,
                sharpe_ratio REAL,
                risk_reward_ratio REAL
            )
        """)

        # Correlation data table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS correlation_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                asset1 TEXT NOT NULL,
                asset2 TEXT NOT NULL,
                correlation_coefficient REAL,
                period_days INTEGER,
                significance REAL
            )
        """)

        # Cost analytics table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cost_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                api_name TEXT NOT NULL,
                operation TEXT,
                cost REAL,
                cached BOOLEAN DEFAULT 0,
                tokens_used INTEGER,
                model_used TEXT
            )
        """)

        # News cache table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                article_url TEXT UNIQUE NOT NULL,
                title TEXT,
                description TEXT,
                source TEXT,
                published_at DATETIME,
                sentiment TEXT,
                sentiment_score REAL,
                confidence REAL,
                analysis_mode TEXT,
                cache_expires_at DATETIME
            )
        """)

        self.conn.commit()
        print("✅ Database tables initialized successfully")

    def insert_signal(self, signal_data: Dict[str, Any]) -> int:
        """Insert a new signal into the database"""
        query = """
            INSERT INTO signals (
                symbol, price, signal, strength, rsi, macd, macd_signal, macd_histogram,
                vwap, ema_9, ema_21, sma_50, bb_upper, bb_middle, bb_lower, volume,
                btc_price, btc_correlation, fear_greed_index, market_regime, indicators_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.cursor.execute(query, (
            signal_data.get('symbol'),
            signal_data.get('price'),
            signal_data.get('signal'),
            signal_data.get('strength'),
            signal_data.get('rsi'),
            signal_data.get('macd'),
            signal_data.get('macd_signal'),
            signal_data.get('macd_histogram'),
            signal_data.get('vwap'),
            signal_data.get('ema_9'),
            signal_data.get('ema_21'),
            signal_data.get('sma_50'),
            signal_data.get('bb_upper'),
            signal_data.get('bb_middle'),
            signal_data.get('bb_lower'),
            signal_data.get('volume'),
            signal_data.get('btc_price'),
            signal_data.get('btc_correlation'),
            signal_data.get('fear_greed_index'),
            signal_data.get('market_regime'),
            json.dumps(signal_data.get('indicators', {}))
        ))

        self.conn.commit()
        return self.cursor.lastrowid

    def insert_trade(self, trade_data: Dict[str, Any]) -> int:
        """Insert a new trade into the database"""
        query = """
            INSERT INTO trades (
                symbol, side, entry_price, quantity, signal_id, rl_action, reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        self.cursor.execute(query, (
            trade_data.get('symbol'),
            trade_data.get('side'),
            trade_data.get('entry_price'),
            trade_data.get('quantity'),
            trade_data.get('signal_id'),
            trade_data.get('rl_action'),
            trade_data.get('reasoning')
        ))

        self.conn.commit()
        return self.cursor.lastrowid

    def update_trade_close(self, trade_id: int, exit_price: float, pnl: float, pnl_percentage: float):
        """Update trade with closing information"""
        query = """
            UPDATE trades
            SET exit_price = ?, pnl = ?, pnl_percentage = ?, status = 'CLOSED', closed_at = ?
            WHERE id = ?
        """

        self.cursor.execute(query, (exit_price, pnl, pnl_percentage, datetime.now(), trade_id))
        self.conn.commit()

    def get_recent_signals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent signals"""
        query = """
            SELECT * FROM signals
            ORDER BY timestamp DESC
            LIMIT ?
        """

        self.cursor.execute(query, (limit,))
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_recent_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent trades"""
        query = """
            SELECT * FROM trades
            ORDER BY timestamp DESC
            LIMIT ?
        """

        self.cursor.execute(query, (limit,))
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Calculate performance statistics"""
        # Get total trades
        self.cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED'")
        total_trades = self.cursor.fetchone()[0]

        # Get winning trades
        self.cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED' AND pnl > 0")
        winning_trades = self.cursor.fetchone()[0]

        # Get losing trades
        self.cursor.execute("SELECT COUNT(*) FROM trades WHERE status = 'CLOSED' AND pnl < 0")
        losing_trades = self.cursor.fetchone()[0]

        # Get total PnL
        self.cursor.execute("SELECT SUM(pnl) FROM trades WHERE status = 'CLOSED'")
        total_pnl = self.cursor.fetchone()[0] or 0

        # Get average win
        self.cursor.execute("SELECT AVG(pnl) FROM trades WHERE status = 'CLOSED' AND pnl > 0")
        avg_win = self.cursor.fetchone()[0] or 0

        # Get average loss
        self.cursor.execute("SELECT AVG(pnl) FROM trades WHERE status = 'CLOSED' AND pnl < 0")
        avg_loss = self.cursor.fetchone()[0] or 0

        # Get max loss
        self.cursor.execute("SELECT MIN(pnl) FROM trades WHERE status = 'CLOSED'")
        max_loss = self.cursor.fetchone()[0] or 0

        # Calculate win rate
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Calculate risk-reward ratio
        risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_loss': max_loss,
            'risk_reward_ratio': risk_reward
        }

    def insert_chart_analysis(self, analysis_data: Dict[str, Any]) -> int:
        """Insert chart analysis result"""
        query = """
            INSERT INTO chart_analyses (
                symbol, timeframe, ai_recommendation, confidence,
                key_observations, risk_factors, analysis_text,
                support_level, resistance_level, chart_image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.cursor.execute(query, (
            analysis_data.get('symbol'),
            analysis_data.get('timeframe'),
            analysis_data.get('ai_recommendation'),
            analysis_data.get('confidence'),
            analysis_data.get('key_observations'),
            analysis_data.get('risk_factors'),
            analysis_data.get('analysis_text'),
            analysis_data.get('support_level'),
            analysis_data.get('resistance_level'),
            analysis_data.get('chart_image_path')
        ))

        self.conn.commit()
        return self.cursor.lastrowid

    def insert_market_context(self, context_data: Dict[str, Any]) -> int:
        """Insert market context data"""
        query = """
            INSERT INTO market_context (
                btc_price, btc_change_24h, eth_price, eth_change_24h,
                btc_dominance, fear_greed_index, fear_greed_label,
                market_trend, btc_trend_strength, market_regime, volatility_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.cursor.execute(query, (
            context_data.get('btc_price'),
            context_data.get('btc_change_24h'),
            context_data.get('eth_price'),
            context_data.get('eth_change_24h'),
            context_data.get('btc_dominance'),
            context_data.get('fear_greed_index'),
            context_data.get('fear_greed_label'),
            context_data.get('market_trend'),
            context_data.get('btc_trend_strength'),
            context_data.get('market_regime'),
            context_data.get('volatility_level')
        ))

        self.conn.commit()
        return self.cursor.lastrowid


def init_database(db_path: str = "trading_bot.db"):
    """Initialize the trading bot database"""
    print(f"🚀 Initializing database at {db_path}...")

    db = TradingDatabase(db_path)
    db.connect()
    db.initialize_tables()
    db.close()

    print(f"✅ Database initialized successfully at {db_path}")
    return db_path


if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
