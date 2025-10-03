"""
Chart Generator Module
Generates candlestick charts with technical indicators using mplfinance
Saves charts to charts/ directory for OpenAI GPT-4o Vision analysis
"""

import os
import pandas as pd
import mplfinance as mpf
from datetime import datetime
from typing import Optional, Dict, Any, List
import matplotlib.pyplot as plt

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class ChartGenerator:
    """
    Generates professional candlestick charts with technical indicators
    Designed for AI analysis by OpenAI GPT-4o Vision API
    """

    def __init__(self, output_dir: str = "charts"):
        """
        Initialize chart generator

        Args:
            output_dir: Directory to save chart images
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"📊 Chart Generator initialized (output: {output_dir}/)")

    def prepare_dataframe(self, klines: List[List]) -> pd.DataFrame:
        """
        Convert Binance klines to DataFrame suitable for mplfinance

        Args:
            klines: Raw klines data from Binance

        Returns:
            DataFrame with OHLCV data and datetime index
        """
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])

        # Convert to numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])

        # Convert timestamp to datetime and set as index
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        # Keep only OHLCV columns
        df = df[['open', 'high', 'low', 'close', 'volume']]

        return df

    def add_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add moving averages to DataFrame

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with MA columns added
        """
        df['EMA9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['SMA50'] = df['close'].rolling(window=50).mean()

        return df

    def add_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.DataFrame:
        """
        Add Bollinger Bands to DataFrame

        Args:
            df: DataFrame with OHLCV data
            period: Moving average period
            std: Number of standard deviations

        Returns:
            DataFrame with BB columns added
        """
        df['BB_Middle'] = df['close'].rolling(window=period).mean()
        df['BB_Std'] = df['close'].rolling(window=period).std()
        df['BB_Upper'] = df['BB_Middle'] + (std * df['BB_Std'])
        df['BB_Lower'] = df['BB_Middle'] - (std * df['BB_Std'])

        return df

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Calculate RSI and add to DataFrame

        Args:
            df: DataFrame with OHLCV data
            period: RSI period

        Returns:
            DataFrame with RSI column added
        """
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        return df

    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> pd.DataFrame:
        """
        Calculate MACD and add to DataFrame

        Args:
            df: DataFrame with OHLCV data
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            DataFrame with MACD columns added
        """
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

        return df

    def generate_chart(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str = "1m",
        indicators: Optional[Dict[str, bool]] = None,
        save_path: Optional[str] = None
    ) -> str:
        """
        Generate candlestick chart with technical indicators

        Args:
            df: DataFrame with OHLCV data (must have datetime index)
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            timeframe: Timeframe (e.g., '1m', '5m', '15m', '1h')
            indicators: Dict of indicators to include (default: all)
            save_path: Custom save path (default: auto-generated)

        Returns:
            Path to saved chart image
        """
        if indicators is None:
            indicators = {
                'ema': True,
                'sma': True,
                'bollinger': True,
                'volume': True
            }

        # Add technical indicators to DataFrame
        df_plot = df.copy()

        if indicators.get('ema') or indicators.get('sma'):
            df_plot = self.add_moving_averages(df_plot)

        if indicators.get('bollinger'):
            df_plot = self.add_bollinger_bands(df_plot)

        # Prepare additional plots
        add_plots = []

        # Add EMAs
        if indicators.get('ema'):
            add_plots.append(mpf.make_addplot(df_plot['EMA9'], color='blue', width=1.5, label='EMA 9'))
            add_plots.append(mpf.make_addplot(df_plot['EMA21'], color='orange', width=1.5, label='EMA 21'))

        # Add SMA
        if indicators.get('sma'):
            add_plots.append(mpf.make_addplot(df_plot['SMA50'], color='purple', width=2, label='SMA 50'))

        # Add Bollinger Bands
        if indicators.get('bollinger'):
            add_plots.append(mpf.make_addplot(df_plot['BB_Upper'], color='gray', linestyle='--', width=1, alpha=0.5))
            add_plots.append(mpf.make_addplot(df_plot['BB_Lower'], color='gray', linestyle='--', width=1, alpha=0.5))

        # Chart style
        style = mpf.make_mpf_style(
            base_mpf_style='charles',
            marketcolors=mpf.make_marketcolors(
                up='#26a69a',
                down='#ef5350',
                edge='inherit',
                wick='inherit',
                volume='in',
                alpha=0.9
            ),
            gridstyle='-',
            gridcolor='#e0e0e0',
            gridaxis='both',
            y_on_right=False
        )

        # Generate filename if not provided
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{symbol}_{timeframe}_{timestamp}.png"
            save_path = os.path.join(self.output_dir, filename)

        # Create chart title
        latest_price = df_plot['close'].iloc[-1]
        price_change = ((df_plot['close'].iloc[-1] - df_plot['close'].iloc[0]) / df_plot['close'].iloc[0]) * 100
        change_emoji = "📈" if price_change > 0 else "📉"
        title = f"{symbol} {timeframe} - ${latest_price:.2f} ({change_emoji} {price_change:+.2f}%)"

        # Plot configuration
        kwargs = {
            'type': 'candle',
            'style': style,
            'title': title,
            'ylabel': 'Price ($)',
            'volume': indicators.get('volume', True),
            'figsize': (16, 10),
            'tight_layout': True,
            'savefig': save_path,
            'returnfig': False,
            'datetime_format': '%H:%M' if timeframe in ['1m', '5m', '15m'] else '%d-%b'
        }

        if add_plots:
            kwargs['addplot'] = add_plots

        # Generate chart
        try:
            mpf.plot(df_plot, **kwargs)
            print(f"✅ Chart saved: {save_path}")
            return save_path
        except Exception as e:
            print(f"❌ Error generating chart: {e}")
            raise

    def generate_chart_with_all_indicators(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str = "15m"
    ) -> str:
        """
        Generate comprehensive chart with all indicators for AI analysis

        Args:
            df: DataFrame with OHLCV data
            symbol: Trading pair symbol
            timeframe: Timeframe

        Returns:
            Path to saved chart image
        """
        # Add all indicators
        df_plot = df.copy()
        df_plot = self.add_moving_averages(df_plot)
        df_plot = self.add_bollinger_bands(df_plot)
        df_plot = self.calculate_rsi(df_plot)
        df_plot = self.calculate_macd(df_plot)

        # Create subplots
        add_plots = []

        # Main chart: EMAs, SMA, Bollinger Bands
        add_plots.append(mpf.make_addplot(df_plot['EMA9'], color='blue', width=1.5, panel=0))
        add_plots.append(mpf.make_addplot(df_plot['EMA21'], color='orange', width=1.5, panel=0))
        add_plots.append(mpf.make_addplot(df_plot['SMA50'], color='purple', width=2, panel=0))
        add_plots.append(mpf.make_addplot(df_plot['BB_Upper'], color='gray', linestyle='--', width=1, alpha=0.5, panel=0))
        add_plots.append(mpf.make_addplot(df_plot['BB_Lower'], color='gray', linestyle='--', width=1, alpha=0.5, panel=0))

        # Panel 1: RSI
        add_plots.append(mpf.make_addplot(df_plot['RSI'], color='purple', width=2, panel=1, ylabel='RSI'))
        # RSI reference lines
        add_plots.append(mpf.make_addplot([70] * len(df_plot), color='red', linestyle='--', width=1, panel=1, alpha=0.5))
        add_plots.append(mpf.make_addplot([30] * len(df_plot), color='green', linestyle='--', width=1, panel=1, alpha=0.5))

        # Panel 2: MACD
        add_plots.append(mpf.make_addplot(df_plot['MACD'], color='blue', width=1.5, panel=2, ylabel='MACD'))
        add_plots.append(mpf.make_addplot(df_plot['MACD_Signal'], color='red', width=1.5, panel=2))
        # MACD Histogram
        colors = ['green' if val >= 0 else 'red' for val in df_plot['MACD_Histogram']]
        add_plots.append(mpf.make_addplot(df_plot['MACD_Histogram'], type='bar', color=colors, panel=2, alpha=0.5))

        # Chart style
        style = mpf.make_mpf_style(
            base_mpf_style='charles',
            marketcolors=mpf.make_marketcolors(
                up='#26a69a',
                down='#ef5350',
                edge='inherit',
                wick='inherit',
                volume='in',
                alpha=0.9
            ),
            gridstyle='-',
            gridcolor='#e0e0e0',
            gridaxis='both',
            y_on_right=False
        )

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_{timeframe}_FULL_{timestamp}.png"
        save_path = os.path.join(self.output_dir, filename)

        # Create chart title
        latest_price = df_plot['close'].iloc[-1]
        price_change = ((df_plot['close'].iloc[-1] - df_plot['close'].iloc[0]) / df_plot['close'].iloc[0]) * 100
        change_emoji = "📈" if price_change > 0 else "📉"
        latest_rsi = df_plot['RSI'].iloc[-1]
        latest_macd = df_plot['MACD_Histogram'].iloc[-1]

        title = f"{symbol} {timeframe} - ${latest_price:.2f} ({change_emoji} {price_change:+.2f}%) | RSI: {latest_rsi:.1f} | MACD: {latest_macd:+.4f}"

        # Generate chart
        try:
            fig, axes = mpf.plot(
                df_plot,
                type='candle',
                style=style,
                title=title,
                ylabel='Price ($)',
                volume=True,
                addplot=add_plots,
                figsize=(18, 12),
                panel_ratios=(6, 2, 2, 2),  # Main, Volume, RSI, MACD
                tight_layout=True,
                returnfig=True
            )

            # Save figure
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close(fig)

            print(f"✅ Comprehensive chart saved: {save_path}")
            print(f"   Price: ${latest_price:.2f} ({price_change:+.2f}%)")
            print(f"   RSI: {latest_rsi:.1f}")
            print(f"   MACD Histogram: {latest_macd:+.4f}")

            return save_path

        except Exception as e:
            print(f"❌ Error generating comprehensive chart: {e}")
            raise


if __name__ == "__main__":
    # Test chart generator
    print("Testing Chart Generator...\n")

    # Import binance client for test data
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.binance_client import BinanceFuturesClient

    # Initialize
    generator = ChartGenerator(output_dir="charts")
    testnet = os.getenv('USE_TESTNET', 'true').lower() == 'true'
    binance = BinanceFuturesClient(testnet=testnet)

    # Get market data
    symbol = os.getenv('TRADING_PAIR', 'BTCUSDT')
    print(f"\n1. Fetching market data for {symbol}...")
    klines = binance.get_klines(symbol=symbol, interval='15m', limit=100)

    if klines:
        # Prepare DataFrame
        print("\n2. Preparing DataFrame...")
        df = generator.prepare_dataframe(klines)
        print(f"   Loaded {len(df)} candles")
        print(f"   Period: {df.index[0]} to {df.index[-1]}")

        # Test 1: Simple chart with EMAs
        print("\n3. Generating simple chart (EMAs + Volume)...")
        chart_path = generator.generate_chart(
            df=df,
            symbol=symbol,
            timeframe='15m',
            indicators={'ema': True, 'volume': True}
        )

        # Test 2: Comprehensive chart with all indicators
        print("\n4. Generating comprehensive chart (All Indicators)...")
        full_chart_path = generator.generate_chart_with_all_indicators(
            df=df,
            symbol=symbol,
            timeframe='15m'
        )

        print(f"\n✅ Chart Generator test completed!")
        print(f"   Simple chart: {chart_path}")
        print(f"   Full chart: {full_chart_path}")

    else:
        print("❌ Failed to fetch market data")
