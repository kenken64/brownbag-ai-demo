"""
Database Module for AI Crypto Trading Bot
Handles all database operations including schema creation, data persistence, and queries
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
import json


class TradingDatabase:
    """Manages all database operations for the trading bot"""

    def __init__(self, db_path: str = "trading_bot.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_path = db_path
        self.conn = None
        self.initialize_database()

    def get_connection(self):
        """Get database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close_connection(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize_database(self):
        """Create all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Core tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                trading_pair TEXT NOT NULL,
                signal_type TEXT NOT NULL,  -- BUY, SELL, HOLD
                signal_strength INTEGER NOT NULL,
                price REAL NOT NULL,
                rsi REAL,
                macd REAL,
                macd_signal REAL,
                macd_histogram REAL,
                vwap REAL,
                ema9 REAL,
                ema21 REAL,
                sma50 REAL,
                bb_upper REAL,
                bb_middle REAL,
                bb_lower REAL,
                volume REAL,
                status TEXT DEFAULT 'pending'  -- pending, executed, skipped
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                trading_pair TEXT NOT NULL,
                side TEXT NOT NULL,  -- BUY, SELL
                entry_price REAL NOT NULL,
                exit_price REAL,
                quantity REAL NOT NULL,
                pnl REAL DEFAULT 0,
                status TEXT DEFAULT 'open',  -- open, closed
                signal_id INTEGER,
                leverage INTEGER,
                position_mode TEXT,  -- hedge, one-way
                stop_loss REAL,
                take_profit REAL,
                closed_at DATETIME,
                FOREIGN KEY (signal_id) REFERENCES signals(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                bot_name TEXT NOT NULL,
                status TEXT NOT NULL,  -- running, stopped, error
                pid INTEGER,
                balance REAL,
                open_positions INTEGER DEFAULT 0,
                total_trades INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0,
                total_pnl REAL DEFAULT 0.0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                model_path TEXT NOT NULL,
                version TEXT NOT NULL,
                episode INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0,
                avg_return REAL DEFAULT 0.0,
                total_states INTEGER DEFAULT 0,
                notes TEXT
            )
        ''')

        # Enhanced tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                btc_price REAL,
                btc_change_24h REAL,
                eth_price REAL,
                eth_change_24h REAL,
                btc_dominance REAL,
                fear_greed_index INTEGER,
                market_trend TEXT,  -- bullish, bearish, neutral
                btc_trend TEXT,  -- up_strong, down_strong, sideways
                market_regime TEXT,  -- risk_on, risk_off
                volatility_level TEXT  -- high, medium, low
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chart_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                trading_pair TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                recommendation TEXT,  -- BUY, SELL, HOLD
                confidence TEXT,  -- low, medium, high
                key_observations TEXT,
                risk_factors TEXT,
                ai_analysis TEXT,
                support_levels TEXT,
                resistance_levels TEXT,
                chart_image_path TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                period TEXT NOT NULL,  -- daily, weekly, monthly
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0,
                total_pnl REAL DEFAULT 0.0,
                avg_win REAL DEFAULT 0.0,
                avg_loss REAL DEFAULT 0.0,
                max_loss REAL DEFAULT 0.0,
                sharpe_ratio REAL,
                risk_reward_ratio REAL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS correlation_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                asset1 TEXT NOT NULL,
                asset2 TEXT NOT NULL,
                correlation_value REAL NOT NULL,
                period_days INTEGER DEFAULT 7,
                strength TEXT  -- strong, moderate, weak
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cost_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                api_name TEXT NOT NULL,  -- openai, binance, newsapi
                operation_type TEXT NOT NULL,
                api_calls INTEGER DEFAULT 0,
                estimated_cost REAL DEFAULT 0.0,
                cache_hits INTEGER DEFAULT 0,
                cache_misses INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                article_url TEXT UNIQUE NOT NULL,
                article_title TEXT,
                sentiment TEXT,  -- bullish, bearish, neutral
                confidence REAL,
                cache_expires_at DATETIME
            )
        ''')

        # CrewAI Multi-Agent tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spike_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                trading_pair TEXT NOT NULL,
                spike_type TEXT NOT NULL,  -- spot_price_spike, futures_spot_divergence, volume_explosion, etc.
                direction TEXT NOT NULL,  -- pump, dump
                magnitude_percent REAL NOT NULL,
                timeframe_minutes INTEGER NOT NULL,
                volume_multiplier REAL,
                price_from REAL NOT NULL,
                price_to REAL NOT NULL,
                confidence_score REAL,
                detection_latency_ms INTEGER,  -- Latency from price change to detection
                agent_detected_by TEXT,  -- Which agent detected it
                status TEXT DEFAULT 'detected',  -- detected, analyzed, traded, skipped
                skip_reason TEXT,
                context_analysis TEXT,  -- JSON with analysis details
                risk_assessment TEXT,  -- JSON with risk assessment
                trade_id INTEGER,  -- Link to trades table if executed
                outcome TEXT,  -- profitable, unprofitable, pending
                pnl REAL,
                FOREIGN KEY (trade_id) REFERENCES trades(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS circuit_breaker_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                triggered_at DATETIME NOT NULL,
                cleared_at DATETIME,
                trigger_reason TEXT NOT NULL,
                trigger_type TEXT NOT NULL,  -- btc_dump, eth_dump, market_wide, liquidations, systemic
                status TEXT NOT NULL,  -- triggered, recovering, cleared, false_trigger
                btc_price_at_trigger REAL,
                eth_price_at_trigger REAL,
                btc_drop_percent REAL,
                eth_drop_percent REAL,
                market_cap_drop_percent REAL,
                liquidations_1h REAL,
                fear_greed_index INTEGER,
                trigger_details TEXT,  -- JSON with detailed metrics
                market_snapshot TEXT,  -- JSON with full market snapshot
                downtime_seconds INTEGER,
                capital_saved REAL DEFAULT 0.0,
                orders_cancelled INTEGER DEFAULT 0,
                positions_affected INTEGER DEFAULT 0,
                recovery_time_seconds INTEGER,
                recovery_conditions_met TEXT,  -- JSON with recovery conditions
                user_notified BOOLEAN DEFAULT 0,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                agent_name TEXT NOT NULL,  -- market_guardian, market_scanner, context_analyzer, etc.
                agent_role TEXT NOT NULL,
                decision_type TEXT NOT NULL,  -- spike_detected, risk_assessed, trade_approved, circuit_breaker_triggered, etc.
                decision TEXT NOT NULL,  -- The actual decision (e.g., "APPROVE", "REJECT", "TRIGGER")
                confidence REAL,
                reasoning TEXT,  -- Agent's reasoning for the decision
                input_data TEXT,  -- JSON with input data to the agent
                output_data TEXT,  -- JSON with agent's output
                execution_time_ms INTEGER,  -- How long the agent took
                spike_event_id INTEGER,  -- Link to spike_events if applicable
                circuit_breaker_event_id INTEGER,  -- Link to circuit_breaker_events if applicable
                trade_id INTEGER,  -- Link to trades if applicable
                FOREIGN KEY (spike_event_id) REFERENCES spike_events(id),
                FOREIGN KEY (circuit_breaker_event_id) REFERENCES circuit_breaker_events(id),
                FOREIGN KEY (trade_id) REFERENCES trades(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                agent_name TEXT NOT NULL,
                period TEXT NOT NULL,  -- daily, weekly, monthly
                total_decisions INTEGER DEFAULT 0,
                correct_decisions INTEGER DEFAULT 0,
                incorrect_decisions INTEGER DEFAULT 0,
                accuracy_percent REAL DEFAULT 0.0,
                avg_confidence REAL DEFAULT 0.0,
                avg_execution_time_ms REAL DEFAULT 0.0,
                total_spikes_detected INTEGER DEFAULT 0,
                true_positives INTEGER DEFAULT 0,
                false_positives INTEGER DEFAULT 0,
                false_negatives INTEGER DEFAULT 0,
                circuit_breaker_triggers INTEGER DEFAULT 0,
                false_circuit_breaker_triggers INTEGER DEFAULT 0,
                notes TEXT
            )
        ''')

        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_context_timestamp ON market_context(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chart_analyses_timestamp ON chart_analyses(timestamp)')

        # Indexes for CrewAI Multi-Agent tables
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_spike_events_timestamp ON spike_events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_spike_events_status ON spike_events(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_spike_events_trading_pair ON spike_events(trading_pair)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_circuit_breaker_events_triggered_at ON circuit_breaker_events(triggered_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_circuit_breaker_events_status ON circuit_breaker_events(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_decisions_timestamp ON agent_decisions(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_decisions_agent_name ON agent_decisions(agent_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_performance_agent_name ON agent_performance(agent_name)')

        conn.commit()
        print("✅ Database initialized successfully with CrewAI Multi-Agent tables")

    def insert_signal(self, signal_data: Dict[str, Any]) -> int:
        """Insert a new trading signal"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO signals (
                trading_pair, signal_type, signal_strength, price,
                rsi, macd, macd_signal, macd_histogram, vwap,
                ema9, ema21, sma50, bb_upper, bb_middle, bb_lower, volume
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal_data.get('trading_pair'),
            signal_data.get('signal_type'),
            signal_data.get('signal_strength'),
            signal_data.get('price'),
            signal_data.get('rsi'),
            signal_data.get('macd'),
            signal_data.get('macd_signal'),
            signal_data.get('macd_histogram'),
            signal_data.get('vwap'),
            signal_data.get('ema9'),
            signal_data.get('ema21'),
            signal_data.get('sma50'),
            signal_data.get('bb_upper'),
            signal_data.get('bb_middle'),
            signal_data.get('bb_lower'),
            signal_data.get('volume')
        ))

        conn.commit()
        return cursor.lastrowid

    def insert_trade(self, trade_data: Dict[str, Any]) -> int:
        """Insert a new trade"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO trades (
                trading_pair, side, entry_price, quantity, signal_id,
                leverage, position_mode, stop_loss, take_profit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data.get('trading_pair'),
            trade_data.get('side'),
            trade_data.get('entry_price'),
            trade_data.get('quantity'),
            trade_data.get('signal_id'),
            trade_data.get('leverage'),
            trade_data.get('position_mode'),
            trade_data.get('stop_loss'),
            trade_data.get('take_profit')
        ))

        conn.commit()
        return cursor.lastrowid

    def update_trade(self, trade_id: int, updates: Dict[str, Any]):
        """Update an existing trade"""
        conn = self.get_connection()
        cursor = conn.cursor()

        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [trade_id]

        cursor.execute(f'UPDATE trades SET {set_clause} WHERE id = ?', values)
        conn.commit()

    def close_trade(self, trade_id: int, exit_price: float, pnl: float):
        """Close a trade"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE trades
            SET exit_price = ?, pnl = ?, status = 'closed', closed_at = ?
            WHERE id = ?
        ''', (exit_price, pnl, datetime.now(), trade_id))

        conn.commit()

    def get_open_trades(self, trading_pair: Optional[str] = None) -> List[Dict]:
        """Get all open trades"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if trading_pair:
            cursor.execute('SELECT * FROM trades WHERE status = "open" AND trading_pair = ?', (trading_pair,))
        else:
            cursor.execute('SELECT * FROM trades WHERE status = "open"')

        return [dict(row) for row in cursor.fetchall()]

    def get_recent_trades(self, limit: int = 50) -> List[Dict]:
        """Get recent trades"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?', (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Calculate performance statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(pnl) as total_pnl,
                AVG(CASE WHEN pnl > 0 THEN pnl END) as avg_win,
                AVG(CASE WHEN pnl < 0 THEN pnl END) as avg_loss,
                MIN(pnl) as max_loss
            FROM trades WHERE status = 'closed'
        ''')

        row = cursor.fetchone()
        total_trades = row['total_trades'] or 0
        winning_trades = row['winning_trades'] or 0

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': row['losing_trades'] or 0,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0.0,
            'total_pnl': row['total_pnl'] or 0.0,
            'avg_win': row['avg_win'] or 0.0,
            'avg_loss': row['avg_loss'] or 0.0,
            'max_loss': row['max_loss'] or 0.0
        }

    def update_bot_status(self, bot_name: str, status_data: Dict[str, Any]):
        """Update bot status"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO bot_status (
                bot_name, status, pid, balance, open_positions,
                total_trades, win_rate, total_pnl
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            bot_name,
            status_data.get('status'),
            status_data.get('pid'),
            status_data.get('balance'),
            status_data.get('open_positions'),
            status_data.get('total_trades'),
            status_data.get('win_rate'),
            status_data.get('total_pnl')
        ))

        conn.commit()

    def insert_market_context(self, context_data: Dict[str, Any]):
        """Insert market context data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO market_context (
                btc_price, btc_change_24h, eth_price, eth_change_24h,
                btc_dominance, fear_greed_index, market_trend,
                btc_trend, market_regime, volatility_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            context_data.get('btc_price'),
            context_data.get('btc_change_24h'),
            context_data.get('eth_price'),
            context_data.get('eth_change_24h'),
            context_data.get('btc_dominance'),
            context_data.get('fear_greed_index'),
            context_data.get('market_trend'),
            context_data.get('btc_trend'),
            context_data.get('market_regime'),
            context_data.get('volatility_level')
        ))

        conn.commit()

    def get_latest_market_context(self) -> Optional[Dict]:
        """Get the most recent market context"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM market_context ORDER BY timestamp DESC LIMIT 1')
        row = cursor.fetchone()

        return dict(row) if row else None

    def insert_chart_analysis(self, analysis_data: Dict[str, Any]):
        """Insert chart analysis"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO chart_analyses (
                trading_pair, timeframe, recommendation, confidence,
                key_observations, risk_factors, ai_analysis,
                support_levels, resistance_levels, chart_image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis_data.get('trading_pair'),
            analysis_data.get('timeframe'),
            analysis_data.get('recommendation'),
            analysis_data.get('confidence'),
            analysis_data.get('key_observations'),
            analysis_data.get('risk_factors'),
            analysis_data.get('ai_analysis'),
            analysis_data.get('support_levels'),
            analysis_data.get('resistance_levels'),
            analysis_data.get('chart_image_path')
        ))

        conn.commit()

    def get_recent_signals(self, limit: int = 50) -> List[Dict]:
        """Get recent signals"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM signals ORDER BY timestamp DESC LIMIT ?', (limit,))
        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    # Test database initialization
    db = TradingDatabase()
    print("Database module loaded successfully")