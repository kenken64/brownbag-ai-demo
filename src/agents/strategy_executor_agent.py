#!/usr/bin/env python3
"""
Strategy Executor Agent - Trade Execution
Executes trades based on approved spike opportunities with proper risk management
"""

import os
import sys
import yaml
from datetime import datetime
from crewai import Agent, Task

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.circuit_breaker_tools import check_circuit_breaker_status
from binance_client import BinanceClient


class StrategyExecutor:
    """
    Strategy Executor - Executes approved trades with risk management
    """

    def __init__(self, config_path: str = "config/crewai_config.yaml"):
        """Initialize Strategy Executor with configuration"""
        self.config = self._load_config(config_path)
        self.binance_client = BinanceClient()
        self.agent = self._create_agent()

        print("⚡ Strategy Executor Agent initialized")
        print(f"   Execution mode: {self.config.get('execution_mode', 'PAPER')}")
        print(f"   Use testnet: {os.getenv('USE_TESTNET', 'true')}")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                full_config = yaml.safe_load(f)
                return full_config.get('strategy_executor', {})
        else:
            # Default configuration
            return {
                'execution_mode': 'PAPER',  # PAPER, LIVE
                'order_type': 'MARKET',
                'enable_stop_loss': True,
                'enable_take_profit': True,
                'max_slippage_percent': 0.5
            }

    def _create_agent(self) -> Agent:
        """Create the Strategy Executor agent"""
        execution_mode = self.config.get('execution_mode', 'PAPER')

        return Agent(
            role="Trade Execution Specialist",
            goal=f"""Execute approved trades efficiently with minimal slippage.
            Current mode: {execution_mode}
            Manage stop loss and take profit orders.
            Monitor positions and provide execution reports.""",
            backstory=f"""You are a trade execution specialist responsible for executing
            approved trades on Binance Futures.

            Current Execution Mode: {execution_mode}
            {"⚠️  PAPER TRADING MODE - No real orders executed" if execution_mode == "PAPER" else "🔴 LIVE TRADING - Real money at risk"}

            Your responsibilities:
            - Execute market orders at best available prices
            - Place stop loss and take profit orders
            - Monitor for excessive slippage
            - Verify order execution
            - Log all execution details
            - Handle execution errors gracefully

            Execution rules:
            - ALWAYS check circuit breaker before execution
            - ALWAYS verify position size is within limits
            - NEVER execute if slippage exceeds {self.config.get('max_slippage_percent', 0.5)}%
            - ALWAYS place protective stops immediately after entry
            - Log every action for audit trail

            In PAPER mode: Simulate execution without placing real orders
            In LIVE mode: Execute real orders with extreme caution

            You are precise, careful, and double-check every parameter before execution.""",
            tools=[check_circuit_breaker_status],
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )

    def create_execution_task(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        position_size: float,
        stop_loss: float,
        take_profit: float
    ) -> Task:
        """
        Create a trade execution task

        Args:
            symbol: Trading pair
            side: LONG or SHORT
            entry_price: Entry price
            position_size: Position size
            stop_loss: Stop loss price
            take_profit: Take profit price

        Returns:
            Task for trade execution
        """
        execution_mode = self.config.get('execution_mode', 'PAPER')

        return Task(
            description=f"""EXECUTE {symbol} TRADE:

TRADE PARAMETERS:
- Symbol: {symbol}
- Side: {side}
- Entry Price: ${entry_price}
- Position Size: {position_size}
- Stop Loss: ${stop_loss}
- Take Profit: ${take_profit}
- Execution Mode: {execution_mode}

EXECUTION WORKFLOW:

1. FINAL SAFETY CHECK:
   - Use check_circuit_breaker_status
   - If circuit breaker active → ABORT execution

2. VERIFY PARAMETERS:
   - Symbol: {symbol}
   - Side: {side} (must be LONG or SHORT)
   - Size: {position_size} (must be > 0)
   - Entry: ${entry_price} (must be valid price)
   - SL: ${stop_loss} (must be on correct side of entry)
   - TP: ${take_profit} (must be on correct side of entry)

3. {"SIMULATE" if execution_mode == "PAPER" else "EXECUTE"} MARKET ORDER:
   {"⚠️  PAPER MODE - Simulating order without real execution" if execution_mode == "PAPER" else "🔴 LIVE MODE - Placing REAL market order"}

   Order details:
   - Type: MARKET
   - Symbol: {symbol}
   - Side: {"BUY" if side == "LONG" else "SELL"}
   - Quantity: {position_size}
   - Expected price: ~${entry_price}

   {"Simulated execution:" if execution_mode == "PAPER" else "Real execution:"}
   - Log order placement
   - Record fill price
   - Calculate actual cost
   - Verify execution

4. {"SIMULATE" if execution_mode == "PAPER" else "PLACE"} STOP LOSS ORDER:
   {"⚠️  PAPER MODE - Simulating SL order" if execution_mode == "PAPER" else "🔴 LIVE MODE - Placing REAL stop loss"}

   - Type: STOP_MARKET
   - Stop Price: ${stop_loss}
   - Side: {"SELL" if side == "LONG" else "BUY"}

5. {"SIMULATE" if execution_mode == "PAPER" else "PLACE"} TAKE PROFIT ORDER:
   {"⚠️  PAPER MODE - Simulating TP order" if execution_mode == "PAPER" else "🔴 LIVE MODE - Placing REAL take profit"}

   - Type: TAKE_PROFIT_MARKET
   - Stop Price: ${take_profit}
   - Side: {"SELL" if side == "LONG" else "BUY"}

6. LOG EXECUTION:
   Record complete execution details:
   - Entry price (actual)
   - Slippage (%)
   - Position size
   - Stop loss order ID
   - Take profit order ID
   - Timestamp
   - Mode: {execution_mode}

7. RETURN EXECUTION REPORT:
   Detailed report of execution status

CRITICAL: In LIVE mode, this executes REAL trades with REAL money.
Double-check all parameters before confirming execution.""",
            agent=self.agent,
            expected_output="""JSON report with:
- execution_status: SUCCESS/FAILED/PAPER_MODE
- mode: PAPER/LIVE
- entry_order_id: Order ID (or "SIMULATED")
- entry_price_actual: Actual fill price
- slippage_percent: Execution slippage
- stop_loss_order_id: SL order ID
- take_profit_order_id: TP order ID
- position_size: Executed size
- total_cost: Total cost in USDT
- timestamp: Execution time
- warnings: Any execution warnings
- notes: Additional notes"""
        )

    def execute_trade(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        position_size: float,
        stop_loss: float,
        take_profit: float
    ) -> dict:
        """
        Execute a trade (or simulate in paper mode)

        Args:
            symbol: Trading pair
            side: LONG or SHORT
            entry_price: Entry price
            position_size: Position size
            stop_loss: Stop loss price
            take_profit: Take profit price

        Returns:
            dict: Execution results
        """
        from crewai import Crew, Process

        task = self.create_execution_task(
            symbol, side, entry_price, position_size, stop_loss, take_profit
        )

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
                'mode': self.config.get('execution_mode', 'PAPER'),
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
    print("\n⚡ Strategy Executor Agent - Testing Mode\n")

    # Initialize executor
    executor = StrategyExecutor()

    # Execute a hypothetical trade (PAPER MODE)
    print("\n📊 Executing BTCUSDT long trade (PAPER MODE)...\n")
    result = executor.execute_trade(
        symbol="BTCUSDT",
        side="LONG",
        entry_price=65000.0,
        position_size=0.01,
        stop_loss=63700.0,
        take_profit=68250.0
    )

    print("\n" + "=" * 70)
    if result['success']:
        print(f"✅ Execution completed ({result['mode']} mode)")
        print(f"\nResult:\n{result['result']}")
    else:
        print(f"❌ Execution failed: {result.get('error')}")
    print("=" * 70)

    print("\n⚠️  IMPORTANT: Currently in PAPER mode (no real trades)")
    print("   To enable LIVE trading, update config/crewai_config.yaml")
    print("   execution_mode: 'LIVE'")
    print("\n   ⚠️  USE EXTREME CAUTION with live trading!")


if __name__ == "__main__":
    main()
