"""
Technical Indicators Module
Calculates technical indicators for trading signal generation
Supports both TA-Lib and pandas fallback implementations
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional

# Try to import TA-Lib, fall back to pandas if not available
try:
    import talib
    TALIB_AVAILABLE = True
    print("✅ TA-Lib library loaded")
except ImportError:
    TALIB_AVAILABLE = False
    print("⚠️ TA-Lib not available, using pandas fallback")


class TechnicalIndicators:
    """Calculate technical indicators for trading signals"""

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        if TALIB_AVAILABLE:
            return talib.RSI(prices, timeperiod=period)
        else:
            # Pandas fallback
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

    @staticmethod
    def calculate_macd(
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD, Signal line, and Histogram"""
        if TALIB_AVAILABLE:
            macd, signal, histogram = talib.MACD(
                prices,
                fastperiod=fast_period,
                slowperiod=slow_period,
                signalperiod=signal_period
            )
            return macd, signal, histogram
        else:
            # Pandas fallback
            ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
            ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
            macd = ema_fast - ema_slow
            signal = macd.ewm(span=signal_period, adjust=False).mean()
            histogram = macd - signal
            return macd, signal, histogram

    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        if TALIB_AVAILABLE:
            return talib.EMA(prices, timeperiod=period)
        else:
            return prices.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        if TALIB_AVAILABLE:
            return talib.SMA(prices, timeperiod=period)
        else:
            return prices.rolling(window=period).mean()

    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands (upper, middle, lower)"""
        if TALIB_AVAILABLE:
            upper, middle, lower = talib.BBANDS(
                prices,
                timeperiod=period,
                nbdevup=std_dev,
                nbdevdn=std_dev
            )
            return upper, middle, lower
        else:
            # Pandas fallback
            middle = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            return upper, middle, lower

    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """
        Calculate Volume Weighted Average Price

        Args:
            df: DataFrame with 'high', 'low', 'close', 'volume' columns
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate all technical indicators for the most recent candle

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dictionary with all indicator values
        """
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']

        # Calculate indicators
        rsi = TechnicalIndicators.calculate_rsi(close)
        macd, macd_signal, macd_histogram = TechnicalIndicators.calculate_macd(close)
        ema9 = TechnicalIndicators.calculate_ema(close, 9)
        ema21 = TechnicalIndicators.calculate_ema(close, 21)
        sma50 = TechnicalIndicators.calculate_sma(close, 50)
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.calculate_bollinger_bands(close)
        vwap = TechnicalIndicators.calculate_vwap(df)

        # Get latest values
        indicators = {
            'price': float(close.iloc[-1]),
            'rsi': float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0,
            'macd': float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0.0,
            'macd_signal': float(macd_signal.iloc[-1]) if not pd.isna(macd_signal.iloc[-1]) else 0.0,
            'macd_histogram': float(macd_histogram.iloc[-1]) if not pd.isna(macd_histogram.iloc[-1]) else 0.0,
            'ema9': float(ema9.iloc[-1]) if not pd.isna(ema9.iloc[-1]) else close.iloc[-1],
            'ema21': float(ema21.iloc[-1]) if not pd.isna(ema21.iloc[-1]) else close.iloc[-1],
            'sma50': float(sma50.iloc[-1]) if not pd.isna(sma50.iloc[-1]) else close.iloc[-1],
            'bb_upper': float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else close.iloc[-1],
            'bb_middle': float(bb_middle.iloc[-1]) if not pd.isna(bb_middle.iloc[-1]) else close.iloc[-1],
            'bb_lower': float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else close.iloc[-1],
            'vwap': float(vwap.iloc[-1]) if not pd.isna(vwap.iloc[-1]) else close.iloc[-1],
            'volume': float(volume.iloc[-1])
        }

        return indicators


class SignalGenerator:
    """Generate weighted trading signals from technical indicators"""

    def __init__(self, min_threshold: int = 3):
        """
        Initialize signal generator

        Args:
            min_threshold: Minimum signal strength to trigger action (default: 3)
        """
        self.min_threshold = min_threshold

    def generate_signal(self, indicators: Dict[str, float]) -> Tuple[str, int]:
        """
        Generate weighted trading signal

        Signal weights:
        - MACD bullish/bearish: ±1
        - VWAP position: ±1
        - EMA crossovers: ±1, ±2, ±3
        - RSI overbought/oversold: ±1
        - Bollinger Bands: ±1

        Returns:
            (signal_type, signal_strength): 'BUY', 'SELL', or 'HOLD' with strength
        """
        signal_strength = 0

        price = indicators['price']
        rsi = indicators['rsi']
        macd = indicators['macd']
        macd_signal = indicators['macd_signal']
        macd_histogram = indicators['macd_histogram']
        vwap = indicators['vwap']
        ema9 = indicators['ema9']
        ema21 = indicators['ema21']
        sma50 = indicators['sma50']
        bb_upper = indicators['bb_upper']
        bb_lower = indicators['bb_lower']

        # MACD signals (±1)
        if macd > macd_signal and macd_histogram > 0:
            signal_strength += 1  # Bullish
        elif macd < macd_signal and macd_histogram < 0:
            signal_strength -= 1  # Bearish

        # VWAP signals (±1)
        if price > vwap:
            signal_strength += 1  # Above VWAP = Bullish
        else:
            signal_strength -= 1  # Below VWAP = Bearish

        # EMA crossovers (±1, ±2, ±3)
        if ema9 > ema21:
            signal_strength += 1  # Short-term bullish
        else:
            signal_strength -= 1  # Short-term bearish

        if ema9 > sma50:
            signal_strength += 2  # Medium-term bullish
        else:
            signal_strength -= 2  # Medium-term bearish

        if ema21 > sma50:
            signal_strength += 3  # Long-term bullish
        else:
            signal_strength -= 3  # Long-term bearish

        # RSI signals (±1)
        if rsi < 30:
            signal_strength += 1  # Oversold = Bullish
        elif rsi > 70:
            signal_strength -= 1  # Overbought = Bearish

        # Bollinger Bands (±1)
        if price < bb_lower:
            signal_strength += 1  # Below lower band = Bullish
        elif price > bb_upper:
            signal_strength -= 1  # Above upper band = Bearish

        # Determine signal type
        if signal_strength >= self.min_threshold:
            signal_type = 'BUY'
        elif signal_strength <= -self.min_threshold:
            signal_type = 'SELL'
        else:
            signal_type = 'HOLD'

        return signal_type, signal_strength


if __name__ == "__main__":
    # Test indicators
    print("Technical indicators module loaded successfully")

    # Create test data
    test_data = pd.DataFrame({
        'high': [100, 101, 102, 103, 104],
        'low': [99, 100, 101, 102, 103],
        'close': [100, 101, 102, 103, 104],
        'volume': [1000, 1100, 1200, 1300, 1400]
    })

    # Test calculation
    # indicators = TechnicalIndicators.calculate_all_indicators(test_data)
    # print(f"Test indicators: {indicators}")

    # Test signal generation
    signal_gen = SignalGenerator()
    print(f"Signal generator initialized with threshold: {signal_gen.min_threshold}")