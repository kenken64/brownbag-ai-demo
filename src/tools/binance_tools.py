#!/usr/bin/env python3
"""
Binance Tools for CrewAI Agents
Provides real-time market data access from Binance
"""

import os
import sys
import json
from typing import Dict, List, Optional
from datetime import datetime
from crewai_tools import tool

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from binance_client import BinanceClient


# Initialize Binance client
binance_client = BinanceClient()


@tool("Get Current Price")
def get_current_price(symbol: str = "BTCUSDT") -> str:
    """
    Get current price for a trading pair from Binance.

    Args:
        symbol: Trading pair (e.g., "BTCUSDT", "ETHUSDT")

    Returns:
        JSON string with current price information
    """
    try:
        price = binance_client.get_current_price(symbol)

        return json.dumps({
            "success": True,
            "symbol": symbol,
            "price": price,
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "symbol": symbol
        }, indent=2)


@tool("Get Recent Price History")
def get_price_history(
    symbol: str = "BTCUSDT",
    interval: str = "1m",
    limit: int = 60
) -> str:
    """
    Get recent price history (klines/candlesticks) from Binance.

    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Number of candles (max 1000)

    Returns:
        JSON string with price history and statistics
    """
    try:
        klines = binance_client.get_klines(symbol, interval, min(limit, 1000))

        if not klines:
            return json.dumps({
                "success": False,
                "error": "No data returned",
                "symbol": symbol
            }, indent=2)

        # Calculate statistics
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]

        current_price = closes[-1]
        start_price = closes[0]
        price_change = current_price - start_price
        price_change_pct = (price_change / start_price) * 100

        high_price = max(closes)
        low_price = min(closes)
        avg_price = sum(closes) / len(closes)
        avg_volume = sum(volumes) / len(volumes)

        return json.dumps({
            "success": True,
            "symbol": symbol,
            "interval": interval,
            "candles_count": len(klines),
            "current_price": current_price,
            "start_price": start_price,
            "price_change": price_change,
            "price_change_percent": round(price_change_pct, 2),
            "high": high_price,
            "low": low_price,
            "avg_price": round(avg_price, 2),
            "avg_volume": round(avg_volume, 2),
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "symbol": symbol
        }, indent=2)


@tool("Calculate Price Change")
def calculate_price_change(
    symbol: str = "BTCUSDT",
    timeframe_minutes: int = 60
) -> str:
    """
    Calculate price change percentage over a specific timeframe.

    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        timeframe_minutes: Timeframe in minutes (1, 5, 15, 60, 240, 1440)

    Returns:
        JSON string with price change analysis
    """
    try:
        # Map timeframe to interval
        if timeframe_minutes <= 1:
            interval = "1m"
            limit = 1
        elif timeframe_minutes <= 5:
            interval = "1m"
            limit = 5
        elif timeframe_minutes <= 15:
            interval = "1m"
            limit = 15
        elif timeframe_minutes <= 60:
            interval = "1m"
            limit = 60
        elif timeframe_minutes <= 240:
            interval = "5m"
            limit = 48
        else:
            interval = "1h"
            limit = min(timeframe_minutes // 60, 24)

        klines = binance_client.get_klines(symbol, interval, limit + 1)

        if len(klines) < 2:
            return json.dumps({
                "success": False,
                "error": "Insufficient data",
                "symbol": symbol
            }, indent=2)

        start_price = float(klines[0][4])  # Close of first candle
        current_price = float(klines[-1][4])  # Close of last candle

        price_change = current_price - start_price
        price_change_pct = (price_change / start_price) * 100

        # Determine direction
        if price_change_pct > 0:
            direction = "PUMP"
        elif price_change_pct < 0:
            direction = "DUMP"
        else:
            direction = "FLAT"

        # Calculate magnitude
        abs_change = abs(price_change_pct)
        if abs_change >= 15:
            magnitude = "EXTREME"
        elif abs_change >= 10:
            magnitude = "LARGE"
        elif abs_change >= 5:
            magnitude = "MODERATE"
        elif abs_change >= 2:
            magnitude = "SMALL"
        else:
            magnitude = "MINIMAL"

        return json.dumps({
            "success": True,
            "symbol": symbol,
            "timeframe_minutes": timeframe_minutes,
            "start_price": start_price,
            "current_price": current_price,
            "price_change": price_change,
            "price_change_percent": round(price_change_pct, 2),
            "direction": direction,
            "magnitude": magnitude,
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "symbol": symbol
        }, indent=2)


@tool("Get Account Balance")
def get_account_balance() -> str:
    """
    Get current account balance from Binance Futures.

    Returns:
        JSON string with account balance information
    """
    try:
        balance = binance_client.get_account_balance()

        return json.dumps({
            "success": True,
            "balance": balance,
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool("Get Open Positions")
def get_open_positions(symbol: Optional[str] = None) -> str:
    """
    Get current open positions from Binance Futures.

    Args:
        symbol: Optional trading pair filter (e.g., "BTCUSDT")

    Returns:
        JSON string with open positions
    """
    try:
        positions = binance_client.get_open_positions(symbol)

        # Calculate total exposure
        total_notional = sum(
            abs(float(pos['positionAmt']) * float(pos['entryPrice']))
            for pos in positions
        )

        return json.dumps({
            "success": True,
            "positions_count": len(positions),
            "total_notional_value": round(total_notional, 2),
            "positions": [
                {
                    "symbol": pos['symbol'],
                    "side": "LONG" if float(pos['positionAmt']) > 0 else "SHORT",
                    "size": abs(float(pos['positionAmt'])),
                    "entry_price": float(pos['entryPrice']),
                    "unrealized_pnl": float(pos['unRealizedProfit']),
                    "leverage": int(pos['leverage'])
                }
                for pos in positions
            ],
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@tool("Detect Volume Spike")
def detect_volume_spike(
    symbol: str = "BTCUSDT",
    lookback_periods: int = 20,
    spike_multiplier: float = 3.0
) -> str:
    """
    Detect if current volume is significantly higher than average.

    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        lookback_periods: Number of periods to calculate average (default: 20)
        spike_multiplier: Multiplier for spike detection (default: 3x)

    Returns:
        JSON string with volume spike analysis
    """
    try:
        # Get recent 1-minute candles
        klines = binance_client.get_klines(symbol, "1m", lookback_periods + 1)

        if len(klines) < lookback_periods + 1:
            return json.dumps({
                "success": False,
                "error": "Insufficient data",
                "symbol": symbol
            }, indent=2)

        # Extract volumes
        volumes = [float(k[5]) for k in klines]
        current_volume = volumes[-1]
        historical_volumes = volumes[:-1]

        # Calculate average and spike threshold
        avg_volume = sum(historical_volumes) / len(historical_volumes)
        spike_threshold = avg_volume * spike_multiplier

        # Detect spike
        is_spike = current_volume >= spike_threshold
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

        return json.dumps({
            "success": True,
            "symbol": symbol,
            "is_volume_spike": is_spike,
            "current_volume": round(current_volume, 2),
            "avg_volume": round(avg_volume, 2),
            "volume_ratio": round(volume_ratio, 2),
            "spike_threshold": round(spike_threshold, 2),
            "spike_multiplier": spike_multiplier,
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "symbol": symbol
        }, indent=2)


@tool("Get Market Volatility")
def get_market_volatility(
    symbol: str = "BTCUSDT",
    periods: int = 20
) -> str:
    """
    Calculate market volatility using standard deviation of price changes.

    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        periods: Number of periods to analyze (default: 20)

    Returns:
        JSON string with volatility metrics
    """
    try:
        # Get recent 1-minute candles
        klines = binance_client.get_klines(symbol, "1m", periods + 1)

        if len(klines) < periods + 1:
            return json.dumps({
                "success": False,
                "error": "Insufficient data",
                "symbol": symbol
            }, indent=2)

        # Calculate price changes
        closes = [float(k[4]) for k in klines]
        price_changes = [
            ((closes[i] - closes[i-1]) / closes[i-1]) * 100
            for i in range(1, len(closes))
        ]

        # Calculate volatility metrics
        import statistics

        avg_change = statistics.mean(price_changes)
        volatility = statistics.stdev(price_changes) if len(price_changes) > 1 else 0
        max_change = max(price_changes)
        min_change = min(price_changes)

        # Classify volatility
        if volatility >= 2.0:
            volatility_level = "EXTREME"
        elif volatility >= 1.0:
            volatility_level = "HIGH"
        elif volatility >= 0.5:
            volatility_level = "MODERATE"
        elif volatility >= 0.2:
            volatility_level = "LOW"
        else:
            volatility_level = "VERY_LOW"

        return json.dumps({
            "success": True,
            "symbol": symbol,
            "volatility": round(volatility, 4),
            "volatility_level": volatility_level,
            "avg_price_change_pct": round(avg_change, 4),
            "max_price_change_pct": round(max_change, 2),
            "min_price_change_pct": round(min_change, 2),
            "periods": periods,
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "symbol": symbol
        }, indent=2)


# Export all tools as a list for easy import
binance_tools = [
    get_current_price,
    get_price_history,
    calculate_price_change,
    get_account_balance,
    get_open_positions,
    detect_volume_spike,
    get_market_volatility
]


if __name__ == "__main__":
    print("🔧 Binance Tools Test")
    print("=" * 60)

    # Test get_current_price
    print("\n1. Testing get_current_price...")
    result = get_current_price("BTCUSDT")
    print(result)

    # Test calculate_price_change
    print("\n2. Testing calculate_price_change (60 min)...")
    result = calculate_price_change("BTCUSDT", 60)
    print(result)

    # Test detect_volume_spike
    print("\n3. Testing detect_volume_spike...")
    result = detect_volume_spike("BTCUSDT")
    print(result)

    # Test get_market_volatility
    print("\n4. Testing get_market_volatility...")
    result = get_market_volatility("BTCUSDT")
    print(result)

    print("\n" + "=" * 60)
    print("✅ Binance Tools Test Complete")
