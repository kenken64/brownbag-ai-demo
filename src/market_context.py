"""
Market Context Module
Tracks BTC/ETH correlation, Fear & Greed Index, and market regime for informed trading decisions
"""

import os
import sys
import requests
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import TradingDatabase

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class MarketContextAnalyzer:
    """
    Analyzes broader market conditions to provide context for trading decisions
    Tracks BTC/ETH prices, Fear & Greed Index, volatility, and market regime
    """

    def __init__(self, db: Optional[TradingDatabase] = None):
        """
        Initialize market context analyzer

        Args:
            db: TradingDatabase instance (creates new if not provided)
        """
        self.db = db or TradingDatabase()

        # API endpoints
        self.fear_greed_api = "https://api.alternative.me/fng/"
        self.coingecko_api = "https://api.coingecko.com/api/v3"

        # Cache for API calls (avoid rate limits)
        self.last_fetch_time = None
        self.cache_duration = 300  # 5 minutes
        self.cached_context = None

    def get_fear_greed_index(self) -> Optional[Dict[str, Any]]:
        """
        Fetch Crypto Fear & Greed Index from alternative.me API

        Returns:
            Dict with fear_greed_index, classification, and timestamp
        """
        try:
            response = requests.get(self.fear_greed_api, timeout=10)
            response.raise_for_status()

            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                latest = data['data'][0]

                fear_greed_value = int(latest['value'])
                fear_greed_class = latest['value_classification']

                result = {
                    'fear_greed_index': fear_greed_value,
                    'classification': fear_greed_class,  # Extreme Fear, Fear, Neutral, Greed, Extreme Greed
                    'timestamp': datetime.now().isoformat()
                }

                print(f"😰 Fear & Greed Index: {fear_greed_value} ({fear_greed_class})")
                return result

        except Exception as e:
            print(f"⚠️ Error fetching Fear & Greed Index: {e}")
            return None

    def get_btc_eth_prices(self) -> Optional[Dict[str, Any]]:
        """
        Fetch BTC and ETH prices from CoinGecko API

        Returns:
            Dict with BTC and ETH prices and 24h changes
        """
        try:
            # CoinGecko simple price endpoint (free tier)
            endpoint = f"{self.coingecko_api}/simple/price"
            params = {
                'ids': 'bitcoin,ethereum',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            }

            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'bitcoin' in data and 'ethereum' in data:
                btc_price = data['bitcoin']['usd']
                btc_change = data['bitcoin']['usd_24h_change']
                eth_price = data['ethereum']['usd']
                eth_change = data['ethereum']['usd_24h_change']

                result = {
                    'btc_price': btc_price,
                    'btc_change_24h': btc_change,
                    'eth_price': eth_price,
                    'eth_change_24h': eth_change,
                    'timestamp': datetime.now().isoformat()
                }

                print(f"₿ BTC: ${btc_price:,.2f} ({btc_change:+.2f}%)")
                print(f"Ξ ETH: ${eth_price:,.2f} ({eth_change:+.2f}%)")

                return result

        except Exception as e:
            print(f"⚠️ Error fetching BTC/ETH prices: {e}")
            return None

    def calculate_btc_dominance(self) -> Optional[float]:
        """
        Calculate Bitcoin dominance (BTC market cap / total crypto market cap)

        Returns:
            BTC dominance percentage
        """
        try:
            endpoint = f"{self.coingecko_api}/global"

            response = requests.get(endpoint, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'data' in data and 'market_cap_percentage' in data['data']:
                btc_dominance = data['data']['market_cap_percentage'].get('btc', 0)
                print(f"🔵 BTC Dominance: {btc_dominance:.2f}%")
                return btc_dominance

        except Exception as e:
            print(f"⚠️ Error fetching BTC dominance: {e}")
            return None

    def determine_market_trend(
        self,
        btc_change: float,
        eth_change: float
    ) -> str:
        """
        Determine overall market trend based on BTC/ETH movements

        Args:
            btc_change: BTC 24h change percentage
            eth_change: ETH 24h change percentage

        Returns:
            "bullish", "bearish", or "neutral"
        """
        avg_change = (btc_change + eth_change) / 2

        if avg_change > 3:
            return "bullish"
        elif avg_change < -3:
            return "bearish"
        else:
            return "neutral"

    def determine_btc_trend(self, btc_change: float) -> str:
        """
        Determine BTC-specific trend strength

        Args:
            btc_change: BTC 24h change percentage

        Returns:
            "up_strong", "up_weak", "down_weak", "down_strong", "sideways"
        """
        if btc_change > 5:
            return "up_strong"
        elif btc_change > 1:
            return "up_weak"
        elif btc_change < -5:
            return "down_strong"
        elif btc_change < -1:
            return "down_weak"
        else:
            return "sideways"

    def determine_market_regime(self, fear_greed_index: int) -> str:
        """
        Determine market regime based on Fear & Greed Index

        Args:
            fear_greed_index: Fear & Greed Index value (0-100)

        Returns:
            "risk_on" or "risk_off"
        """
        # Risk-off: Extreme Fear (0-25)
        # Risk-on: Neutral to Greed (50-100)
        if fear_greed_index < 35:
            return "risk_off"
        else:
            return "risk_on"

    def classify_volatility(self, btc_change: float, eth_change: float) -> str:
        """
        Classify market volatility level

        Args:
            btc_change: BTC 24h change percentage
            eth_change: ETH 24h change percentage

        Returns:
            "high", "medium", or "low"
        """
        max_change = max(abs(btc_change), abs(eth_change))

        if max_change > 7:
            return "high"
        elif max_change > 3:
            return "medium"
        else:
            return "low"

    def get_market_context(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get complete market context with all indicators

        Args:
            use_cache: Use cached data if available (default: True)

        Returns:
            Dict with complete market context
        """
        # Check cache
        if use_cache and self.cached_context and self.last_fetch_time:
            time_since_fetch = (datetime.now() - self.last_fetch_time).total_seconds()
            if time_since_fetch < self.cache_duration:
                print(f"📦 Using cached market context ({int(time_since_fetch)}s old)")
                return self.cached_context

        print("🌍 Fetching market context...")

        # Fetch data
        btc_eth_data = self.get_btc_eth_prices()
        fear_greed_data = self.get_fear_greed_index()
        btc_dominance = self.calculate_btc_dominance()

        if not btc_eth_data or not fear_greed_data:
            print("⚠️ Failed to fetch market context")
            return None

        # Extract values
        btc_price = btc_eth_data['btc_price']
        btc_change = btc_eth_data['btc_change_24h']
        eth_price = btc_eth_data['eth_price']
        eth_change = btc_eth_data['eth_change_24h']
        fear_greed_index = fear_greed_data['fear_greed_index']

        # Analyze market conditions
        market_trend = self.determine_market_trend(btc_change, eth_change)
        btc_trend = self.determine_btc_trend(btc_change)
        market_regime = self.determine_market_regime(fear_greed_index)
        volatility = self.classify_volatility(btc_change, eth_change)

        # Compile context
        context = {
            # Prices
            'btc_price': btc_price,
            'btc_change_24h': btc_change,
            'eth_price': eth_price,
            'eth_change_24h': eth_change,
            'btc_dominance': btc_dominance,

            # Sentiment
            'fear_greed_index': fear_greed_index,

            # Classifications
            'market_trend': market_trend,  # bullish, bearish, neutral
            'btc_trend': btc_trend,  # up_strong, down_strong, sideways, etc.
            'market_regime': market_regime,  # risk_on, risk_off
            'volatility_level': volatility,  # high, medium, low

            # Metadata
            'timestamp': datetime.now().isoformat()
        }

        # Cache the result
        self.cached_context = context
        self.last_fetch_time = datetime.now()

        # Print summary
        print(f"\n📊 Market Context Summary:")
        print(f"   Trend: {market_trend.upper()} | BTC: {btc_trend}")
        print(f"   Regime: {market_regime.upper()} | Volatility: {volatility.upper()}")
        print(f"   Fear & Greed: {fear_greed_index} | BTC Dom: {btc_dominance:.1f}%\n")

        return context

    def save_to_database(self, context: Dict[str, Any]) -> bool:
        """
        Save market context to database

        Args:
            context: Market context dict

        Returns:
            True if successful
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO market_context (
                    btc_price, btc_change_24h, eth_price, eth_change_24h,
                    btc_dominance, fear_greed_index, market_trend,
                    btc_trend, market_regime, volatility_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                context['btc_price'],
                context['btc_change_24h'],
                context['eth_price'],
                context['eth_change_24h'],
                context.get('btc_dominance'),
                context['fear_greed_index'],
                context['market_trend'],
                context['btc_trend'],
                context['market_regime'],
                context['volatility_level']
            ))

            conn.commit()
            print("✅ Market context saved to database")
            return True

        except Exception as e:
            print(f"❌ Error saving market context: {e}")
            return False

    def get_latest_from_database(self) -> Optional[Dict[str, Any]]:
        """
        Get latest market context from database

        Returns:
            Latest market context dict or None
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM market_context
                ORDER BY timestamp DESC
                LIMIT 1
            ''')

            row = cursor.fetchone()
            if row:
                return dict(row)

            return None

        except Exception as e:
            print(f"❌ Error fetching from database: {e}")
            return None


if __name__ == "__main__":
    # Test market context analyzer
    print("Testing Market Context Analyzer...\n")

    analyzer = MarketContextAnalyzer()

    # Test 1: Get market context
    print("1. Fetching market context...")
    context = analyzer.get_market_context(use_cache=False)

    if context:
        # Test 2: Save to database
        print("\n2. Saving to database...")
        analyzer.save_to_database(context)

        # Test 3: Retrieve from database
        print("\n3. Retrieving from database...")
        db_context = analyzer.get_latest_from_database()
        if db_context:
            print(f"   Retrieved: {db_context['market_trend']} market")

        # Test 4: Test cache
        print("\n4. Testing cache (should use cached data)...")
        cached_context = analyzer.get_market_context(use_cache=True)

    print("\n✅ Market Context Analyzer test completed!")
