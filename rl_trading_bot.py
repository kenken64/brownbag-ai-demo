"""
RL-Enhanced Trading Bot
Main trading bot with reinforcement learning and technical analysis
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import pandas as pd
import numpy as np

# Import local modules
from database import TradingDatabase
from technical_indicators import calculate_all_indicators, generate_signal_from_indicators, get_indicator_summary
from q_learning_model import QLearningTrader

# Try to import Binance client
try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    print("⚠️ python-binance not installed. Install with: pip install python-binance")

# Load environment variables
load_dotenv()

# Configure logging with emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/rl_bot_main.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Separate error log
error_logger = logging.getLogger('error_logger')
error_handler = logging.FileHandler('logs/rl_bot_error.log')
error_handler.setLevel(logging.ERROR)
error_logger.addHandler(error_handler)


class RLTradingBot:
    """Reinforcement Learning Enhanced Trading Bot"""

    def __init__(self):
        """Initialize the trading bot"""
        logging.info("🚀 Initializing RL Trading Bot...")

        # Load configuration from environment
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_SECRET_KEY')
        self.symbol = os.getenv('TRADING_SYMBOL', 'SUIUSDC')
        self.leverage = int(os.getenv('LEVERAGE', 50))
        self.position_percentage = float(os.getenv('POSITION_PERCENTAGE', 5)) / 100
        self.stop_loss_pct = float(os.getenv('STOP_LOSS_PERCENTAGE', 2)) / 100
        self.take_profit_pct = float(os.getenv('TAKE_PROFIT_PERCENTAGE', 3)) / 100
        self.interval = int(os.getenv('INTERVAL', 60))
        self.min_signal_threshold = int(os.getenv('MINIMUM_SIGNAL_THRESHOLD', 3))
        self.use_testnet = os.getenv('USE_TESTNET', 'true').lower() == 'true'

        # Initialize database
        db_path = os.getenv('DATABASE_PATH', 'trading_bot.db')
        self.db = TradingDatabase(db_path)
        self.db.connect()

        # Initialize Q-Learning model
        self.rl_model = QLearningTrader(
            learning_rate=0.1,
            discount_factor=0.95,
            epsilon=0.1,
            epsilon_min=0.01,
            epsilon_decay=0.995
        )

        # Load existing model if available
        if os.path.exists('rl_trading_model.pkl'):
            self.rl_model.load_model('rl_trading_model.pkl')
        else:
            logging.info("🆕 No existing RL model found. Starting with new model.")

        # Initialize Binance client
        self.client = None
        if BINANCE_AVAILABLE and self.api_key and self.api_secret:
            try:
                self.client = Client(self.api_key, self.api_secret, testnet=self.use_testnet)
                self.setup_futures_account()
                logging.info(f"✅ Connected to Binance Futures ({'TESTNET' if self.use_testnet else 'LIVE'})")
            except Exception as e:
                logging.error(f"❌ Failed to connect to Binance: {e}")
                error_logger.error(f"Binance connection error: {e}", exc_info=True)
        else:
            logging.warning("⚠️ Binance credentials not found. Running in simulation mode.")

        # Trading state
        self.current_position = None
        self.last_signal_state = None
        self.trading_enabled = True
        self.last_update_time = datetime.now()

        logging.info("✅ RL Trading Bot initialized successfully")

    def setup_futures_account(self):
        """Setup Binance Futures account settings"""
        try:
            # Set leverage
            self.client.futures_change_leverage(symbol=self.symbol, leverage=self.leverage)
            logging.info(f"✅ Leverage set to {self.leverage}x")

            # Set margin type to CROSS
            try:
                self.client.futures_change_margin_type(symbol=self.symbol, marginType='CROSS')
                logging.info("✅ Margin type set to CROSS")
            except BinanceAPIException as e:
                if "No need to change margin type" in str(e):
                    logging.info("✅ Margin type already set to CROSS")
                else:
                    raise

        except Exception as e:
            logging.error(f"❌ Error setting up futures account: {e}")
            error_logger.error(f"Futures setup error: {e}", exc_info=True)

    def get_market_data(self, limit: int = 100) -> Optional[pd.DataFrame]:
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
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            return df

        except Exception as e:
            logging.error(f"❌ Error fetching market data: {e}")
            error_logger.error(f"Market data error: {e}", exc_info=True)
            return None

    def get_market_context(self) -> Dict[str, Any]:
        """
        Fetch broader market context (BTC, ETH, Fear & Greed)

        Returns:
            Dictionary with market context data
        """
        context = {
            'btc_price': 0,
            'btc_change_24h': 0,
            'eth_price': 0,
            'eth_change_24h': 0,
            'btc_dominance': 0,
            'fear_greed_index': 50,
            'fear_greed_label': 'neutral',
            'market_trend': 'neutral',
            'btc_trend_strength': 'sideways',
            'market_regime': 'neutral',
            'volatility_level': 'medium'
        }

        try:
            if not self.client:
                return context

            # Get BTC price and 24h change
            btc_ticker = self.client.futures_ticker(symbol='BTCUSDT')
            context['btc_price'] = float(btc_ticker['lastPrice'])
            context['btc_change_24h'] = float(btc_ticker['priceChangePercent'])

            # Get ETH price and 24h change
            eth_ticker = self.client.futures_ticker(symbol='ETHUSDT')
            context['eth_price'] = float(eth_ticker['lastPrice'])
            context['eth_change_24h'] = float(eth_ticker['priceChangePercent'])

            # Determine market trend
            if context['btc_change_24h'] > 2:
                context['market_trend'] = 'bullish'
                context['btc_trend_strength'] = 'up_strong'
            elif context['btc_change_24h'] > 0:
                context['market_trend'] = 'bullish'
                context['btc_trend_strength'] = 'up_weak'
            elif context['btc_change_24h'] < -2:
                context['market_trend'] = 'bearish'
                context['btc_trend_strength'] = 'down_strong'
            elif context['btc_change_24h'] < 0:
                context['market_trend'] = 'bearish'
                context['btc_trend_strength'] = 'down_weak'
            else:
                context['market_trend'] = 'neutral'
                context['btc_trend_strength'] = 'sideways'

            # Market regime based on trend
            if abs(context['btc_change_24h']) > 3:
                context['market_regime'] = 'high_volatility'
                context['volatility_level'] = 'high'
            elif abs(context['btc_change_24h']) > 1:
                context['market_regime'] = 'normal'
                context['volatility_level'] = 'medium'
            else:
                context['market_regime'] = 'low_volatility'
                context['volatility_level'] = 'low'

            # Store in database
            self.db.insert_market_context(context)

        except Exception as e:
            logging.error(f"❌ Error fetching market context: {e}")
            error_logger.error(f"Market context error: {e}", exc_info=True)

        return context

    def get_current_position(self) -> Optional[Dict[str, Any]]:
        """
        Get current open position

        Returns:
            Position dict or None
        """
        try:
            if not self.client:
                return None

            positions = self.client.futures_position_information(symbol=self.symbol)

            for position in positions:
                if float(position['positionAmt']) != 0:
                    return {
                        'side': 'LONG' if float(position['positionAmt']) > 0 else 'SHORT',
                        'quantity': abs(float(position['positionAmt'])),
                        'entry_price': float(position['entryPrice']),
                        'unrealized_pnl': float(position['unRealizedProfit']),
                        'leverage': int(position['leverage'])
                    }

            return None

        except Exception as e:
            logging.error(f"❌ Error getting position: {e}")
            error_logger.error(f"Position retrieval error: {e}", exc_info=True)
            return None

    def execute_trade(self, signal: str, price: float, market_context: Dict[str, Any]) -> bool:
        """
        Execute trade based on signal

        Args:
            signal: Trading signal (BUY/SELL/HOLD)
            price: Current price
            market_context: Market context data

        Returns:
            True if trade executed successfully
        """
        if not self.trading_enabled:
            logging.info("⏸️ Trading is paused")
            return False

        if not self.client:
            logging.info("💭 Simulation mode - would execute: {signal}")
            return False

        try:
            # Get account balance
            account = self.client.futures_account()
            balance = float(account['totalWalletBalance'])

            # Calculate position size
            position_value = balance * self.position_percentage * self.leverage
            quantity = position_value / price

            # Round quantity to appropriate precision
            # This should be adjusted based on symbol requirements
            quantity = round(quantity, 2)

            if signal == 'BUY':
                logging.info(f"💲 Executing BUY order: {quantity} @ ${price:.4f}")
                order = self.client.futures_create_order(
                    symbol=self.symbol,
                    side='BUY',
                    type='MARKET',
                    quantity=quantity
                )
                logging.info(f"✅ BUY order executed: {order['orderId']}")
                return True

            elif signal == 'SELL':
                logging.info(f"💲 Executing SELL order: {quantity} @ ${price:.4f}")
                order = self.client.futures_create_order(
                    symbol=self.symbol,
                    side='SELL',
                    type='MARKET',
                    quantity=quantity
                )
                logging.info(f"✅ SELL order executed: {order['orderId']}")
                return True

        except Exception as e:
            logging.error(f"❌ Trade execution error: {e}")
            error_logger.error(f"Trade execution error: {e}", exc_info=True)
            return False

        return False

    def make_trading_decision(
        self,
        signal: str,
        signal_strength: int,
        indicators: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Make final trading decision using RL model and safety checks

        Args:
            signal: Original technical signal
            signal_strength: Signal strength
            indicators: Technical indicators
            market_context: Market context

        Returns:
            Tuple of (final_decision, reasoning)
        """
        # Prepare state for RL model
        position = self.get_current_position()
        has_position = position is not None
        position_pnl = 0

        if has_position:
            current_price = indicators['current_price']
            if position['side'] == 'LONG':
                position_pnl = (current_price - position['entry_price']) / position['entry_price']
            else:
                position_pnl = (position['entry_price'] - current_price) / position['entry_price']

        state_data = {
            'signal': signal,
            'signal_strength': signal_strength,
            'rsi': indicators['rsi'],
            'macd_histogram': indicators['macd_histogram'],
            'price': indicators['current_price'],
            'vwap': indicators['vwap'],
            'market_regime': market_context.get('market_regime', 'neutral'),
            'fear_greed_index': market_context.get('fear_greed_index', 50),
            'btc_correlation': 0.5,  # Simplified for now
            'has_position': has_position,
            'position_pnl': position_pnl
        }

        # Get RL model recommendation
        rl_action_idx, rl_action, confidence = self.rl_model.choose_action(state_data, explore=True)

        # Safety-first decision framework
        reasoning = []

        # Original signal
        reasoning.append(f"📊 Original signal: {signal} (strength: {signal_strength})")
        reasoning.append(f"🧠 RL recommendation: {rl_action} (confidence: {confidence:.2f})")

        # Safety check: insufficient confidence
        if confidence < 0.3:
            final_decision = 'HOLD'
            reasoning.append("⚠️ Insufficient confidence - choosing HOLD for safety")
            return final_decision, " | ".join(reasoning)

        # Position management logic
        if has_position:
            if position_pnl > 0:
                # Profitable position
                if signal == 'HOLD' or rl_action == 'HOLD':
                    final_decision = 'HOLD'
                    reasoning.append("✅ Keeping profitable position open")
                else:
                    final_decision = rl_action
                    reasoning.append(f"🔄 RL suggests {rl_action} on profitable position")
            else:
                # Losing position
                if signal == 'HOLD' or rl_action == 'HOLD':
                    final_decision = 'SELL' if position['side'] == 'LONG' else 'BUY'
                    reasoning.append("⚠️ Cutting losses on negative PnL position")
                else:
                    final_decision = rl_action
                    reasoning.append(f"🔄 RL suggests {rl_action} on losing position")
        else:
            # No position - follow RL recommendation if confident
            if signal_strength >= self.min_signal_threshold and confidence > 0.5:
                final_decision = rl_action
                reasoning.append(f"✅ High confidence trade: {rl_action}")
            else:
                final_decision = 'HOLD'
                reasoning.append("⚠️ Waiting for stronger signal")

        return final_decision, " | ".join(reasoning)

    def run_iteration(self):
        """Run one iteration of the trading bot"""
        try:
            logging.info("🔍 Starting trading iteration...")

            # Fetch market data
            df = self.get_market_data(limit=200)
            if df is None or len(df) < 50:
                logging.warning("⚠️ Insufficient market data")
                return

            # Calculate indicators
            indicators = calculate_all_indicators(df)
            logging.info(get_indicator_summary(indicators))

            # Generate signal
            signal, signal_strength = generate_signal_from_indicators(
                indicators,
                self.min_signal_threshold
            )

            # Get market context
            market_context = self.get_market_context()
            logging.info(f"🌐 Market Context: BTC ${market_context['btc_price']:.2f} ({market_context['btc_change_24h']:+.2f}%) | Trend: {market_context['market_trend']}")

            # Make trading decision
            final_decision, reasoning = self.make_trading_decision(
                signal,
                signal_strength,
                indicators,
                market_context
            )

            logging.info(f"🔍 Signal: {signal} ({signal_strength}) -> Final: {final_decision}")
            logging.info(f"💡 Reasoning: {reasoning}")

            # Store signal in database
            signal_data = {
                'symbol': self.symbol,
                'price': indicators['current_price'],
                'signal': signal,
                'strength': signal_strength,
                **indicators,
                'btc_price': market_context['btc_price'],
                'fear_greed_index': market_context['fear_greed_index'],
                'market_regime': market_context['market_regime']
            }
            signal_id = self.db.insert_signal(signal_data)

            # Execute trade if needed
            if final_decision in ['BUY', 'SELL']:
                success = self.execute_trade(
                    final_decision,
                    indicators['current_price'],
                    market_context
                )

                if success:
                    # Store trade in database
                    trade_data = {
                        'symbol': self.symbol,
                        'side': final_decision,
                        'entry_price': indicators['current_price'],
                        'quantity': 0,  # Will be filled after execution
                        'signal_id': signal_id,
                        'rl_action': final_decision,
                        'reasoning': reasoning
                    }
                    self.db.insert_trade(trade_data)

            # Save model periodically
            if signal_id % 100 == 0:
                self.rl_model.save_model()

            self.last_update_time = datetime.now()

        except Exception as e:
            logging.error(f"❌ Error in trading iteration: {e}")
            error_logger.error(f"Iteration error: {e}", exc_info=True)

    def run(self):
        """Main bot loop"""
        logging.info("🚀 Starting RL Trading Bot main loop...")
        logging.info(f"⚙️ Config: {self.symbol} | Leverage: {self.leverage}x | Interval: {self.interval}s | Testnet: {self.use_testnet}")

        while True:
            try:
                self.run_iteration()
                logging.info(f"⏰ Sleeping for {self.interval} seconds...\n")
                time.sleep(self.interval)

            except KeyboardInterrupt:
                logging.info("⏹️ Stopping bot (Keyboard Interrupt)...")
                break
            except Exception as e:
                logging.error(f"❌ Unexpected error in main loop: {e}")
                error_logger.error(f"Main loop error: {e}", exc_info=True)
                time.sleep(self.interval)

        # Cleanup
        self.rl_model.save_model()
        self.db.close()
        logging.info("✅ RL Trading Bot stopped successfully")


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Initialize and run bot
    bot = RLTradingBot()
    bot.run()
