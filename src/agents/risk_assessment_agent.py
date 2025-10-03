#!/usr/bin/env python3
"""
Risk Assessment Agent - Trade Risk Evaluation
Evaluates risk for potential spike trades and provides position sizing recommendations
"""

import os
import sys
import yaml
from datetime import datetime
from crewai import Agent, Task

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.risk_tools import (
    get_portfolio_status,
    calculate_position_size,
    check_daily_loss_limit,
    calculate_stop_loss_take_profit,
    check_market_stability,
    calculate_risk_metrics,
    get_recent_performance
)


class RiskAssessmentAgent:
    """
    Risk Assessment Agent - Evaluates trade risk and position sizing
    """

    def __init__(self, config_path: str = "config/crewai_config.yaml"):
        """Initialize Risk Assessment Agent with configuration"""
        self.config = self._load_config(config_path)
        self.agent = self._create_agent()

        print("🛡️  Risk Assessment Agent initialized")
        print(f"   Max risk per trade: {self.config.get('max_risk_percent', 2.0)}%")
        print(f"   Max daily loss: {self.config.get('max_daily_loss_percent', 5.0)}%")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                full_config = yaml.safe_load(f)
                return full_config.get('risk_assessment', {})
        else:
            # Default configuration
            return {
                'max_risk_percent': 2.0,
                'max_daily_loss_percent': 5.0,
                'max_position_percent': 30.0,
                'default_leverage': 10,
                'stop_loss_percent': 2.0,
                'take_profit_percent': 5.0
            }

    def _create_agent(self) -> Agent:
        """Create the Risk Assessment agent"""
        return Agent(
            role="Risk Management Specialist",
            goal="""Evaluate trading risk and provide optimal position sizing recommendations.
            Ensure all trades comply with risk management rules.
            Protect capital from excessive losses while maximizing opportunity.""",
            backstory="""You are a professional risk manager for a trading bot.
            Your primary responsibility is capital preservation through proper risk management.

            You evaluate:
            - Current portfolio status and available capital
            - Position sizing based on account balance and volatility
            - Stop loss and take profit levels
            - Daily and weekly loss limits
            - Market stability (circuit breaker status)
            - Recent trading performance
            - Risk/reward ratios for each trade

            You enforce strict rules:
            - Never risk more than {max_risk_percent}% per trade
            - Never exceed {max_daily_loss_percent}% daily loss limit
            - Position size must not exceed {max_position_percent}% of balance
            - Always check circuit breaker before approving trades
            - Reject trades during high-risk market conditions

            You are conservative, analytical, and prioritize capital preservation
            over profit maximization. When in doubt, you recommend reducing position
            size or avoiding the trade entirely.""".format(
                max_risk_percent=self.config.get('max_risk_percent', 2.0),
                max_daily_loss_percent=self.config.get('max_daily_loss_percent', 5.0),
                max_position_percent=self.config.get('max_position_percent', 30.0)
            ),
            tools=[
                get_portfolio_status,
                calculate_position_size,
                check_daily_loss_limit,
                calculate_stop_loss_take_profit,
                check_market_stability,
                calculate_risk_metrics,
                get_recent_performance
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=10
        )

    def create_risk_assessment_task(
        self,
        symbol: str,
        entry_price: float,
        side: str,
        spike_confidence: float
    ) -> Task:
        """
        Create a risk assessment task for a potential trade

        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            entry_price: Planned entry price
            side: "LONG" or "SHORT"
            spike_confidence: Confidence score from spike detection (0.0-1.0)

        Returns:
            Task for risk assessment
        """
        return Task(
            description=f"""RISK ASSESSMENT FOR {symbol} TRADE:

TRADE PARAMETERS:
- Symbol: {symbol}
- Entry Price: ${entry_price}
- Side: {side}
- Spike Confidence: {spike_confidence}

COMPREHENSIVE RISK ANALYSIS:

1. CHECK MARKET STABILITY:
   - Use check_market_stability tool
   - If circuit breaker active → REJECT trade immediately

2. CHECK DAILY LOSS LIMIT:
   - Use check_daily_loss_limit tool with {self.config.get('max_daily_loss_percent', 5.0)}%
   - If limit exceeded → REJECT trade

3. GET PORTFOLIO STATUS:
   - Use get_portfolio_status tool
   - Check current balance, open positions, recent performance
   - Verify sufficient capital available

4. CALCULATE STOP LOSS & TAKE PROFIT:
   - Use calculate_stop_loss_take_profit tool
   - Entry: ${entry_price}, Side: {side}
   - SL: {self.config.get('stop_loss_percent', 2.0)}%, TP: {self.config.get('take_profit_percent', 5.0)}%
   - Verify risk/reward ratio is favorable (minimum 2:1)

5. CALCULATE OPTIMAL POSITION SIZE:
   - Use calculate_position_size tool
   - Risk: {self.config.get('max_risk_percent', 2.0)}% of balance
   - Based on stop loss distance
   - Ensure position doesn't exceed {self.config.get('max_position_percent', 30.0)}% of balance

6. CALCULATE RISK METRICS:
   - Use calculate_risk_metrics tool
   - Leverage: {self.config.get('default_leverage', 10)}x
   - Verify liquidation distance is safe (>10%)
   - Check risk level classification

7. CHECK RECENT PERFORMANCE:
   - Use get_recent_performance tool (24 hours)
   - If recent win rate < 40% → Reduce position size by 50%
   - If recent losses > 3 consecutive → Consider avoiding trade

8. MAKE FINAL DECISION:
   Based on ALL above factors:

   APPROVE if:
   - ✅ Market is stable (no circuit breaker)
   - ✅ Daily loss limit not exceeded
   - ✅ Sufficient capital available
   - ✅ Risk/reward ratio >= 2:1
   - ✅ Position size within limits
   - ✅ Spike confidence >= 0.7

   REDUCE POSITION if:
   - ⚠️  Spike confidence 0.5-0.7
   - ⚠️  Recent performance poor
   - ⚠️  High market volatility

   REJECT if:
   - ❌ Circuit breaker active
   - ❌ Daily loss limit exceeded
   - ❌ Insufficient capital
   - ❌ Risk/reward ratio < 1.5:1
   - ❌ Spike confidence < 0.5

RETURN: Detailed risk assessment with clear recommendation""",
            agent=self.agent,
            expected_output="""JSON report with:
- decision: APPROVE/REDUCE/REJECT
- recommended_position_size: Size in base currency
- stop_loss: Price level
- take_profit: Price level
- risk_amount: Dollar amount at risk
- risk_percent: Percentage of balance at risk
- risk_reward_ratio: Ratio (e.g., 2.5)
- max_loss_if_stopped: Dollar amount
- expected_profit_if_target: Dollar amount
- confidence: 0.0-1.0 in this recommendation
- warnings: List of risk warnings
- reasoning: Detailed explanation"""
        )

    def assess_trade_risk(
        self,
        symbol: str,
        entry_price: float,
        side: str,
        spike_confidence: float
    ) -> dict:
        """
        Assess risk for a potential trade

        Args:
            symbol: Trading pair
            entry_price: Entry price
            side: LONG or SHORT
            spike_confidence: Spike confidence score

        Returns:
            dict: Risk assessment results
        """
        from crewai import Crew, Process

        task = self.create_risk_assessment_task(symbol, entry_price, side, spike_confidence)

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
    print("\n🛡️  Risk Assessment Agent - Testing Mode\n")

    # Initialize agent
    agent = RiskAssessmentAgent()

    # Assess a hypothetical trade
    print("\n📊 Assessing risk for BTCUSDT long trade...\n")
    result = agent.assess_trade_risk(
        symbol="BTCUSDT",
        entry_price=65000.0,
        side="LONG",
        spike_confidence=0.75
    )

    print("\n" + "=" * 70)
    if result['success']:
        print("✅ Risk assessment completed")
        print(f"\nResult:\n{result['result']}")
    else:
        print(f"❌ Assessment failed: {result.get('error')}")
    print("=" * 70)


if __name__ == "__main__":
    main()
