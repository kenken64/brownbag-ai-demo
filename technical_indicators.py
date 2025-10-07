"""
Technical Indicators Module
Calculates all technical indicators for trading signals
Falls back to pandas-based calculations if TA-Lib is not available
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple


def calculate_rsi(data: pd.Series, period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI)

    Args:
        data: Price data series
        period: RSI period (default: 14)

    Returns:
        Current RSI value
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0


def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
    """
    Calculate MACD (Moving Average Convergence Divergence)

    Args:
        data: Price data series
        fast: Fast EMA period (default: 12)
        slow: Slow EMA period (default: 26)
        signal: Signal line period (default: 9)

    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    exp1 = data.ewm(span=fast, adjust=False).mean()
    exp2 = data.ewm(span=slow, adjust=False).mean()

    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return (
        float(macd_line.iloc[-1]),
        float(signal_line.iloc[-1]),
        float(histogram.iloc[-1])
    )


def calculate_ema(data: pd.Series, period: int) -> float:
    """
    Calculate Exponential Moving Average (EMA)

    Args:
        data: Price data series
        period: EMA period

    Returns:
        Current EMA value
    """
    ema = data.ewm(span=period, adjust=False).mean()
    return float(ema.iloc[-1])


def calculate_sma(data: pd.Series, period: int) -> float:
    """
    Calculate Simple Moving Average (SMA)

    Args:
        data: Price data series
        period: SMA period

    Returns:
        Current SMA value
    """
    sma = data.rolling(window=period).mean()
    return float(sma.iloc[-1])


def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[float, float, float]:
    """
    Calculate Bollinger Bands

    Args:
        data: Price data series
        period: Period for SMA (default: 20)
        std_dev: Number of standard deviations (default: 2)

    Returns:
        Tuple of (Upper band, Middle band, Lower band)
    """
    sma = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()

    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)

    return (
        float(upper_band.iloc[-1]),
        float(sma.iloc[-1]),
        float(lower_band.iloc[-1])
    )


def calculate_vwap(df: pd.DataFrame) -> float:
    """
    Calculate Volume Weighted Average Price (VWAP)

    Args:
        df: DataFrame with 'high', 'low', 'close', 'volume' columns

    Returns:
        Current VWAP value
    """
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()

    return float(vwap.iloc[-1])


def calculate_all_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate all technical indicators for the trading system

    Args:
        df: DataFrame with OHLCV data

    Returns:
        Dictionary containing all calculated indicators
    """
    close_prices = df['close']

    # Calculate all indicators
    indicators = {
        'rsi': calculate_rsi(close_prices),
        'ema_9': calculate_ema(close_prices, 9),
        'ema_21': calculate_ema(close_prices, 21),
        'sma_50': calculate_sma(close_prices, 50),
        'vwap': calculate_vwap(df),
        'current_price': float(close_prices.iloc[-1]),
        'volume': float(df['volume'].iloc[-1])
    }

    # MACD
    macd, macd_signal, macd_histogram = calculate_macd(close_prices)
    indicators['macd'] = macd
    indicators['macd_signal'] = macd_signal
    indicators['macd_histogram'] = macd_histogram

    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(close_prices)
    indicators['bb_upper'] = bb_upper
    indicators['bb_middle'] = bb_middle
    indicators['bb_lower'] = bb_lower

    return indicators


def generate_signal_from_indicators(indicators: Dict[str, Any], min_threshold: int = 3) -> Tuple[str, int]:
    """
    Generate trading signal based on multiple technical indicators

    Args:
        indicators: Dictionary of calculated indicators
        min_threshold: Minimum signal strength to act (default: 3)

    Returns:
        Tuple of (signal, strength)
    """
    signal_strength = 0

    # RSI Signals
    if indicators['rsi'] < 30:
        signal_strength += 1  # Oversold - bullish
    elif indicators['rsi'] > 70:
        signal_strength -= 1  # Overbought - bearish

    # MACD Signals
    if indicators['macd'] > indicators['macd_signal'] and indicators['macd_histogram'] > 0:
        signal_strength += 1  # Bullish MACD
    elif indicators['macd'] < indicators['macd_signal'] and indicators['macd_histogram'] < 0:
        signal_strength -= 1  # Bearish MACD

    # VWAP Signals
    if indicators['current_price'] > indicators['vwap']:
        signal_strength += 1  # Price above VWAP - bullish
    else:
        signal_strength -= 1  # Price below VWAP - bearish

    # EMA Crossover Signals
    if indicators['ema_9'] > indicators['ema_21']:
        signal_strength += 2  # Golden cross - strong bullish
    else:
        signal_strength -= 2  # Death cross - strong bearish

    # Price vs SMA
    if indicators['current_price'] > indicators['sma_50']:
        signal_strength += 1  # Above long-term average - bullish
    else:
        signal_strength -= 1  # Below long-term average - bearish

    # Bollinger Bands
    if indicators['current_price'] <= indicators['bb_lower']:
        signal_strength += 1  # At lower band - potential bounce
    elif indicators['current_price'] >= indicators['bb_upper']:
        signal_strength -= 1  # At upper band - potential pullback

    # Determine signal
    if signal_strength >= min_threshold:
        signal = "BUY"
    elif signal_strength <= -min_threshold:
        signal = "SELL"
    else:
        signal = "HOLD"

    return signal, signal_strength


def get_indicator_summary(indicators: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of current indicators

    Args:
        indicators: Dictionary of calculated indicators

    Returns:
        Summary string
    """
    summary = f"""
    📈 Technical Indicators Summary:
    - Price: ${indicators['current_price']:.4f}
    - RSI(14): {indicators['rsi']:.2f}
    - MACD: {indicators['macd']:.4f} | Signal: {indicators['macd_signal']:.4f} | Histogram: {indicators['macd_histogram']:.4f}
    - VWAP: ${indicators['vwap']:.4f}
    - EMA(9): ${indicators['ema_9']:.4f} | EMA(21): ${indicators['ema_21']:.4f}
    - SMA(50): ${indicators['sma_50']:.4f}
    - Bollinger Bands: Upper ${indicators['bb_upper']:.4f} | Middle ${indicators['bb_middle']:.4f} | Lower ${indicators['bb_lower']:.4f}
    - Volume: {indicators['volume']:.2f}
    """
    return summary.strip()


if __name__ == "__main__":
    # Test with sample data
    print("Testing technical indicators module...")

    # Create sample OHLCV data
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    sample_df = pd.DataFrame({
        'open': np.random.uniform(100, 110, 100),
        'high': np.random.uniform(105, 115, 100),
        'low': np.random.uniform(95, 105, 100),
        'close': np.random.uniform(100, 110, 100),
        'volume': np.random.uniform(1000, 5000, 100)
    }, index=dates)

    # Calculate indicators
    indicators = calculate_all_indicators(sample_df)
    print("\nCalculated Indicators:")
    print(get_indicator_summary(indicators))

    # Generate signal
    signal, strength = generate_signal_from_indicators(indicators)
    print(f"\n🔍 Signal: {signal} (Strength: {strength})")
