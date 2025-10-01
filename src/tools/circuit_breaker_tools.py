"""
Circuit Breaker Tools for CrewAI Agents
Tools for monitoring market conditions and controlling circuit breaker state
"""

import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crewai_tools import tool
from circuit_breaker_state import get_circuit_breaker_state, CircuitBreakerStatus


@tool("Check Circuit Breaker Status")
def check_circuit_breaker_status() -> str:
    """
    Check the current status of the circuit breaker.

    Returns:
        str: Circuit breaker status (SAFE, WARNING, TRIGGERED, RECOVERING) with additional details
    """
    try:
        cb_state = get_circuit_breaker_state()
        status = cb_state.get_status()
        full_state = cb_state.get_full_state()

        result = {
            "status": status.value,
            "is_safe": cb_state.is_safe(),
            "is_active": cb_state.is_active(),
            "triggered_at": full_state.get("triggered_at"),
            "trigger_reason": full_state.get("trigger_reason"),
            "recovery_started_at": full_state.get("recovery_started_at")
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "status": "UNKNOWN"})


@tool("Trigger Circuit Breaker")
def trigger_circuit_breaker(reason: str, trigger_details: str) -> str:
    """
    Trigger the circuit breaker to halt all trading operations.

    Args:
        reason: Reason for triggering (e.g., "BTC dropped 17.3% in 52 minutes")
        trigger_details: JSON string with detailed crash metrics

    Returns:
        str: Result of triggering the circuit breaker
    """
    try:
        cb_state = get_circuit_breaker_state()

        # Parse trigger details
        details = json.loads(trigger_details) if isinstance(trigger_details, str) else trigger_details

        # Extract market snapshot if available
        market_snapshot = details.get("market_snapshot", {})

        # Trigger circuit breaker
        success = cb_state.trigger(
            reason=reason,
            details=details,
            market_snapshot=market_snapshot
        )

        if success:
            result = {
                "success": True,
                "message": f"Circuit breaker TRIGGERED: {reason}",
                "timestamp": datetime.now().isoformat(),
                "status": "TRIGGERED"
            }
        else:
            result = {
                "success": False,
                "message": "Circuit breaker already active",
                "status": cb_state.get_status().value
            }

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@tool("Set Circuit Breaker Warning")
def set_circuit_breaker_warning(warning_reason: str, warning_details: str) -> str:
    """
    Set circuit breaker to WARNING status (approaching trigger threshold).

    Args:
        warning_reason: Warning reason (e.g., "BTC down 12%, approaching 15% threshold")
        warning_details: JSON string with warning metrics

    Returns:
        str: Result of setting warning status
    """
    try:
        cb_state = get_circuit_breaker_state()

        # Parse warning details
        details = json.loads(warning_details) if isinstance(warning_details, str) else warning_details

        # Set warning
        cb_state.set_warning(reason=warning_reason, details=details)

        result = {
            "success": True,
            "message": f"Circuit breaker set to WARNING: {warning_reason}",
            "timestamp": datetime.now().isoformat(),
            "status": "WARNING"
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@tool("Calculate Market Drawdown")
def calculate_market_drawdown(
    asset: str,
    current_price: float,
    timeframe_hours: int
) -> str:
    """
    Calculate market drawdown percentage for an asset over a timeframe.
    This is a mock implementation - in production, this would fetch historical prices.

    Args:
        asset: Asset symbol (e.g., "BTC", "ETH")
        current_price: Current asset price
        timeframe_hours: Timeframe in hours (1, 4, 24)

    Returns:
        str: Drawdown analysis with percentage and assessment
    """
    try:
        # Mock implementation - in production, fetch real historical prices
        # For now, simulate with random data
        import random

        # Simulate historical high price (10-30% higher than current)
        high_price = current_price * (1 + random.uniform(0.10, 0.30))

        # Calculate drawdown
        drawdown_percent = ((high_price - current_price) / high_price) * 100

        # Determine severity
        if drawdown_percent >= 20:
            severity = "CRITICAL"
            assessment = "Major market crash detected"
        elif drawdown_percent >= 15:
            severity = "SEVERE"
            assessment = "Circuit breaker threshold met"
        elif drawdown_percent >= 10:
            severity = "WARNING"
            assessment = "Approaching circuit breaker threshold"
        else:
            severity = "NORMAL"
            assessment = "Normal market fluctuation"

        result = {
            "asset": asset,
            "current_price": current_price,
            "high_price": high_price,
            "drawdown_percent": round(drawdown_percent, 2),
            "timeframe_hours": timeframe_hours,
            "severity": severity,
            "assessment": assessment,
            "timestamp": datetime.now().isoformat()
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Start Circuit Breaker Recovery")
def start_circuit_breaker_recovery() -> str:
    """
    Start the recovery process after market stabilization.

    Returns:
        str: Result of starting recovery process
    """
    try:
        cb_state = get_circuit_breaker_state()

        # Check current status
        current_status = cb_state.get_status()

        if current_status != CircuitBreakerStatus.TRIGGERED:
            return json.dumps({
                "success": False,
                "message": f"Cannot start recovery - current status is {current_status.value}",
                "status": current_status.value
            })

        # Start recovery
        cb_state.start_recovery()

        result = {
            "success": True,
            "message": "Circuit breaker recovery process started",
            "timestamp": datetime.now().isoformat(),
            "status": "RECOVERING"
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@tool("Clear Circuit Breaker")
def clear_circuit_breaker(capital_saved: float = 0.0) -> str:
    """
    Clear circuit breaker and return to SAFE status after market stabilization.

    Args:
        capital_saved: Estimated capital saved by circuit breaker activation

    Returns:
        str: Result of clearing circuit breaker
    """
    try:
        cb_state = get_circuit_breaker_state()

        # Get current state for reporting
        full_state = cb_state.get_full_state()

        # Clear circuit breaker
        cb_state.clear(capital_saved=capital_saved)

        # Calculate downtime
        downtime_seconds = full_state.get("downtime_seconds", 0)

        result = {
            "success": True,
            "message": "Circuit breaker cleared - trading resumed",
            "timestamp": datetime.now().isoformat(),
            "status": "SAFE",
            "downtime_seconds": downtime_seconds,
            "capital_saved": capital_saved
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


@tool("Get Circuit Breaker Statistics")
def get_circuit_breaker_statistics() -> str:
    """
    Get circuit breaker statistics and history.

    Returns:
        str: Circuit breaker statistics including total triggers, capital saved, etc.
    """
    try:
        cb_state = get_circuit_breaker_state()
        stats = cb_state.get_stats()

        # Calculate uptime percentage
        total_downtime = stats.get("total_downtime_seconds", 0)
        uptime_percent = 100.0  # Default to 100%

        result = {
            "total_triggers": stats.get("total_triggers", 0),
            "false_triggers": stats.get("false_triggers", 0),
            "total_downtime_seconds": total_downtime,
            "total_downtime_minutes": round(total_downtime / 60, 2),
            "capital_saved": stats.get("capital_saved", 0.0),
            "last_check_at": stats.get("last_check_at"),
            "uptime_percent": uptime_percent
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Assess Market Recovery Conditions")
def assess_market_recovery_conditions(
    btc_current_price: float,
    btc_trigger_price: float,
    stabilization_minutes: int,
    recent_drops: str
) -> str:
    """
    Assess if market recovery conditions are met for resuming trading.

    Args:
        btc_current_price: Current BTC price
        btc_trigger_price: BTC price when circuit breaker triggered
        stabilization_minutes: Minutes since last significant drop
        recent_drops: JSON string with recent price drops (array of percentages)

    Returns:
        str: Assessment of recovery conditions
    """
    try:
        # Parse recent drops
        drops = json.loads(recent_drops) if isinstance(recent_drops, str) else recent_drops

        # Calculate recovery percentage
        if btc_trigger_price > 0:
            recovery_percent = ((btc_current_price - btc_trigger_price) / btc_trigger_price) * 100
        else:
            recovery_percent = 0.0

        # Check conditions
        conditions = {
            "stabilization_ok": stabilization_minutes >= 30,
            "no_recent_large_drops": all(abs(drop) < 5.0 for drop in drops),
            "btc_recovered_50_percent": recovery_percent >= 50.0,
            "price_stable": len(drops) == 0 or max(abs(d) for d in drops) < 2.0
        }

        # Determine if safe to resume
        all_conditions_met = all(conditions.values())

        result = {
            "safe_to_resume": all_conditions_met,
            "btc_recovery_percent": round(recovery_percent, 2),
            "stabilization_minutes": stabilization_minutes,
            "conditions": conditions,
            "recommendation": "SAFE TO RESUME TRADING" if all_conditions_met else "CONTINUE MONITORING",
            "timestamp": datetime.now().isoformat()
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# Export all tools as a list for easy registration with CrewAI
circuit_breaker_tools = [
    check_circuit_breaker_status,
    trigger_circuit_breaker,
    set_circuit_breaker_warning,
    calculate_market_drawdown,
    start_circuit_breaker_recovery,
    clear_circuit_breaker,
    get_circuit_breaker_statistics,
    assess_market_recovery_conditions
]


if __name__ == "__main__":
    # Test circuit breaker tools
    print("Testing Circuit Breaker Tools...\n")

    # Test 1: Check status
    print("1. Checking circuit breaker status:")
    result = check_circuit_breaker_status()
    print(result)

    # Test 2: Calculate drawdown
    print("\n2. Calculating market drawdown:")
    result = calculate_market_drawdown.run(asset="BTC", current_price=42000, timeframe_hours=1)
    print(result)

    # Test 3: Get statistics
    print("\n3. Getting circuit breaker statistics:")
    result = get_circuit_breaker_statistics()
    print(result)

    print("\n✅ Circuit Breaker Tools test completed!")
