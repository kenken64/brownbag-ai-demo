"""
Main RL Trading Bot
Integrates all components: RL model, technical indicators, market context, and Binance trading
Implements safety-first logic with PnL-based position management
"""

import os
import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, Any, Tuple
import signal

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import TradingDatabase
from src.rl_model import QLearningAgent
from src.indicators import TechnicalIndicators, SignalGenerator
from src.market_context import MarketContextAnalyzer
from src.binance_client import BinanceFuturesClient

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class RLTradingBot:
    """
    Main RL Trading Bot with safety-first logic
    60-second check interval, PnL-based position management
    """

    def __init__(self):
        """Initialize trading bot with all components"""
        print("=" * 60)
        print("🚀 AI-DRIVEN CRYPTOCURRENCY TRADING BOT")
        print("=" * 60)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Load configuration
        self.trading_pair = os.getenv('TRADING_PAIR', 'BTCUSDT')
        self.leverage = int(os.getenv('LEVERAGE', '10'))
        self.position_percentage = float(os.getenv('POSITION_PERCENTAGE', '0.05'))
        self.check_interval = int(os.getenv('INTERVAL', '60'))
        self.min_signal_threshold = int(os.getenv('MIN_SIGNAL_THRESHOLD', '3'))
        self.testnet = os.getenv('USE_TESTNET', 'true').lower() == 'true'

        # Risk management
        self.stop_loss_pct = float(os.getenv('STOP_LOSS_PERCENTAGE', '0.02'))
        self.take_profit_pct = float(os.getenv('TAKE_PROFIT_PERCENTAGE', '0.05'))
        self.max_daily_loss_pct = float(os.getenv('MAX_DAILY_LOSS_PERCENTAGE', '0.05'))

        print(f"⚙️ Configuration:")
        print(f"   Trading Pair: {self.trading_pair}")
        print(f"   Leverage: {self.leverage}x")
        print(f"   Position Size: {self.position_percentage * 100}%")
        print(f"   Check Interval: {self.check_interval}s")
        print(f"   Signal Threshold: {self.min_signal_threshold}")
        print(f"   Stop Loss: {self.stop_loss_pct * 100}%")
        print(f"   Take Profit: {self.take_profit_pct * 100}%")
        print(f"   Mode: {'TESTNET' if self.testnet else 'LIVE'}\n")

        # Initialize components
        print("📊 Initializing components...")
        self.db = TradingDatabase()
        self.rl_agent = QLearningAgent(
            learning_rate=0.1,
            epsilon=0.1  # Low exploration for trading
        )
        self.signal_generator = SignalGenerator(min_threshold=self.min_signal_threshold)
        self.market_context = MarketContextAnalyzer(db=self.db)
        self.binance = BinanceFuturesClient(testnet=self.testnet)

        # Load RL model if exists
        model_path = "models/rl_trading_model.pkl"
        if os.path.exists(model_path):
            self.rl_agent.load_model(model_path)
            print(f"✅ Loaded RL model from {model_path}")
        else:
            print(f"ℹ️ No existing model, starting fresh")

        # Setup Binance
        print(f"\n🔧 Setting up Binance...")
        self.binance.set_leverage(self.trading_pair, self.leverage)
        self.binance.set_margin_type(self.trading_pair, "CROSSED")

        # State tracking
        self.current_position = None  # None, 'LONG', or 'SHORT'
        self.entry_price = None
        self.entry_time = None
        self.position_quantity = None
        self.trade_id = None
        self.running = True
        self.daily_start_balance = None
        self.daily_pnl = 0.0

        # Signal for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        print("\n✅ Bot initialized successfully!")
        print("=" * 60)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n\n⚠️ Received shutdown signal ({signum})")
        print("🛑 Stopping bot gracefully...")
        self.running = False

    def get_market_data(self, limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch market data from Binance

        Args:
            limit: Number of candles to fetch

        Returns:
            DataFrame with OHLCV data
        """
        try:
            klines = self.binance.get_klines(
                symbol=self.trading_pair,
                interval='1m',
                limit=limit
            )

            if not klines:
                return None

            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])

            return df

        except Exception as e:
            print(f"❌ Error fetching market data: {e}")
            return None

    def calculate_indicators(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Calculate all technical indicators

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dict with indicator values
        """
        try:
            indicators = TechnicalIndicators.calculate_all_indicators(df)
            return indicators
        except Exception as e:
            print(f"❌ Error calculating indicators: {e}")
            return None

    def generate_signal(self, indicators: Dict[str, Any]) -> Tuple[str, int]:
        """
        Generate trading signal from indicators

        Args:
            indicators: Dict with indicator values

        Returns:
            (signal_type, signal_strength): 'BUY', 'SELL', or 'HOLD' with strength
        """
        signal_type, signal_strength = self.signal_generator.generate_signal(indicators)
        return signal_type, signal_strength

    def prepare_rl_state(
        self,
        indicators: Dict[str, Any],
        market_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepare state dict for RL agent

        Args:
            indicators: Technical indicators
            market_context: Market context data

        Returns:
            State dict for RL agent
        """
        # Get position PnL
        position_pnl = 0.0
        if self.current_position and self.entry_price:
            current_price = indicators['price']
            if self.current_position == 'LONG':
                position_pnl = (current_price - self.entry_price) / self.entry_price
            elif self.current_position == 'SHORT':
                position_pnl = (self.entry_price - current_price) / self.entry_price

        # Build state
        state = {
            'signal_strength': indicators.get('signal_strength', 0),
            'rsi': indicators.get('rsi', 50),
            'macd_histogram': indicators.get('macd_histogram', 0),
            'position_pnl': position_pnl,
            'has_position': 1 if self.current_position else 0
        }

        # Add market context if available
        if market_context:
            state['fear_greed_index'] = market_context.get('fear_greed_index', 50)
            state['btc_trend'] = market_context.get('btc_trend', 'neutral')
            state['market_regime'] = market_context.get('market_regime', 'neutral')

        return state

    def execute_buy(self, price: float, signal_strength: int) -> bool:
        """
        Execute BUY order (open LONG position)

        Args:
            price: Current price
            signal_strength: Signal strength

        Returns:
            True if successful
        """
        try:
            print(f"\n💰 EXECUTING BUY ORDER")
            print(f"   Signal Strength: {signal_strength}")
            print(f"   Price: ${price:.4f}")

            # Calculate quantity
            result = self.binance.calculate_quantity(
                symbol=self.trading_pair,
                side='BUY',
                percentage=self.position_percentage,
                leverage=self.leverage
            )

            if not result:
                print("❌ Failed to calculate quantity")
                return False

            quantity, notional = result

            # Place order
            order = self.binance.place_market_order(
                symbol=self.trading_pair,
                side='BUY',
                quantity=quantity
            )

            if not order:
                print("❌ Order failed")
                return False

            # Update state
            self.current_position = 'LONG'
            self.entry_price = price
            self.entry_time = datetime.now()
            self.position_quantity = quantity

            # Set stop loss and take profit
            sl_price = price * (1 - self.stop_loss_pct)
            tp_price = price * (1 + self.take_profit_pct)
            self.binance.set_stop_loss_take_profit(
                symbol=self.trading_pair,
                stop_loss_price=sl_price,
                take_profit_price=tp_price
            )

            # Log to database
            self.trade_id = self.db.insert_trade({
                'trading_pair': self.trading_pair,
                'side': 'BUY',
                'entry_price': price,
                'quantity': quantity,
                'leverage': self.leverage,
                'position_mode': 'one-way',
                'stop_loss': sl_price,
                'take_profit': tp_price
            })

            print(f"✅ LONG position opened")
            print(f"   Quantity: {quantity}")
            print(f"   Entry: ${price:.4f}")
            print(f"   Stop Loss: ${sl_price:.4f}")
            print(f"   Take Profit: ${tp_price:.4f}")

            return True

        except Exception as e:
            print(f"❌ Buy execution error: {e}")
            return False

    def execute_sell(self, price: float, reason: str = "Signal") -> bool:
        """
        Execute SELL order (close LONG position)

        Args:
            price: Current price
            reason: Reason for selling

        Returns:
            True if successful
        """
        try:
            print(f"\n💸 EXECUTING SELL ORDER ({reason})")
            print(f"   Price: ${price:.4f}")

            # Close position
            order = self.binance.close_position(symbol=self.trading_pair)

            if not order:
                print("❌ Close position failed")
                return False

            # Calculate PnL
            pnl = 0.0
            if self.entry_price and self.position_quantity:
                if self.current_position == 'LONG':
                    pnl = (price - self.entry_price) * self.position_quantity
                elif self.current_position == 'SHORT':
                    pnl = (self.entry_price - price) * self.position_quantity

                pnl_pct = (pnl / (self.entry_price * self.position_quantity)) * 100

            # Update database
            if self.trade_id:
                self.db.close_trade(
                    trade_id=self.trade_id,
                    exit_price=price,
                    pnl=pnl
                )

            # Update daily PnL
            self.daily_pnl += pnl

            # Reset state
            self.current_position = None
            self.entry_price = None
            self.entry_time = None
            self.position_quantity = None
            self.trade_id = None

            pnl_emoji = "🟢" if pnl > 0 else "🔴"
            print(f"✅ Position closed")
            print(f"{pnl_emoji} PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
            print(f"📊 Daily PnL: ${self.daily_pnl:.2f}")

            return True

        except Exception as e:
            print(f"❌ Sell execution error: {e}")
            return False

    def check_position_management(self, current_price: float) -> bool:
        """
        Check if position should be closed based on PnL and time

        Args:
            current_price: Current market price

        Returns:
            True if position was closed
        """
        if not self.current_position or not self.entry_price:
            return False

        # Calculate PnL percentage
        if self.current_position == 'LONG':
            pnl_pct = (current_price - self.entry_price) / self.entry_price
        else:
            pnl_pct = (self.entry_price - current_price) / self.entry_price

        # Safety-first logic: Cut losses early, let winners run
        # If PnL is negative and getting worse, close immediately
        if pnl_pct < -self.stop_loss_pct * 0.8:  # 80% of stop loss
            print(f"\n⚠️ PnL at {pnl_pct * 100:.2f}% - cutting loss early")
            return self.execute_sell(current_price, reason="Stop Loss")

        # Take profit if target reached
        if pnl_pct > self.take_profit_pct:
            print(f"\n🎯 Take profit target reached: {pnl_pct * 100:.2f}%")
            return self.execute_sell(current_price, reason="Take Profit")

        return False

    def check_daily_loss_limit(self) -> bool:
        """
        Check if daily loss limit has been reached

        Returns:
            True if should stop trading
        """
        if not self.daily_start_balance:
            return False

        loss_pct = abs(self.daily_pnl) / self.daily_start_balance

        if self.daily_pnl < 0 and loss_pct >= self.max_daily_loss_pct:
            print(f"\n🛑 DAILY LOSS LIMIT REACHED: ${self.daily_pnl:.2f} ({loss_pct * 100:.2f}%)")
            print("⏸️ Stopping trading for today")
            return True

        return False

    def run_trading_cycle(self):
        """Execute one trading cycle (check signals, make decisions)"""
        try:
            print(f"\n{'=' * 60}")
            print(f"🔄 Trading Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'=' * 60}")

            # Check daily loss limit
            if self.check_daily_loss_limit():
                return

            # 1. Get market context (cached for 5 minutes)
            market_context = self.market_context.get_market_context(use_cache=True)
            if market_context:
                self.market_context.save_to_database(market_context)

            # 2. Get market data
            print("📈 Fetching market data...")
            df = self.get_market_data(limit=100)
            if df is None or len(df) < 50:
                print("⚠️ Insufficient market data")
                return

            current_price = float(df['close'].iloc[-1])
            print(f"💲 Current Price: ${current_price:.4f}")

            # 3. Check position management first (safety-first)
            if self.check_position_management(current_price):
                return  # Position was closed, skip rest of cycle

            # 4. Calculate indicators
            print("📊 Calculating indicators...")
            indicators = self.calculate_indicators(df)
            if not indicators:
                return

            indicators['price'] = current_price

            # 5. Generate signal
            signal_type, signal_strength = self.generate_signal(indicators)
            print(f"🔍 Technical Signal: {signal_type} (Strength: {signal_strength})")

            # 6. Prepare RL state
            rl_state = self.prepare_rl_state(indicators, market_context)

            # 7. Get RL action and confidence
            rl_action, confidence = self.rl_agent.get_action_confidence(rl_state)
            rl_action_name = self.rl_agent.ACTION_NAMES[rl_action]
            print(f"🧠 RL Recommendation: {rl_action_name} (Confidence: {confidence:.2f})")

            # 8. Make trading decision (combine signals with safety checks)
            self._make_trading_decision(
                signal_type=signal_type,
                signal_strength=signal_strength,
                rl_action=rl_action,
                rl_action_name=rl_action_name,
                confidence=confidence,
                current_price=current_price,
                indicators=indicators
            )

            # 9. Save signal to database
            signal_data = {
                'trading_pair': self.trading_pair,
                'signal_type': signal_type,
                'signal_strength': signal_strength,
                'price': current_price,
                **{k: v for k, v in indicators.items() if k != 'price'}
            }
            self.db.insert_signal(signal_data)

            print(f"{'=' * 60}\n")

        except Exception as e:
            print(f"❌ Error in trading cycle: {e}")

    def _make_trading_decision(
        self,
        signal_type: str,
        signal_strength: int,
        rl_action: int,
        rl_action_name: str,
        confidence: float,
        current_price: float,
        indicators: Dict[str, Any]
    ):
        """
        Make final trading decision combining technical signals and RL

        Safety-first logic:
        - Only trade if RL is confident (>0.3)
        - Require alignment between technical signal and RL
        - Cut losses early on negative PnL
        - Let winners run on positive PnL
        """

        # Safety check: Don't trade if RL confidence is too low
        if confidence < 0.3:
            print("⚠️ RL confidence too low - HOLD")
            return

        # Case 1: No position - consider opening
        if not self.current_position:
            # BUY signal: Strong bullish + RL recommends BUY
            if (signal_strength >= self.min_signal_threshold and
                signal_type == 'BUY' and
                rl_action_name == 'BUY'):

                print("✅ Strong BUY signal + RL confirmation")
                self.execute_buy(current_price, signal_strength)

            # No action for other cases when no position
            else:
                print(f"⏸️ Waiting for strong signal (Current: {signal_type} {signal_strength})")

        # Case 2: Have LONG position - consider closing
        elif self.current_position == 'LONG':
            # Calculate current PnL
            pnl_pct = (current_price - self.entry_price) / self.entry_price

            # Safety-first: Cut losses on negative PnL + HOLD signal
            if pnl_pct < 0 and signal_type == 'HOLD':
                print(f"⚠️ Negative PnL ({pnl_pct * 100:.2f}%) + HOLD signal - closing to prevent further loss")
                self.execute_sell(current_price, reason="Cut Loss")

            # Let winners run: Keep on positive PnL + HOLD signal
            elif pnl_pct > 0 and signal_type == 'HOLD':
                print(f"🟢 Positive PnL ({pnl_pct * 100:.2f}%) - letting winner run")

            # Strong SELL signal: Close position
            elif signal_strength <= -self.min_signal_threshold and signal_type == 'SELL':
                print("🔴 Strong SELL signal - closing position")
                self.execute_sell(current_price, reason="SELL Signal")

            # RL suggests exit
            elif rl_action_name == 'SELL' and confidence > 0.5:
                print("🧠 RL strongly recommends exit")
                self.execute_sell(current_price, reason="RL Exit")

            else:
                print(f"📊 Holding position (PnL: {pnl_pct * 100:+.2f}%)")

    def run(self):
        """Main bot loop"""
        print(f"\n{'=' * 60}")
        print("🤖 BOT IS NOW RUNNING")
        print(f"{'=' * 60}\n")
        print(f"⏱️ Check interval: {self.check_interval} seconds")
        print(f"🛑 Press Ctrl+C to stop gracefully\n")

        # Get initial balance
        balance = self.binance.get_account_balance()
        self.daily_start_balance = balance.get('available_balance', 0)

        cycle_count = 0

        while self.running:
            try:
                cycle_count += 1
                print(f"🔄 Cycle #{cycle_count}")

                self.run_trading_cycle()

                # Save RL model periodically (every 10 cycles)
                if cycle_count % 10 == 0:
                    model_path = "models/rl_trading_model.pkl"
                    os.makedirs("models", exist_ok=True)
                    self.rl_agent.save_model(model_path)
                    print(f"💾 RL model saved ({cycle_count} cycles)")

                # Wait for next cycle
                if self.running:
                    print(f"⏳ Sleeping for {self.check_interval} seconds...\n")
                    time.sleep(self.check_interval)

            except KeyboardInterrupt:
                print("\n\n⚠️ Keyboard interrupt received")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("⏳ Retrying in 60 seconds...\n")
                time.sleep(60)

        # Cleanup
        print(f"\n{'=' * 60}")
        print("🛑 BOT SHUTDOWN")
        print(f"{'=' * 60}")
        print(f"⏰ Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Total cycles: {cycle_count}")
        print(f"💰 Daily PnL: ${self.daily_pnl:.2f}")

        # Close any open positions
        if self.current_position:
            print("\n⚠️ Closing open position...")
            positions = self.binance.get_open_positions(symbol=self.trading_pair)
            if positions:
                self.binance.close_position(symbol=self.trading_pair)

        print("\n✅ Shutdown complete")
        self.db.close_connection()


def main():
    """Entry point for trading bot"""
    try:
        bot = RLTradingBot()
        bot.run()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("🛑 Bot terminated")


if __name__ == "__main__":
    main()
