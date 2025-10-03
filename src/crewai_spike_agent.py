#!/usr/bin/env python3
"""
CrewAI Spike Agent - Main Orchestrator
Coordinates Market Guardian and Market Scanner agents
Provides spike detection and circuit breaker protection
"""

import os
import sys
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.market_guardian_agent import MarketGuardian
from agents.market_scanner_agent import MarketScanner
from database import TradingDatabase
from circuit_breaker_state import get_circuit_breaker_state


class CrewAISpikeAgent:
    """
    Main orchestrator for CrewAI spike detection and circuit breaker system
    """

    def __init__(self):
        """Initialize the CrewAI Spike Agent system"""
        print("\n" + "=" * 70)
        print("🤖 CREWAI SPIKE AGENT SYSTEM")
        print("=" * 70)

        # Initialize components
        self.db = TradingDatabase()
        self.cb_state = get_circuit_breaker_state()

        # Initialize agents
        print("\n📡 Initializing agents...")
        self.market_guardian = MarketGuardian()
        self.market_scanner = MarketScanner()

        # Threading control
        self.guardian_thread = None
        self.scanner_thread = None
        self.stop_flag = threading.Event()

        print("\n✅ CrewAI Spike Agent System initialized")
        print("=" * 70)

    def start_market_guardian_background(self):
        """Start Market Guardian in background thread"""
        if self.guardian_thread and self.guardian_thread.is_alive():
            print("⚠️  Market Guardian already running")
            return

        print("\n🛡️  Starting Market Guardian in background...")

        def guardian_loop():
            """Background loop for Market Guardian"""
            interval_seconds = self.market_guardian.config.get('monitoring_interval_ms', 5000) / 1000
            cycle_count = 0

            while not self.stop_flag.is_set():
                cycle_count += 1
                print(f"\n🛡️  Guardian Cycle #{cycle_count} - {datetime.now().strftime('%H:%M:%S')}")

                try:
                    result = self.market_guardian.monitor_once()

                    if result['success']:
                        # Log to database
                        self._log_guardian_activity(result)
                    else:
                        print(f"❌ Guardian cycle failed: {result.get('error')}")

                except Exception as e:
                    print(f"❌ Guardian error: {e}")

                # Sleep with interruption check
                for _ in range(int(interval_seconds)):
                    if self.stop_flag.is_set():
                        break
                    time.sleep(1)

            print("🛡️  Market Guardian stopped")

        self.guardian_thread = threading.Thread(target=guardian_loop, daemon=True)
        self.guardian_thread.start()
        print("✅ Market Guardian running in background")

    def scan_for_spikes(self, symbol: Optional[str] = None) -> Dict:
        """
        Scan for price spikes

        Args:
            symbol: Optional specific symbol to scan. If None, scans all monitored pairs.

        Returns:
            dict: Spike detection results
        """
        # Check circuit breaker first
        if not self.cb_state.is_safe():
            return {
                'success': False,
                'reason': 'Circuit breaker active',
                'circuit_breaker_status': self.cb_state.get_status().value
            }

        if symbol:
            result = self.market_scanner.scan_symbol(symbol)
            self._log_spike_scan(result)
            return result
        else:
            results = self.market_scanner.scan_all_pairs()
            for result in results:
                self._log_spike_scan(result)
            return {
                'success': True,
                'scans_completed': len(results),
                'results': results
            }

    def get_system_status(self) -> Dict:
        """
        Get comprehensive system status

        Returns:
            dict: System status information
        """
        cb_status = self.cb_state.get_status()
        cb_full_state = self.cb_state.get_full_state()

        return {
            'timestamp': datetime.now().isoformat(),
            'circuit_breaker': {
                'status': cb_status.value,
                'is_safe': self.cb_state.is_safe(),
                'is_active': self.cb_state.is_active(),
                'triggered_at': cb_full_state.get('triggered_at'),
                'trigger_reason': cb_full_state.get('trigger_reason')
            },
            'market_guardian': {
                'running': self.guardian_thread.is_alive() if self.guardian_thread else False,
                'monitoring_interval_ms': self.market_guardian.config.get('monitoring_interval_ms', 5000)
            },
            'market_scanner': {
                'monitored_pairs': self.market_scanner.config.get('monitored_pairs', []),
                'price_spike_threshold': self.market_scanner.config.get('price_spike_threshold', 5.0),
                'volume_spike_multiplier': self.market_scanner.config.get('volume_spike_multiplier', 3.0)
            }
        }

    def stop(self):
        """Stop all background processes"""
        print("\n🛑 Stopping CrewAI Spike Agent System...")
        self.stop_flag.set()

        # Wait for threads to finish
        if self.guardian_thread and self.guardian_thread.is_alive():
            self.guardian_thread.join(timeout=5)

        print("✅ CrewAI Spike Agent System stopped")

    def _log_guardian_activity(self, result: Dict):
        """Log Market Guardian activity to database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO agent_decisions (
                    timestamp,
                    agent_name,
                    agent_role,
                    decision_type,
                    decision,
                    confidence,
                    reasoning,
                    output_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                'market_guardian',
                'Market Crash Protection Specialist',
                'circuit_breaker_check',
                'MONITORED',
                1.0,
                'Routine monitoring cycle',
                str(result.get('result', ''))[:1000]  # Truncate to 1000 chars
            ))

            conn.commit()

        except Exception as e:
            print(f"⚠️  Failed to log guardian activity: {e}")

    def _log_spike_scan(self, result: Dict):
        """Log spike scan to database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO agent_decisions (
                    timestamp,
                    agent_name,
                    agent_role,
                    decision_type,
                    decision,
                    confidence,
                    reasoning,
                    input_data,
                    output_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                'market_scanner',
                'Binance Market Surveillance Specialist',
                'spike_scan',
                'SCANNED',
                0.8,
                f"Scanned {result.get('symbol', 'unknown')} for spikes",
                result.get('symbol', ''),
                str(result.get('result', ''))[:1000]  # Truncate to 1000 chars
            ))

            conn.commit()

        except Exception as e:
            print(f"⚠️  Failed to log spike scan: {e}")


def main():
    """Main entry point"""
    print("\n🤖 CrewAI Spike Agent - Main Orchestrator\n")

    # Create orchestrator
    orchestrator = CrewAISpikeAgent()

    # Get system status
    status = orchestrator.get_system_status()
    print("\n📊 System Status:")
    print(f"   Circuit Breaker: {status['circuit_breaker']['status']}")
    print(f"   Is Safe: {status['circuit_breaker']['is_safe']}")
    print(f"   Guardian Running: {status['market_guardian']['running']}")
    print(f"   Monitored Pairs: {', '.join(status['market_scanner']['monitored_pairs'])}")

    print("\n💡 Available commands:")
    print("   orchestrator.start_market_guardian_background()  # Start guardian")
    print("   orchestrator.scan_for_spikes('BTCUSDT')         # Scan specific symbol")
    print("   orchestrator.scan_for_spikes()                  # Scan all pairs")
    print("   orchestrator.get_system_status()                # Get status")
    print("   orchestrator.stop()                             # Stop all")

    # Interactive mode
    import argparse
    parser = argparse.ArgumentParser(description="CrewAI Spike Agent Orchestrator")
    parser.add_argument('--start-guardian', action='store_true',
                       help='Start Market Guardian in background')
    parser.add_argument('--scan', type=str, nargs='?', const='ALL',
                       help='Scan for spikes (specify symbol or ALL)')
    parser.add_argument('--daemon', action='store_true',
                       help='Run as daemon with both guardian and scanner')
    args = parser.parse_args()

    if args.start_guardian:
        orchestrator.start_market_guardian_background()
        print("\n✅ Market Guardian started. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            orchestrator.stop()

    elif args.scan:
        if args.scan == 'ALL':
            result = orchestrator.scan_for_spikes()
        else:
            result = orchestrator.scan_for_spikes(args.scan)

        print("\n📊 Scan Results:")
        print(result)

    elif args.daemon:
        orchestrator.start_market_guardian_background()
        print("\n🚀 Running in daemon mode...")
        print("   Market Guardian: Monitoring for crashes")
        print("   Spike Scanner: On-demand via API")
        print("\n   Press Ctrl+C to stop")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            orchestrator.stop()

    else:
        print("\n📖 Run with --help for options")


if __name__ == "__main__":
    main()
