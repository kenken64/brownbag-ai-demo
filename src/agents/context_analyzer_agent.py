#!/usr/bin/env python3
"""
Context Analyzer Agent - Market Context Analysis
Analyzes news, social sentiment, and market correlations for spike context
"""

import os
import sys
import yaml
from datetime import datetime
from crewai import Agent, Task

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.binance_tools import get_current_price, get_market_volatility
from tools.circuit_breaker_tools import check_circuit_breaker_status


class ContextAnalyzer:
    """
    Context Analyzer - Provides market context for spike analysis
    """

    def __init__(self, config_path: str = "config/crewai_config.yaml"):
        """Initialize Context Analyzer with configuration"""
        self.config = self._load_config(config_path)
        self.agent = self._create_agent()

        print("🔍 Context Analyzer Agent initialized")
        print(f"   Analysis depth: {self.config.get('analysis_depth', 'standard')}")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                full_config = yaml.safe_load(f)
                return full_config.get('context_analyzer', {})
        else:
            # Default configuration
            return {
                'analysis_depth': 'standard',
                'check_news': True,
                'check_correlations': True,
                'confidence_threshold': 0.6
            }

    def _create_agent(self) -> Agent:
        """Create the Context Analyzer agent"""
        return Agent(
            role="Market Context Analysis Specialist",
            goal="""Analyze market context to determine if a price spike is genuine or manipulated.
            Assess news sentiment, market correlations, and overall crypto market conditions.
            Provide confidence assessment for spike trading opportunities.""",
            backstory="""You are a market context expert who helps distinguish between
            genuine trading opportunities and false signals. You analyze multiple factors:

            - Recent news and announcements related to the asset
            - Overall cryptocurrency market sentiment
            - Correlation with major assets (BTC, ETH)
            - Market-wide movements vs isolated spikes
            - Volatility patterns across the market

            You help the trading bot avoid:
            - Pump-and-dump schemes
            - Low liquidity manipulation
            - False breakouts
            - Correlated market-wide moves (not spike-specific)

            You are analytical, cautious, and provide well-reasoned assessments
            based on multiple data sources.""",
            tools=[
                get_current_price,
                get_market_volatility,
                check_circuit_breaker_status
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=8
        )

    def create_context_analysis_task(
        self,
        symbol: str,
        spike_detected: bool,
        spike_magnitude: float
    ) -> Task:
        """
        Create a context analysis task for a detected spike

        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            spike_detected: Whether a spike was detected
            spike_magnitude: Magnitude of the spike (percentage)

        Returns:
            Task for context analysis
        """
        return Task(
            description=f"""ANALYZE MARKET CONTEXT FOR {symbol} SPIKE:

SPIKE INFORMATION:
- Symbol: {symbol}
- Spike Detected: {spike_detected}
- Magnitude: {spike_magnitude}%

ANALYSIS STEPS:

1. CHECK CIRCUIT BREAKER STATUS:
   - Use check_circuit_breaker_status tool
   - If NOT safe → Return {{"is_genuine": false, "reason": "Circuit breaker active - market crash in progress"}}

2. ANALYZE BTC CORRELATION:
   - Get current BTC price using get_current_price("BTCUSDT")
   - Get BTC volatility using get_market_volatility("BTCUSDT")
   - Determine if {symbol} spike is correlated with BTC movement
   - If BTC also spiking significantly → Lower spike uniqueness

3. ANALYZE ETH CORRELATION:
   - Get current ETH price using get_current_price("ETHUSDT")
   - Get ETH volatility using get_market_volatility("ETHUSDT")
   - Check if market-wide movement or {symbol}-specific

4. ASSESS SPIKE GENUINENESS:
   Consider these factors:
   - Is the spike isolated to {symbol} or market-wide?
   - Is BTC/ETH also experiencing high volatility?
   - What is the overall market sentiment?
   - Is the magnitude reasonable ({spike_magnitude}%)?

5. DETERMINE MANIPULATION RISK:
   High risk indicators:
   - Very large spike (>10%) with no BTC/ETH correlation
   - Extreme volatility spike without market-wide movement
   - Spike during low global market activity

   Low risk indicators:
   - Moderate spike (3-7%) with some BTC correlation
   - Gradual volatility increase
   - Spike during active market hours

6. PROVIDE RECOMMENDATION:
   - HIGH CONFIDENCE (>0.8): Likely genuine, strong fundamentals
   - MEDIUM CONFIDENCE (0.5-0.8): Unclear, proceed with caution
   - LOW CONFIDENCE (<0.5): Likely false signal or manipulation

RETURN: Detailed context analysis with confidence score""",
            agent=self.agent,
            expected_output="""JSON report with:
- is_genuine: true/false
- confidence: 0.0-1.0
- btc_correlation: High/Medium/Low
- eth_correlation: High/Medium/Low
- market_wide_movement: true/false
- manipulation_risk: High/Medium/Low
- overall_market_sentiment: Bullish/Bearish/Neutral
- recommendation: PROCEED/CAUTION/AVOID
- reasoning: Detailed explanation of analysis"""
        )

    def analyze_spike_context(
        self,
        symbol: str,
        spike_detected: bool,
        spike_magnitude: float
    ) -> dict:
        """
        Analyze market context for a spike

        Args:
            symbol: Trading pair
            spike_detected: Whether spike was detected
            spike_magnitude: Spike magnitude percentage

        Returns:
            dict: Context analysis results
        """
        from crewai import Crew, Process

        task = self.create_context_analysis_task(symbol, spike_detected, spike_magnitude)

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


def main():
    """Main entry point for testing"""
    print("\n🔍 Context Analyzer Agent - Testing Mode\n")

    # Initialize analyzer
    analyzer = ContextAnalyzer()

    # Analyze a hypothetical spike
    print("\n📊 Analyzing context for BTCUSDT spike...\n")
    result = analyzer.analyze_spike_context(
        symbol="BTCUSDT",
        spike_detected=True,
        spike_magnitude=6.5
    )

    print("\n" + "=" * 70)
    if result['success']:
        print("✅ Context analysis completed")
        print(f"\nResult:\n{result['result']}")
    else:
        print(f"❌ Analysis failed: {result.get('error')}")
    print("=" * 70)


if __name__ == "__main__":
    main()
