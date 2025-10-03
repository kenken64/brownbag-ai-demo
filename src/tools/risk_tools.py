#!/usr/bin/env python3
"""
Risk Assessment Tools for CrewAI Agents
Provides portfolio and risk management capabilities
"""

import os
import sys
import json
from typing import Dict, Optional
from datetime import datetime
from crewai_tools import tool

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import TradingDatabase
from circuit_breaker_state import get_circuit_breaker_state


# Initialize components
db = TradingDatabase()
cb_state = get_circuit_breaker_state()


@tool("Get Portfolio Status")
def get_portfolio_status() -> str:
    """
    Get current portfolio status including balance, positions, and PnL.

    Returns:
        JSON string with portfolio information
    """
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

        # Get open positions
        cursor.execute('''
            SELECT COUNT(*) as count FROM trades
            WHERE exit_price IS NULL
        ''')
        open_positions = cursor.fetchone()['count']

        # Get recent performance
        cursor.execute('''
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                SUM(pnl) as total_pnl
            FROM trades
            WHERE pnl IS NOT NULL
        ''')
        perf = cursor.fetchone()

        win_rate = (perf['wins'] / perf['total_trades'] * 100) if perf['total_trades'] > 0 else 0

        result = {
            "success": True,
            "balance": float(status['balance']) if status else 0,
            "total_pnl": float(status['total_pnl']) if status else 0,
            "win_rate": round(win_rate, 2),
            "open_positions": open_positions,
            "total_trades": perf['total_trades'] or 0,
            "timestamp": datetime.now().isoformat()
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool("Calculate Position Size")
def calculate_position_size(
    entry_price: float,
    stop_loss_price: float,
    risk_percent: float = 2.0
) -> str:
    """
    Calculate optimal position size based on risk management rules.

    Args:
        entry_price: Planned entry price
        stop_loss_price: Stop loss price
        risk_percent: Percentage of balance to risk (default: 2%)

    Returns:
        JSON string with position sizing recommendation
    """
    try:
        # Get current balance
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT balance FROM bot_status
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        result = cursor.fetchone()
        balance = float(result['balance']) if result else 1000.0

        # Calculate risk amount
        risk_amount = balance * (risk_percent / 100)

        # Calculate price risk per unit
        price_risk = abs(entry_price - stop_loss_price)
        price_risk_pct = (price_risk / entry_price) * 100

        # Calculate position size
        position_size = risk_amount / price_risk if price_risk > 0 else 0

        # Calculate notional value
        notional_value = position_size * entry_price

        # Check if position size is reasonable
        max_position_value = balance * 0.5  # Max 50% of balance
        is_reasonable = notional_value <= max_position_value

        return json.dumps({
            "success": True,
            "balance": balance,
            "risk_amount": round(risk_amount, 2),
            "risk_percent": risk_percent,
            "entry_price": entry_price,
            "stop_loss_price": stop_loss_price,
            "price_risk_percent": round(price_risk_pct, 2),
            "recommended_position_size": round(position_size, 6),
            "notional_value": round(notional_value, 2),
            "is_reasonable": is_reasonable,
            "max_position_value": round(max_position_value, 2),
            "warning": None if is_reasonable else "Position size exceeds 50% of balance",
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool("Check Daily Loss Limit")
def check_daily_loss_limit(max_daily_loss_percent: float = 5.0) -> str:
    """
    Check if daily loss limit has been exceeded.

    Args:
        max_daily_loss_percent: Maximum allowed daily loss percentage (default: 5%)

    Returns:
        JSON string with daily loss status
    """
    try:
        from datetime import datetime, timedelta

        conn = db.get_connection()
        cursor = conn.cursor()

        # Get today's date
        today = datetime.now().date().isoformat()

        # Get starting balance (first trade of the day or last bot_status)
        cursor.execute('''
            SELECT balance FROM bot_status
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        result = cursor.fetchone()
        current_balance = float(result['balance']) if result else 1000.0

        # Get today's PnL
        cursor.execute('''
            SELECT SUM(pnl) as daily_pnl FROM trades
            WHERE DATE(timestamp) = ? AND pnl IS NOT NULL
        ''', (today,))
        result = cursor.fetchone()
        daily_pnl = float(result['daily_pnl']) if result and result['daily_pnl'] else 0

        # Calculate starting balance
        starting_balance = current_balance - daily_pnl

        # Calculate daily loss percentage
        daily_loss_pct = (daily_pnl / starting_balance * 100) if starting_balance > 0 else 0

        # Check if limit exceeded
        limit_exceeded = daily_loss_pct <= -max_daily_loss_percent

        return json.dumps({
            "success": True,
            "starting_balance": round(starting_balance, 2),
            "current_balance": round(current_balance, 2),
            "daily_pnl": round(daily_pnl, 2),
            "daily_loss_percent": round(daily_loss_pct, 2),
            "max_daily_loss_percent": max_daily_loss_percent,
            "limit_exceeded": limit_exceeded,
            "can_trade": not limit_exceeded,
            "warning": "Daily loss limit exceeded! Trading should be halted." if limit_exceeded else None,
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool("Calculate Stop Loss and Take Profit")
def calculate_stop_loss_take_profit(
    entry_price: float,
    side: str = "LONG",
    stop_loss_percent: float = 2.0,
    take_profit_percent: float = 5.0
) -> str:
    """
    Calculate stop loss and take profit levels.

    Args:
        entry_price: Entry price
        side: Position side ("LONG" or "SHORT")
        stop_loss_percent: Stop loss percentage (default: 2%)
        take_profit_percent: Take profit percentage (default: 5%)

    Returns:
        JSON string with SL/TP levels
    """
    try:
        side = side.upper()

        if side == "LONG":
            stop_loss = entry_price * (1 - stop_loss_percent / 100)
            take_profit = entry_price * (1 + take_profit_percent / 100)
        elif side == "SHORT":
            stop_loss = entry_price * (1 + stop_loss_percent / 100)
            take_profit = entry_price * (1 - take_profit_percent / 100)
        else:
            return json.dumps({
                "success": False,
                "error": "Invalid side. Must be 'LONG' or 'SHORT'"
            }, indent=2)

        # Calculate risk/reward ratio
        risk_reward_ratio = take_profit_percent / stop_loss_percent

        return json.dumps({
            "success": True,
            "side": side,
            "entry_price": entry_price,
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "stop_loss_percent": stop_loss_percent,
            "take_profit_percent": take_profit_percent,
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool("Check Market Stability")
def check_market_stability() -> str:
    """
    Check if market conditions are stable (circuit breaker status).

    Returns:
        JSON string with market stability status
    """
    try:
        # Get circuit breaker state
        status = cb_state.get_status()
        is_safe = cb_state.is_safe()
        full_state = cb_state.get_full_state()

        return json.dumps({
            "success": True,
            "is_stable": is_safe,
            "can_trade": is_safe,
            "circuit_breaker_status": status.value,
            "warning": full_state.get('trigger_reason') if not is_safe else None,
            "trigger_details": full_state.get('trigger_details') if not is_safe else None,
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool("Calculate Risk Metrics")
def calculate_risk_metrics(
    entry_price: float,
    position_size: float,
    leverage: int = 1
) -> str:
    """
    Calculate comprehensive risk metrics for a potential trade.

    Args:
        entry_price: Entry price
        position_size: Position size (in base currency)
        leverage: Leverage multiplier (default: 1x)

    Returns:
        JSON string with risk metrics
    """
    try:
        # Get current balance
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT balance FROM bot_status
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        result = cursor.fetchone()
        balance = float(result['balance']) if result else 1000.0

        # Calculate notional value
        notional_value = position_size * entry_price

        # Calculate margin required
        margin_required = notional_value / leverage

        # Calculate position as % of balance
        position_pct = (margin_required / balance) * 100

        # Calculate liquidation price (simplified)
        # For LONG: liquidation when loss = margin
        # For SHORT: liquidation when profit needed = margin
        liquidation_distance = 100 / leverage  # % distance to liquidation

        # Risk classification
        if position_pct > 50:
            risk_level = "EXTREME"
        elif position_pct > 30:
            risk_level = "HIGH"
        elif position_pct > 10:
            risk_level = "MODERATE"
        elif position_pct > 5:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"

        return json.dumps({
            "success": True,
            "balance": balance,
            "entry_price": entry_price,
            "position_size": position_size,
            "leverage": leverage,
            "notional_value": round(notional_value, 2),
            "margin_required": round(margin_required, 2),
            "position_as_percent_of_balance": round(position_pct, 2),
            "liquidation_distance_percent": round(liquidation_distance, 2),
            "risk_level": risk_level,
            "is_acceptable": position_pct <= 30,  # Max 30% recommended
            "warning": None if position_pct <= 30 else f"Position size is {risk_level} risk",
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool("Get Recent Performance")
def get_recent_performance(lookback_hours: int = 24) -> str:
    """
    Get recent trading performance metrics.

    Args:
        lookback_hours: Hours to look back (default: 24)

    Returns:
        JSON string with performance metrics
    """
    try:
        from datetime import datetime, timedelta

        cutoff_time = (datetime.now() - timedelta(hours=lookback_hours)).isoformat()

        conn = db.get_connection()
        cursor = conn.cursor()

        # Get recent trades
        cursor.execute('''
            SELECT * FROM trades
            WHERE timestamp >= ? AND pnl IS NOT NULL
        ''', (cutoff_time,))
        trades = cursor.fetchall()

        if not trades:
            return json.dumps({
                "success": True,
                "lookback_hours": lookback_hours,
                "total_trades": 0,
                "no_data": True
            }, indent=2)

        # Calculate metrics
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] < 0]

        total_pnl = sum(t['pnl'] for t in trades)
        total_wins = sum(t['pnl'] for t in winning_trades)
        total_losses = abs(sum(t['pnl'] for t in losing_trades))

        win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        return json.dumps({
            "success": True,
            "lookback_hours": lookback_hours,
            "total_trades": len(trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(total_wins / len(winning_trades), 2) if winning_trades else 0,
            "avg_loss": round(total_losses / len(losing_trades), 2) if losing_trades else 0,
            "profit_factor": round(profit_factor, 2),
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


# Export all tools as a list
risk_tools = [
    get_portfolio_status,
    calculate_position_size,
    check_daily_loss_limit,
    calculate_stop_loss_take_profit,
    check_market_stability,
    calculate_risk_metrics,
    get_recent_performance
]


if __name__ == "__main__":
    print("🛡️  Risk Assessment Tools Test")
    print("=" * 60)

    # Test get_portfolio_status
    print("\n1. Testing get_portfolio_status...")
    result = get_portfolio_status()
    print(result)

    # Test calculate_position_size
    print("\n2. Testing calculate_position_size...")
    result = calculate_position_size(65000, 63700, 2.0)
    print(result)

    # Test check_market_stability
    print("\n3. Testing check_market_stability...")
    result = check_market_stability()
    print(result)

    # Test calculate_risk_metrics
    print("\n4. Testing calculate_risk_metrics...")
    result = calculate_risk_metrics(65000, 0.1, 10)
    print(result)

    print("\n" + "=" * 60)
    print("✅ Risk Assessment Tools Test Complete")
