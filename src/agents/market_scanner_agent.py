#!/usr/bin/env python3
"""
Market Scanner Agent - Spike Detection
Continuously scans markets for price/volume spikes and anomalies
"""

import os
import sys
import yaml
from datetime import datetime
from crewai import Agent, Task

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.binance_tools import (
    get_current_price,
    calculate_price_change,
    detect_volume_spike,
    get_market_volatility
)
from tools.circuit_breaker_tools import check_circuit_breaker_status


class MarketScanner:
    """
    Market Scanner - Detects price and volume spikes in real-time
    """

    def __init__(self, config_path: str = "config/crewai_config.yaml"):
        """Initialize Market Scanner with configuration"""
        self.config = self._load_config(config_path)
        self.agent = self._create_agent()

        print("📡 Market Scanner Agent initialized")
        print(f"   Monitoring pairs: {len(self.config.get('monitored_pairs', ['BTCUSDT']))} pairs")
        print(f"   Price spike threshold: {self.config.get('price_spike_threshold', 5.0)}%")
        print(f"   Volume spike multiplier: {self.config.get('volume_spike_multiplier', 3.0)}x")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                full_config = yaml.safe_load(f)
                return full_config.get('market_scanner', {})
        else:
            # Default configuration
            return {
                'monitored_pairs': ['BTCUSDT', 'ETHUSDT'],
                'price_spike_threshold': 5.0,  # 5% in 5 minutes
                'volume_spike_multiplier': 3.0,  # 3x average volume
                'check_circuit_breaker': True,
                'timeframes': [1, 5, 15],  # minutes
                'confidence_threshold': 0.7
            }

    def _create_agent(self) -> Agent:
        """Create the Market Scanner agent"""
        return Agent(
            role="Binance Market Surveillance Specialist",
            goal="""Detect anomalous price movements and volume spikes across monitored trading pairs.
            Identify profitable spike opportunities while filtering out false signals.
            Ensure circuit breaker is safe before processing spikes.""",
            backstory="""You are a market surveillance expert specializing in detecting
            sudden price movements on Binance. You monitor multiple timeframes and use
            both price action and volume analysis to identify genuine trading opportunities.

            You look for:
            - Rapid price increases (pumps) or decreases (dumps)
            - Abnormal volume spikes (3x+ average volume)
            - High volatility periods
            - Spot-futures price divergence

            You filter out:
            - Low liquidity spikes (likely manipulation)
            - Spikes during circuit breaker activation
            - False breakouts with low volume
            - Correlated movements (entire market moving)

            You are analytical, data-driven, and provide high-confidence alerts only.""",
            tools=[
                get_current_price,
                calculate_price_change,
                detect_volume_spike,
                get_market_volatility,
                check_circuit_breaker_status
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=10
        )

    def create_spike_detection_task(self, symbol: str) -> Task:
        """
        Create a spike detection task for a specific trading pair

        Args:
            symbol: Trading pair (e.g., "BTCUSDT")

        Returns:
            Task for spike detection
        """
        return Task(
            description=f"""DETECT PRICE/VOLUME SPIKES FOR {symbol}:

1. CHECK CIRCUIT BREAKER STATUS:
   - Use check_circuit_breaker_status tool
   - If NOT safe → STOP analysis and return {{\"spike_detected\": false, \"reason\": \"Circuit breaker active\"}}

2. ANALYZE PRICE MOVEMENT (Multiple Timeframes):
   - Use calculate_price_change for {symbol}:
     * 1 minute timeframe
     * 5 minute timeframe
     * 15 minute timeframe
   - Identify if price change exceeds {self.config.get('price_spike_threshold', 5.0)}%

3. ANALYZE VOLUME:
   - Use detect_volume_spike for {symbol}
   - Check if volume spike detected (>{self.config.get('volume_spike_multiplier', 3.0)}x)

4. ANALYZE VOLATILITY:
   - Use get_market_volatility for {symbol}
   - Assess volatility level (EXTREME, HIGH, MODERATE, LOW)

5. DETERMINE SPIKE CONFIDENCE:
   - High confidence: Price spike + Volume spike + High volatility
   - Medium confidence: Price spike + Volume spike OR High volatility
   - Low confidence: Only one indicator triggered

6. CLASSIFY SPIKE TYPE:
   - PUMP: Rapid price increase
   - DUMP: Rapid price decrease
   - VOLUME_EXPLOSION: Volume spike without significant price change
   - FALSE_SIGNAL: Inconclusive or low confidence

7. GENERATE ALERT:
   If confidence >= {self.config.get('confidence_threshold', 0.7)}:
   - Report spike with full details
   - Include timeframe, magnitude, confidence
   - Recommend action (TRADE, MONITOR, IGNORE)

RETURN: JSON with spike detection results""",
            agent=self.agent,
            expected_output="""JSON report with:
- spike_detected: true/false
- spike_type: PUMP/DUMP/VOLUME_EXPLOSION/FALSE_SIGNAL
- confidence: 0.0-1.0
- timeframe: Primary timeframe detected
- price_change_percent: Percentage change
- volume_ratio: Current volume / Average volume
- volatility_level: EXTREME/HIGH/MODERATE/LOW
- recommendation: TRADE/MONITOR/IGNORE
- reasoning: Detailed explanation"""
        )

    def scan_symbol(self, symbol: str) -> dict:
        """
        Scan a single symbol for spikes

        Args:
            symbol: Trading pair (e.g., "BTCUSDT")

        Returns:
            dict: Spike detection results
        """
        from crewai import Crew, Process

        task = self.create_spike_detection_task(symbol)

        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
            memory=False
        )

        try:
            result = crew.kickoff()
            return {
                'success': True,
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'result': str(result)
            }
        except Exception as e:
            return {
                'success': False,
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    def scan_all_pairs(self) -> list:
        """
        Scan all monitored pairs for spikes

        Returns:
            list: Results for all pairs
        """
        results = []
        monitored_pairs = self.config.get('monitored_pairs', ['BTCUSDT'])

        print(f"\n🔍 Scanning {len(monitored_pairs)} pairs for spikes...")

        for symbol in monitored_pairs:
            print(f"\n{'='*70}")
            print(f"📊 Scanning {symbol}...")
            print(f"{'='*70}")

            result = self.scan_symbol(symbol)
            results.append(result)

            if result['success']:
                print(f"✅ {symbol} scan complete")
            else:
                print(f"❌ {symbol} scan failed: {result.get('error')}")

        return results


def main():
    """Main entry point for testing"""
    print("\n📡 Market Scanner Agent - Testing Mode\n")

    # Initialize scanner
    scanner = MarketScanner()

    # Scan a single symbol
    print("\n🔍 Scanning BTCUSDT for spikes...\n")
    result = scanner.scan_symbol("BTCUSDT")

    print("\n" + "=" * 70)
    if result['success']:
        print("✅ Scan completed successfully")
        print(f"\nResult:\n{result['result']}")
    else:
        print(f"❌ Scan failed: {result.get('error')}")
    print("=" * 70)

    print("\n💡 To scan all monitored pairs:")
    print("   scanner.scan_all_pairs()")


if __name__ == "__main__":
    main()
