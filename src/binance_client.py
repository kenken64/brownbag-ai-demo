"""
Binance Futures API Client
Handles all interactions with Binance Futures API including order placement, position management, and market data
"""

import os
import sys
from typing import Optional, Dict, List, Any, Tuple
from decimal import Decimal, ROUND_DOWN
import time
from datetime import datetime

# Binance API
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.enums import *

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class BinanceFuturesClient:
    """
    Wrapper for Binance Futures API with safety features
    Supports both testnet and live trading
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        testnet: bool = True
    ):
        """
        Initialize Binance Futures client

        Args:
            api_key: Binance API key (reads from env if not provided)
            api_secret: Binance API secret (reads from env if not provided)
            testnet: Use testnet (default: True for safety)
        """
        self.api_key = api_key or os.getenv('BINANCE_API_KEY')
        self.api_secret = api_secret or os.getenv('BINANCE_SECRET_KEY')
        self.testnet = testnet

        if not self.api_key or not self.api_secret:
            raise ValueError("Binance API credentials not found. Set BINANCE_API_KEY and BINANCE_SECRET_KEY in .env")

        # Initialize client
        if self.testnet:
            # Testnet URLs
            self.client = Client(
                self.api_key,
                self.api_secret,
                testnet=True
            )
            # Set testnet base URL for futures
            self.client.FUTURES_URL = 'https://testnet.binancefuture.com'
            print("🧪 Connected to Binance Futures TESTNET")
        else:
            self.client = Client(self.api_key, self.api_secret)
            print("🚀 Connected to Binance Futures LIVE")

        # Cache for symbol info
        self.symbol_info_cache = {}

    def get_account_balance(self) -> Dict[str, Any]:
        """
        Get futures account balance

        Returns:
            Dict with balance information
        """
        try:
            account = self.client.futures_account()

            # Extract key information
            total_balance = float(account['totalWalletBalance'])
            available_balance = float(account['availableBalance'])
            total_unrealized_pnl = float(account['totalUnrealizedProfit'])

            balance_info = {
                'total_balance': total_balance,
                'available_balance': available_balance,
                'unrealized_pnl': total_unrealized_pnl,
                'margin_balance': total_balance + total_unrealized_pnl,
                'timestamp': datetime.now().isoformat()
            }

            print(f"💰 Account Balance: ${total_balance:.2f} (Available: ${available_balance:.2f})")
            return balance_info

        except BinanceAPIException as e:
            print(f"❌ Error getting account balance: {e}")
            return {}

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get trading rules and precision info for a symbol

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')

        Returns:
            Dict with symbol information
        """
        # Check cache first
        if symbol in self.symbol_info_cache:
            return self.symbol_info_cache[symbol]

        try:
            exchange_info = self.client.futures_exchange_info()

            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    # Extract important filters
                    filters = {f['filterType']: f for f in s['filters']}

                    symbol_info = {
                        'symbol': symbol,
                        'status': s['status'],
                        'base_asset': s['baseAsset'],
                        'quote_asset': s['quoteAsset'],
                        'price_precision': s['pricePrecision'],
                        'quantity_precision': s['quantityPrecision'],
                        'min_qty': float(filters.get('LOT_SIZE', {}).get('minQty', 0)),
                        'max_qty': float(filters.get('LOT_SIZE', {}).get('maxQty', 0)),
                        'step_size': float(filters.get('LOT_SIZE', {}).get('stepSize', 0)),
                        'min_notional': float(filters.get('MIN_NOTIONAL', {}).get('notional', 0)),
                        'tick_size': float(filters.get('PRICE_FILTER', {}).get('tickSize', 0))
                    }

                    # Cache the info
                    self.symbol_info_cache[symbol] = symbol_info
                    return symbol_info

            print(f"⚠️ Symbol {symbol} not found")
            return None

        except BinanceAPIException as e:
            print(f"❌ Error getting symbol info: {e}")
            return None

    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Set leverage for a symbol

        Args:
            symbol: Trading pair
            leverage: Leverage multiplier (1-125)

        Returns:
            True if successful
        """
        try:
            result = self.client.futures_change_leverage(
                symbol=symbol,
                leverage=leverage
            )
            print(f"⚡ Leverage set to {leverage}x for {symbol}")
            return True
        except BinanceAPIException as e:
            if "No need to change leverage" in str(e):
                print(f"ℹ️ Leverage already set to {leverage}x for {symbol}")
                return True
            print(f"❌ Error setting leverage: {e}")
            return False

    def set_margin_type(self, symbol: str, margin_type: str = "CROSSED") -> bool:
        """
        Set margin type (CROSSED or ISOLATED)

        Args:
            symbol: Trading pair
            margin_type: "CROSSED" or "ISOLATED"

        Returns:
            True if successful
        """
        try:
            result = self.client.futures_change_margin_type(
                symbol=symbol,
                marginType=margin_type
            )
            print(f"📊 Margin type set to {margin_type} for {symbol}")
            return True
        except BinanceAPIException as e:
            if "No need to change margin type" in str(e):
                print(f"ℹ️ Margin type already set to {margin_type} for {symbol}")
                return True
            print(f"❌ Error setting margin type: {e}")
            return False

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price for a symbol

        Args:
            symbol: Trading pair

        Returns:
            Current price as float
        """
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            return price
        except BinanceAPIException as e:
            print(f"❌ Error getting price: {e}")
            return None

    def get_klines(
        self,
        symbol: str,
        interval: str = '1m',
        limit: int = 100
    ) -> Optional[List[List]]:
        """
        Get historical klines/candlestick data

        Args:
            symbol: Trading pair
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of klines to retrieve

        Returns:
            List of klines
        """
        try:
            klines = self.client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            return klines
        except BinanceAPIException as e:
            print(f"❌ Error getting klines: {e}")
            return None

    def round_quantity(self, quantity: float, step_size: float) -> float:
        """
        Round quantity to valid step size

        Args:
            quantity: Original quantity
            step_size: Minimum quantity step

        Returns:
            Rounded quantity
        """
        precision = len(str(step_size).split('.')[-1]) if '.' in str(step_size) else 0
        return float(Decimal(str(quantity)).quantize(Decimal(str(step_size)), rounding=ROUND_DOWN))

    def round_price(self, price: float, tick_size: float) -> float:
        """
        Round price to valid tick size

        Args:
            price: Original price
            tick_size: Minimum price step

        Returns:
            Rounded price
        """
        precision = len(str(tick_size).split('.')[-1]) if '.' in str(tick_size) else 0
        return float(Decimal(str(price)).quantize(Decimal(str(tick_size)), rounding=ROUND_DOWN))

    def calculate_quantity(
        self,
        symbol: str,
        side: str,
        percentage: float,
        leverage: int
    ) -> Optional[Tuple[float, float]]:
        """
        Calculate order quantity based on available balance and leverage

        Args:
            symbol: Trading pair
            side: "BUY" or "SELL"
            percentage: Percentage of balance to use (0.0 - 1.0)
            leverage: Leverage multiplier

        Returns:
            Tuple of (quantity, notional_value) or None if error
        """
        try:
            # Get account balance
            balance_info = self.get_account_balance()
            if not balance_info:
                return None

            available_balance = balance_info['available_balance']

            # Get current price
            current_price = self.get_current_price(symbol)
            if not current_price:
                return None

            # Get symbol info for precision
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return None

            # Calculate notional value (balance * percentage * leverage)
            notional_value = available_balance * percentage * leverage

            # Calculate quantity
            quantity = notional_value / current_price

            # Round to valid step size
            quantity = self.round_quantity(quantity, symbol_info['step_size'])

            # Validate minimum notional
            if notional_value < symbol_info['min_notional']:
                print(f"⚠️ Order value ${notional_value:.2f} below minimum ${symbol_info['min_notional']:.2f}")
                return None

            # Validate quantity range
            if quantity < symbol_info['min_qty'] or quantity > symbol_info['max_qty']:
                print(f"⚠️ Quantity {quantity} outside valid range [{symbol_info['min_qty']}, {symbol_info['max_qty']}]")
                return None

            print(f"📊 Calculated quantity: {quantity} (Notional: ${notional_value:.2f}, Price: ${current_price:.2f})")
            return (quantity, notional_value)

        except Exception as e:
            print(f"❌ Error calculating quantity: {e}")
            return None

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> Optional[Dict[str, Any]]:
        """
        Place a market order

        Args:
            symbol: Trading pair
            side: "BUY" or "SELL"
            quantity: Order quantity

        Returns:
            Order result dict or None if error
        """
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )

            print(f"✅ Market order placed: {side} {quantity} {symbol}")
            print(f"   Order ID: {order['orderId']}")
            print(f"   Status: {order['status']}")

            return order

        except BinanceOrderException as e:
            print(f"❌ Order error: {e}")
            return None
        except BinanceAPIException as e:
            print(f"❌ API error: {e}")
            return None

    def get_open_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open positions

        Args:
            symbol: Optional symbol filter

        Returns:
            List of position dicts
        """
        try:
            positions = self.client.futures_position_information(symbol=symbol)

            # Filter to only positions with non-zero amount
            open_positions = [
                {
                    'symbol': p['symbol'],
                    'position_side': p['positionSide'],
                    'position_amt': float(p['positionAmt']),
                    'entry_price': float(p['entryPrice']),
                    'mark_price': float(p['markPrice']),
                    'unrealized_pnl': float(p['unRealizedProfit']),
                    'leverage': int(p['leverage']),
                    'margin_type': p['marginType']
                }
                for p in positions
                if float(p['positionAmt']) != 0
            ]

            if open_positions:
                print(f"📍 Open positions: {len(open_positions)}")
                for pos in open_positions:
                    pnl_emoji = "🟢" if pos['unrealized_pnl'] > 0 else "🔴"
                    print(f"   {pnl_emoji} {pos['symbol']}: {pos['position_amt']} @ ${pos['entry_price']:.4f} (PnL: ${pos['unrealized_pnl']:.2f})")

            return open_positions

        except BinanceAPIException as e:
            print(f"❌ Error getting positions: {e}")
            return []

    def close_position(
        self,
        symbol: str,
        position_side: str = "BOTH"
    ) -> Optional[Dict[str, Any]]:
        """
        Close an open position

        Args:
            symbol: Trading pair
            position_side: "BOTH", "LONG", or "SHORT"

        Returns:
            Order result or None
        """
        try:
            # Get position info
            positions = self.get_open_positions(symbol=symbol)
            if not positions:
                print(f"ℹ️ No open position for {symbol}")
                return None

            position = positions[0]
            position_amt = abs(position['position_amt'])

            # Determine closing side (opposite of position)
            if position['position_amt'] > 0:
                close_side = SIDE_SELL
            else:
                close_side = SIDE_BUY

            # Place closing order
            order = self.place_market_order(
                symbol=symbol,
                side=close_side,
                quantity=position_amt
            )

            if order:
                print(f"✅ Position closed: {symbol} (PnL: ${position['unrealized_pnl']:.2f})")

            return order

        except Exception as e:
            print(f"❌ Error closing position: {e}")
            return None

    def set_stop_loss_take_profit(
        self,
        symbol: str,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Set stop loss and take profit for a position

        Args:
            symbol: Trading pair
            stop_loss_price: Stop loss price
            take_profit_price: Take profit price

        Returns:
            Dict with order results
        """
        results = {}

        try:
            # Get current position
            positions = self.get_open_positions(symbol=symbol)
            if not positions:
                print(f"ℹ️ No open position for {symbol}")
                return results

            position = positions[0]
            position_amt = abs(position['position_amt'])

            # Determine order side (opposite of position)
            if position['position_amt'] > 0:
                order_side = SIDE_SELL
            else:
                order_side = SIDE_BUY

            # Get symbol info for price rounding
            symbol_info = self.get_symbol_info(symbol)

            # Place stop loss order
            if stop_loss_price:
                sl_price = self.round_price(stop_loss_price, symbol_info['tick_size'])
                try:
                    sl_order = self.client.futures_create_order(
                        symbol=symbol,
                        side=order_side,
                        type=FUTURE_ORDER_TYPE_STOP_MARKET,
                        stopPrice=sl_price,
                        closePosition=True
                    )
                    results['stop_loss'] = sl_order
                    print(f"🛑 Stop loss set at ${sl_price:.4f}")
                except BinanceAPIException as e:
                    print(f"⚠️ Stop loss error: {e}")

            # Place take profit order
            if take_profit_price:
                tp_price = self.round_price(take_profit_price, symbol_info['tick_size'])
                try:
                    tp_order = self.client.futures_create_order(
                        symbol=symbol,
                        side=order_side,
                        type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
                        stopPrice=tp_price,
                        closePosition=True
                    )
                    results['take_profit'] = tp_order
                    print(f"🎯 Take profit set at ${tp_price:.4f}")
                except BinanceAPIException as e:
                    print(f"⚠️ Take profit error: {e}")

            return results

        except Exception as e:
            print(f"❌ Error setting SL/TP: {e}")
            return results


if __name__ == "__main__":
    # Test Binance Futures client
    print("Testing Binance Futures Client...\n")

    # Initialize client (testnet by default)
    testnet = os.getenv('USE_TESTNET', 'true').lower() == 'true'

    try:
        client = BinanceFuturesClient(testnet=testnet)

        # Test 1: Get account balance
        print("\n1. Testing account balance...")
        balance = client.get_account_balance()

        # Test 2: Get symbol info
        print("\n2. Testing symbol info...")
        symbol = os.getenv('TRADING_PAIR', 'BTCUSDT')
        symbol_info = client.get_symbol_info(symbol)
        if symbol_info:
            print(f"   Symbol: {symbol_info['symbol']}")
            print(f"   Price Precision: {symbol_info['price_precision']}")
            print(f"   Quantity Precision: {symbol_info['quantity_precision']}")
            print(f"   Min Quantity: {symbol_info['min_qty']}")
            print(f"   Min Notional: ${symbol_info['min_notional']}")

        # Test 3: Get current price
        print(f"\n3. Testing current price for {symbol}...")
        price = client.get_current_price(symbol)
        if price:
            print(f"   Current Price: ${price:.2f}")

        # Test 4: Set leverage
        print(f"\n4. Testing leverage setting...")
        leverage = int(os.getenv('LEVERAGE', '10'))
        client.set_leverage(symbol, leverage)

        # Test 5: Set margin type
        print(f"\n5. Testing margin type...")
        client.set_margin_type(symbol, "CROSSED")

        # Test 6: Get open positions
        print(f"\n6. Testing open positions...")
        positions = client.get_open_positions()
        if not positions:
            print("   No open positions")

        print("\n✅ Binance Futures Client test completed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
