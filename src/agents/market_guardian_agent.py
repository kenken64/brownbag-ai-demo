#!/usr/bin/env python3
"""
Market Guardian Agent - Circuit Breaker Protection
Continuously monitors market conditions and triggers circuit breaker during crashes
This is the HIGHEST PRIORITY agent for capital protection
"""

import os
import sys
import time
import yaml
from datetime import datetime
from crewai import Agent, Task, Crew, Process

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.circuit_breaker_tools import circuit_breaker_tools
from tools.binance_tools import get_current_price, calculate_price_change


class MarketGuardian:
    """
    Market Guardian - Protects capital by monitoring for market crashes
    """

    def __init__(self, config_path: str = "config/crewai_config.yaml"):
        """Initialize Market Guardian with configuration"""
        self.config = self._load_config(config_path)
        self.agent = self._create_agent()
        self.monitoring_task = self._create_monitoring_task()
        self.crew = self._create_crew()

        print("🛡️  Market Guardian Agent initialized")
        print(f"   Monitoring interval: {self.config.get('monitoring_interval_ms', 5000)}ms")
        print(f"   BTC dump threshold: {self.config.get('btc_dump_threshold', 15.0)}%")
        print(f"   ETH dump threshold: {self.config.get('eth_dump_threshold', 15.0)}%")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                full_config = yaml.safe_load(f)
                return full_config.get('market_guardian', {})
        else:
            # Default configuration
            return {
                'monitoring_interval_ms': 5000,  # 5 seconds
                'btc_dump_threshold': 15.0,
                'eth_dump_threshold': 15.0,
                'market_wide_threshold': 10.0,
                'timeframe_minutes': 60,
                'auto_recovery': True,
                'recovery_wait_minutes': 30
            }

    def _create_agent(self) -> Agent:
        """Create the Market Guardian agent"""
        return Agent(
            role="Market Crash Protection Specialist",
            goal="""Monitor BTC, ETH, and overall market conditions continuously.
            Trigger circuit breaker IMMEDIATELY when market dumps exceed 15% in 1 hour.
            Protect capital from catastrophic losses during black swan events.
            Resume trading ONLY when market stabilizes.""",
            backstory="""You are the guardian of the trading bot's capital.
            Your sole purpose is to detect market crashes and halt all trading
            before significant losses occur. You have the authority to override
            all other agents and stop trading immediately when crashes are detected.

            You monitor:
            - Bitcoin (BTC) price movements
            - Ethereum (ETH) price movements
            - Overall cryptocurrency market conditions

            When you detect:
            - BTC dump >15% in 60 minutes → TRIGGER circuit breaker
            - ETH dump >15% in 60 minutes → TRIGGER circuit breaker
            - Market-wide crash → TRIGGER circuit breaker

            You are cautious, vigilant, and err on the side of safety.
            False positives are acceptable - missing a crash is not.""",
            tools=circuit_breaker_tools + [calculate_price_change],
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )

    def _create_monitoring_task(self) -> Task:
        """Create the continuous monitoring task"""
        return Task(
            description=f"""CONTINUOUS MARKET CRASH MONITORING:

1. CHECK BTC PRICE MOVEMENT (Last 60 minutes):
   - Use calculate_price_change tool for BTCUSDT, 60 minutes
   - If drop >= {self.config.get('btc_dump_threshold', 15.0)}% → TRIGGER circuit breaker

2. CHECK ETH PRICE MOVEMENT (Last 60 minutes):
   - Use calculate_price_change tool for ETHUSDT, 60 minutes
   - If drop >= {self.config.get('eth_dump_threshold', 15.0)}% → TRIGGER circuit breaker

3. CHECK CIRCUIT BREAKER STATUS:
   - Use check_circuit_breaker_status tool
   - If already triggered → Monitor for recovery conditions

4. IF CRASH DETECTED:
   - Use trigger_circuit_breaker tool immediately
   - Provide detailed reason (BTC/ETH drop %, timeframe)
   - Include market snapshot data

5. IF IN RECOVERY:
   - Use assess_market_recovery_conditions tool
   - Check if market has stabilized
   - Recommend resumption ONLY if safe

CRITICAL: You must prioritize SAFETY over profits. When in doubt, trigger the circuit breaker.
A false trigger costs opportunity. Missing a crash costs capital.""",
            agent=self.agent,
            expected_output="""JSON report with:
- btc_status: Safe/Warning/Critical
- eth_status: Safe/Warning/Critical
- circuit_breaker_status: Current status
- action_taken: None/Warning/Triggered/Recovery
- reason: Detailed explanation
- recommendations: What to do next"""
        )

    def _create_crew(self) -> Crew:
        """Create the Market Guardian crew"""
        return Crew(
            agents=[self.agent],
            tasks=[self.monitoring_task],
            process=Process.sequential,
            verbose=True,
            memory=False  # Stateless - relies on circuit breaker state
        )

    def monitor_once(self) -> dict:
        """
        Run one monitoring cycle

        Returns:
            dict: Monitoring results
        """
        try:
            result = self.crew.kickoff()
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'result': str(result)
            }
        except Exception as e:
            return {
                'success': False,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    def start_continuous_monitoring(self):
        """
        Start continuous monitoring loop (blocking)
        Runs indefinitely until interrupted
        """
        print("\n" + "=" * 70)
        print("🛡️  MARKET GUARDIAN - CONTINUOUS MONITORING STARTED")
        print("=" * 70)
        print(f"⏰ Check interval: {self.config.get('monitoring_interval_ms', 5000)}ms")
        print(f"🔴 BTC dump threshold: {self.config.get('btc_dump_threshold', 15.0)}%")
        print(f"🔴 ETH dump threshold: {self.config.get('eth_dump_threshold', 15.0)}%")
        print(f"🛑 Press Ctrl+C to stop")
        print("=" * 70)
        print()

        interval_seconds = self.config.get('monitoring_interval_ms', 5000) / 1000
        cycle_count = 0

        try:
            while True:
                cycle_count += 1
                print(f"\n{'='*70}")
                print(f"🔍 Monitoring Cycle #{cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*70}")

                # Run monitoring cycle
                result = self.monitor_once()

                if result['success']:
                    print(f"✅ Cycle complete")
                else:
                    print(f"❌ Cycle failed: {result.get('error')}")

                # Wait for next cycle
                print(f"⏳ Sleeping for {interval_seconds} seconds...")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n\n" + "=" * 70)
            print("🛑 Market Guardian monitoring stopped by user")
            print("=" * 70)

    def get_status_summary(self) -> str:
        """Get a quick status summary"""
        from circuit_breaker_state import get_circuit_breaker_state

        cb_state = get_circuit_breaker_state()
        status = cb_state.get_status()

        return f"""
Market Guardian Status:
  Circuit Breaker: {status.value}
  Is Safe: {cb_state.is_safe()}
  Monitoring: Active
  Last Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""


def main():
    """Main entry point for testing"""
    print("\n🛡️  Market Guardian Agent - Testing Mode\n")

    # Initialize guardian
    guardian = MarketGuardian()

    # Print status
    print(guardian.get_status_summary())

    # Run one monitoring cycle
    print("\n🔍 Running single monitoring cycle...\n")
    result = guardian.monitor_once()

    print("\n" + "=" * 70)
    if result['success']:
        print("✅ Monitoring cycle completed successfully")
        print(f"\nResult:\n{result['result']}")
    else:
        print(f"❌ Monitoring cycle failed: {result.get('error')}")
    print("=" * 70)

    # Ask if user wants continuous monitoring
    print("\n💡 To start continuous monitoring, use:")
    print("   guardian.start_continuous_monitoring()")
    print("\n   Or run in production mode:")
    print("   python3 src/agents/market_guardian_agent.py --continuous")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Market Guardian Agent")
    parser.add_argument('--continuous', action='store_true',
                       help='Start continuous monitoring (blocking)')
    args = parser.parse_args()

    guardian = MarketGuardian()

    if args.continuous:
        guardian.start_continuous_monitoring()
    else:
        main()
