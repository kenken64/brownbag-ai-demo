"""
Database Manager for AI Crypto Trading Bot
Handles database connections, connection pooling, and transaction management
Version: 1.0
"""

import sqlite3
import threading
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import json
import os

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Thread-safe SQLite database manager with connection pooling"""

    def __init__(self, db_path: str = "trading_bot.db", pool_size: int = 10):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file
            pool_size: Maximum number of connections in pool
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self._local = threading.local()
        self._lock = threading.Lock()
        self._initialize_database()

    def _initialize_database(self):
        """Ensure database file exists and has proper permissions"""
        if not os.path.exists(self.db_path):
            logger.warning(f"Database file {self.db_path} not found, creating new database")
            # Database will be created on first connection

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0,
                isolation_level=None  # Autocommit mode
            )
            # Enable row factory for dict-like access
            self._local.connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode = WAL")

        return self._local.connection

    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor with automatic cleanup"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    @contextmanager
    def transaction(self):
        """Context manager for database transactions with automatic rollback"""
        conn = self._get_connection()
        conn.isolation_level = 'DEFERRED'

        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
        finally:
            conn.isolation_level = None

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dictionaries

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of result rows as dictionaries
        """
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def execute_insert(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Execute an INSERT query and return last row ID

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            ID of inserted row
        """
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            return cursor.lastrowid

    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        Execute an UPDATE or DELETE query and return affected rows

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows
        """
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            return cursor.rowcount

    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        Execute a query with multiple parameter sets

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Number of affected rows
        """
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount

    def close_all_connections(self):
        """Close all database connections"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')

    # Convenience methods for common operations

    def get_latest_signal(self, trading_pair: str = None) -> Optional[Dict[str, Any]]:
        """Get the latest signal, optionally filtered by trading pair"""
        query = """
            SELECT * FROM signals
            WHERE 1=1
        """
        params = []

        if trading_pair:
            query += " AND trading_pair = ?"
            params.append(trading_pair)

        query += " ORDER BY timestamp DESC LIMIT 1"

        results = self.execute_query(query, tuple(params) if params else None)
        return results[0] if results else None

    def get_recent_signals(self, limit: int = 10, trading_pair: str = None) -> List[Dict[str, Any]]:
        """Get recent signals"""
        query = """
            SELECT * FROM signals
            WHERE 1=1
        """
        params = []

        if trading_pair:
            query += " AND trading_pair = ?"
            params.append(trading_pair)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        return self.execute_query(query, tuple(params))

    def get_open_trades(self, trading_pair: str = None) -> List[Dict[str, Any]]:
        """Get all open trades"""
        query = """
            SELECT * FROM trades
            WHERE status = 'open'
        """
        params = []

        if trading_pair:
            query += " AND trading_pair = ?"
            params.append(trading_pair)

        query += " ORDER BY timestamp DESC"

        return self.execute_query(query, tuple(params) if params else None)

    def get_recent_trades(self, limit: int = 20, trading_pair: str = None) -> List[Dict[str, Any]]:
        """Get recent trades"""
        query = """
            SELECT * FROM trades
            WHERE 1=1
        """
        params = []

        if trading_pair:
            query += " AND trading_pair = ?"
            params.append(trading_pair)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        return self.execute_query(query, tuple(params))

    def get_performance_metrics(self, period: str = None) -> Dict[str, Any]:
        """Calculate performance metrics from trades"""
        query = """
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(pnl) as total_pnl,
                AVG(CASE WHEN pnl > 0 THEN pnl ELSE NULL END) as avg_win,
                AVG(CASE WHEN pnl <= 0 THEN pnl ELSE NULL END) as avg_loss,
                MIN(pnl) as max_loss,
                MAX(pnl) as max_win
            FROM trades
            WHERE status = 'closed'
        """

        results = self.execute_query(query)
        if not results:
            return {}

        metrics = results[0]

        # Calculate win rate
        total = metrics.get('total_trades', 0)
        wins = metrics.get('winning_trades', 0)
        metrics['win_rate'] = (wins / total * 100) if total > 0 else 0.0

        # Calculate risk-reward ratio
        avg_win = metrics.get('avg_win', 0) or 0
        avg_loss = abs(metrics.get('avg_loss', 0) or 0)
        metrics['risk_reward_ratio'] = (avg_win / avg_loss) if avg_loss > 0 else 0.0

        return metrics

    def get_latest_market_context(self) -> Optional[Dict[str, Any]]:
        """Get latest market context data"""
        query = """
            SELECT * FROM market_context
            ORDER BY timestamp DESC LIMIT 1
        """
        results = self.execute_query(query)
        return results[0] if results else None

    def get_latest_chart_analysis(self, trading_pair: str = None) -> Optional[Dict[str, Any]]:
        """Get latest chart analysis"""
        query = """
            SELECT * FROM chart_analyses
            WHERE 1=1
        """
        params = []

        if trading_pair:
            query += " AND trading_pair = ?"
            params.append(trading_pair)

        query += " ORDER BY timestamp DESC LIMIT 1"

        results = self.execute_query(query, tuple(params) if params else None)
        return results[0] if results else None

    def get_bot_status(self, bot_name: str = None) -> Optional[Dict[str, Any]]:
        """Get latest bot status"""
        query = """
            SELECT * FROM bot_status
            WHERE 1=1
        """
        params = []

        if bot_name:
            query += " AND bot_name = ?"
            params.append(bot_name)

        query += " ORDER BY timestamp DESC LIMIT 1"

        results = self.execute_query(query, tuple(params) if params else None)
        return results[0] if results else None

    def insert_signal(self, signal_data: Dict[str, Any]) -> int:
        """Insert a new signal"""
        query = """
            INSERT INTO signals (
                trading_pair, signal_type, signal_strength, price,
                rsi, macd, macd_signal, macd_histogram, vwap,
                ema9, ema21, sma50, bb_upper, bb_middle, bb_lower,
                volume, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
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
            signal_data.get('volume'),
            signal_data.get('status', 'pending')
        )

        return self.execute_insert(query, params)

    def insert_trade(self, trade_data: Dict[str, Any]) -> int:
        """Insert a new trade"""
        query = """
            INSERT INTO trades (
                trading_pair, side, entry_price, quantity,
                leverage, position_mode, signal_id, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            trade_data.get('trading_pair'),
            trade_data.get('side'),
            trade_data.get('entry_price'),
            trade_data.get('quantity'),
            trade_data.get('leverage'),
            trade_data.get('position_mode'),
            trade_data.get('signal_id'),
            trade_data.get('status', 'open')
        )

        return self.execute_insert(query, params)

    def update_bot_status(self, status_data: Dict[str, Any]) -> int:
        """Update bot status"""
        query = """
            INSERT INTO bot_status (
                bot_name, status, pid, balance, open_positions,
                total_trades, win_rate, total_pnl
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            status_data.get('bot_name'),
            status_data.get('status'),
            status_data.get('pid'),
            status_data.get('balance'),
            status_data.get('open_positions'),
            status_data.get('total_trades'),
            status_data.get('win_rate'),
            status_data.get('total_pnl')
        )

        return self.execute_insert(query, params)


# Global database manager instance
db_manager = DatabaseManager()
