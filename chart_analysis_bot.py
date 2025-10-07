"""
Chart Analysis Bot
Generates charts and uses OpenAI GPT-4o for AI-powered analysis
"""

import os
import sys
import time
import logging
import base64
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from io import BytesIO

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ openai not installed. Install with: pip install openai")

# Try to import Binance client
try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    print("⚠️ python-binance not installed.")

# Import local modules
from database import TradingDatabase
from technical_indicators import calculate_all_indicators

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chart_analysis_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)


class ChartAnalysisBot:
    """AI-powered chart analysis using OpenAI GPT-4o"""

    def __init__(self):
        """Initialize the chart analysis bot"""
        logging.info("🚀 Initializing Chart Analysis Bot...")

        # Load configuration
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_SECRET_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.symbol = os.getenv('TRADING_SYMBOL', 'SUIUSDC')
        self.use_testnet = os.getenv('USE_TESTNET', 'true').lower() == 'true'
        self.analysis_interval = 15 * 60  # 15 minutes in seconds

        # Initialize database
        db_path = os.getenv('DATABASE_PATH', 'trading_bot.db')
        self.db = TradingDatabase(db_path)
        self.db.connect()

        # Initialize Binance client
        self.client = None
        if BINANCE_AVAILABLE and self.api_key and self.api_secret:
            try:
                self.client = Client(self.api_key, self.api_secret, testnet=self.use_testnet)
                logging.info(f"✅ Connected to Binance ({'TESTNET' if self.use_testnet else 'LIVE'})")
            except Exception as e:
                logging.error(f"❌ Failed to connect to Binance: {e}")

        # Initialize OpenAI client
        self.openai_client = None
        if OPENAI_AVAILABLE and self.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logging.info("✅ OpenAI client initialized")
            except Exception as e:
                logging.error(f"❌ Failed to initialize OpenAI: {e}")

        # Latest analysis result
        self.latest_analysis = None

        logging.info("✅ Chart Analysis Bot initialized successfully")

    def get_market_data(self, limit: int = 500) -> Optional[pd.DataFrame]:
        """
        Fetch market data from Binance

        Args:
            limit: Number of candles to fetch

        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            if not self.client:
                logging.warning("⚠️ No Binance client. Cannot fetch market data.")
                return None

            # Get klines (candlestick data)
            klines = self.client.futures_klines(
                symbol=self.symbol,
                interval=Client.KLINE_INTERVAL_15MINUTE,
                limit=limit
            )

            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Convert to appropriate types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            return df

        except Exception as e:
            logging.error(f"❌ Error fetching market data: {e}")
            return None

    def generate_chart(self, df: pd.DataFrame, save_path: str = 'chart_latest.png') -> Optional[str]:
        """
        Generate candlestick chart with technical indicators

        Args:
            df: DataFrame with OHLCV data
            save_path: Path to save chart image

        Returns:
            Path to saved chart or None
        """
        try:
            # Calculate indicators for overlay
            indicators = calculate_all_indicators(df)

            # Prepare EMAs for chart
            ema_9 = df['close'].ewm(span=9, adjust=False).mean()
            ema_21 = df['close'].ewm(span=21, adjust=False).mean()
            sma_50 = df['close'].rolling(window=50).mean()

            # MACD
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            histogram = macd - signal

            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # Bollinger Bands
            bb_sma = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            bb_upper = bb_sma + (bb_std * 2)
            bb_lower = bb_sma - (bb_std * 2)

            # Create additional plots
            apds = [
                mpf.make_addplot(ema_9, color='blue', width=1, label='EMA 9'),
                mpf.make_addplot(ema_21, color='orange', width=1, label='EMA 21'),
                mpf.make_addplot(sma_50, color='red', width=1, label='SMA 50'),
                mpf.make_addplot(bb_upper, color='gray', linestyle='--', width=0.8),
                mpf.make_addplot(bb_lower, color='gray', linestyle='--', width=0.8),
                mpf.make_addplot(macd, panel=2, color='blue', ylabel='MACD'),
                mpf.make_addplot(signal, panel=2, color='red'),
                mpf.make_addplot(histogram, panel=2, type='bar', color='gray'),
                mpf.make_addplot(rsi, panel=3, color='purple', ylabel='RSI'),
            ]

            # Create chart
            style = mpf.make_mpf_style(
                base_mpf_style='charles',
                gridcolor='lightgray',
                y_on_right=False
            )

            fig, axes = mpf.plot(
                df,
                type='candle',
                style=style,
                addplot=apds,
                volume=True,
                panel_ratios=(6, 2, 2, 2),
                figsize=(16, 12),
                title=f'{self.symbol} Technical Analysis - 15min',
                returnfig=True,
                warn_too_much_data=1000
            )

            # Save chart
            fig.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close(fig)

            logging.info(f"✅ Chart saved to {save_path}")
            return save_path

        except Exception as e:
            logging.error(f"❌ Error generating chart: {e}")
            return None

    def analyze_chart_with_ai(self, chart_path: str, indicators: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze chart using OpenAI GPT-4o Vision

        Args:
            chart_path: Path to chart image
            indicators: Current technical indicators

        Returns:
            Analysis result dict or None
        """
        if not self.openai_client:
            logging.warning("⚠️ OpenAI client not initialized")
            return None

        try:
            # Read and encode image
            with open(chart_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Create analysis prompt
            prompt = f"""
            Analyze this cryptocurrency trading chart for {self.symbol} and provide:

            1. RECOMMENDATION: State BUY, SELL, or HOLD
            2. CONFIDENCE: Rate your confidence (Low/Medium/High)
            3. KEY OBSERVATIONS: List 3-5 key technical observations
            4. RISK FACTORS: List 2-3 main risk factors
            5. ANALYSIS: Provide a brief analysis (2-3 sentences)

            Current Technical Indicators:
            - Price: ${indicators['current_price']:.4f}
            - RSI: {indicators['rsi']:.2f}
            - MACD: {indicators['macd']:.4f}
            - EMA 9: ${indicators['ema_9']:.4f}
            - EMA 21: ${indicators['ema_21']:.4f}

            Format your response as:
            RECOMMENDATION: [BUY/SELL/HOLD]
            CONFIDENCE: [Low/Medium/High]
            KEY OBSERVATIONS:
            - [observation 1]
            - [observation 2]
            - [observation 3]
            RISK FACTORS:
            - [risk 1]
            - [risk 2]
            ANALYSIS:
            [Your analysis here]
            """

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            # Parse response
            ai_response = response.choices[0].message.content

            # Extract structured data
            result = self.parse_ai_response(ai_response)
            result['raw_response'] = ai_response
            result['timestamp'] = datetime.now().isoformat()

            logging.info(f"✅ AI Analysis completed: {result['recommendation']} ({result['confidence']})")

            return result

        except Exception as e:
            logging.error(f"❌ Error in AI analysis: {e}")
            return None

    def parse_ai_response(self, response: str) -> Dict[str, Any]:
        """
        Parse AI response into structured data

        Args:
            response: Raw AI response text

        Returns:
            Structured analysis dict
        """
        result = {
            'recommendation': 'HOLD',
            'confidence': 'Medium',
            'key_observations': [],
            'risk_factors': [],
            'analysis_text': ''
        }

        try:
            lines = response.split('\n')
            current_section = None

            for line in lines:
                line = line.strip()

                if line.startswith('RECOMMENDATION:'):
                    result['recommendation'] = line.split(':', 1)[1].strip()
                elif line.startswith('CONFIDENCE:'):
                    result['confidence'] = line.split(':', 1)[1].strip()
                elif line.startswith('KEY OBSERVATIONS:'):
                    current_section = 'observations'
                elif line.startswith('RISK FACTORS:'):
                    current_section = 'risks'
                elif line.startswith('ANALYSIS:'):
                    current_section = 'analysis'
                elif line.startswith('-') and current_section == 'observations':
                    result['key_observations'].append(line[1:].strip())
                elif line.startswith('-') and current_section == 'risks':
                    result['risk_factors'].append(line[1:].strip())
                elif current_section == 'analysis' and line:
                    result['analysis_text'] += line + ' '

            result['analysis_text'] = result['analysis_text'].strip()

        except Exception as e:
            logging.error(f"❌ Error parsing AI response: {e}")

        return result

    def run_analysis(self):
        """Run one analysis cycle"""
        try:
            logging.info("🔍 Starting chart analysis cycle...")

            # Fetch market data
            df = self.get_market_data(limit=500)
            if df is None or len(df) < 100:
                logging.warning("⚠️ Insufficient market data")
                return

            # Calculate indicators
            indicators = calculate_all_indicators(df)

            # Generate chart
            chart_path = 'chart_latest.png'
            chart_file = self.generate_chart(df, chart_path)

            if not chart_file:
                logging.error("❌ Failed to generate chart")
                return

            # Analyze with AI
            analysis_result = self.analyze_chart_with_ai(chart_file, indicators)

            if analysis_result:
                self.latest_analysis = analysis_result

                # Store in database
                analysis_data = {
                    'symbol': self.symbol,
                    'timeframe': '15m',
                    'ai_recommendation': analysis_result['recommendation'],
                    'confidence': 0.5,  # Placeholder
                    'key_observations': '\n'.join(analysis_result['key_observations']),
                    'risk_factors': '\n'.join(analysis_result['risk_factors']),
                    'analysis_text': analysis_result['analysis_text'],
                    'chart_image_path': chart_path
                }
                self.db.insert_chart_analysis(analysis_data)

                logging.info("✅ Analysis cycle completed successfully")

        except Exception as e:
            logging.error(f"❌ Error in analysis cycle: {e}")

    def run(self):
        """Main bot loop"""
        logging.info("🚀 Starting Chart Analysis Bot main loop...")
        logging.info(f"⚙️ Analysis interval: {self.analysis_interval}s (15 minutes)")

        while True:
            try:
                self.run_analysis()
                logging.info(f"⏰ Sleeping for {self.analysis_interval} seconds...\n")
                time.sleep(self.analysis_interval)

            except KeyboardInterrupt:
                logging.info("⏹️ Stopping bot (Keyboard Interrupt)...")
                break
            except Exception as e:
                logging.error(f"❌ Unexpected error in main loop: {e}")
                time.sleep(self.analysis_interval)

        # Cleanup
        self.db.close()
        logging.info("✅ Chart Analysis Bot stopped successfully")


if __name__ == "__main__":
    # Initialize and run bot
    bot = ChartAnalysisBot()
    bot.run()
