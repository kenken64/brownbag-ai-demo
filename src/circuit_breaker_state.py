"""
Circuit Breaker State Manager
Manages shared state for circuit breaker protection across all agents and bot components
Supports both in-memory (thread-safe) and Redis-based state management
"""

import os
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from enum import Enum


class CircuitBreakerStatus(Enum):
    """Circuit breaker status enum"""
    SAFE = "SAFE"
    WARNING = "WARNING"
    TRIGGERED = "TRIGGERED"
    RECOVERING = "RECOVERING"


class CircuitBreakerState:
    """
    Thread-safe circuit breaker state manager
    Manages circuit breaker status, crash events, and recovery conditions
    """

    def __init__(self, use_redis: bool = False, redis_config: Optional[Dict] = None):
        """
        Initialize circuit breaker state manager

        Args:
            use_redis: Whether to use Redis for shared state (default: False, use in-memory)
            redis_config: Redis configuration dict with host, port, db
        """
        self.use_redis = use_redis
        self.redis_client = None
        self.lock = threading.Lock()

        # In-memory state (used if Redis is not enabled)
        self._state = {
            "status": CircuitBreakerStatus.SAFE.value,
            "triggered_at": None,
            "trigger_reason": None,
            "trigger_details": {},
            "recovery_started_at": None,
            "last_check_at": None,
            "market_snapshot": {},
            "downtime_seconds": 0,
            "capital_saved": 0.0,
            "total_triggers": 0,
            "false_triggers": 0
        }

        if use_redis:
            self._init_redis(redis_config or {})

    def _init_redis(self, config: Dict):
        """Initialize Redis connection"""
        try:
            import redis
            self.redis_client = redis.Redis(
                host=config.get('host', 'localhost'),
                port=config.get('port', 6379),
                db=config.get('db', 0),
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            print("✅ Redis connection established for circuit breaker state")
        except ImportError:
            print("⚠️ Redis library not installed, falling back to in-memory state")
            self.use_redis = False
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}, falling back to in-memory state")
            self.use_redis = False

    def get_status(self) -> CircuitBreakerStatus:
        """Get current circuit breaker status"""
        with self.lock:
            if self.use_redis:
                status_str = self.redis_client.get("circuit_breaker:status")
                return CircuitBreakerStatus(status_str) if status_str else CircuitBreakerStatus.SAFE
            return CircuitBreakerStatus(self._state["status"])

    def is_active(self) -> bool:
        """Check if circuit breaker is currently active (TRIGGERED or RECOVERING)"""
        status = self.get_status()
        return status in [CircuitBreakerStatus.TRIGGERED, CircuitBreakerStatus.RECOVERING]

    def is_safe(self) -> bool:
        """Check if circuit breaker status is SAFE"""
        return self.get_status() == CircuitBreakerStatus.SAFE

    def trigger(
        self,
        reason: str,
        details: Dict[str, Any],
        market_snapshot: Optional[Dict] = None
    ) -> bool:
        """
        Trigger circuit breaker

        Args:
            reason: Reason for triggering (e.g., "BTC dropped 17.3% in 52 minutes")
            details: Detailed information about the crash
            market_snapshot: Current market data snapshot

        Returns:
            True if successfully triggered, False if already triggered
        """
        with self.lock:
            current_status = self.get_status()

            # Don't re-trigger if already triggered
            if current_status == CircuitBreakerStatus.TRIGGERED:
                return False

            triggered_at = datetime.now().isoformat()

            if self.use_redis:
                self.redis_client.set("circuit_breaker:status", CircuitBreakerStatus.TRIGGERED.value)
                self.redis_client.set("circuit_breaker:triggered_at", triggered_at)
                self.redis_client.set("circuit_breaker:trigger_reason", reason)
                self.redis_client.set("circuit_breaker:trigger_details", json.dumps(details))
                if market_snapshot:
                    self.redis_client.set("circuit_breaker:market_snapshot", json.dumps(market_snapshot))
                # Increment total triggers
                self.redis_client.incr("circuit_breaker:total_triggers")
            else:
                self._state["status"] = CircuitBreakerStatus.TRIGGERED.value
                self._state["triggered_at"] = triggered_at
                self._state["trigger_reason"] = reason
                self._state["trigger_details"] = details
                self._state["market_snapshot"] = market_snapshot or {}
                self._state["total_triggers"] += 1

            print(f"🚨 CIRCUIT BREAKER TRIGGERED: {reason}")
            return True

    def set_warning(self, reason: str, details: Dict[str, Any]):
        """
        Set circuit breaker to WARNING status (approaching trigger threshold)

        Args:
            reason: Warning reason (e.g., "BTC down 12%, approaching 15% threshold")
            details: Warning details
        """
        with self.lock:
            current_status = self.get_status()

            # Only set warning if currently SAFE
            if current_status != CircuitBreakerStatus.SAFE:
                return

            if self.use_redis:
                self.redis_client.set("circuit_breaker:status", CircuitBreakerStatus.WARNING.value)
                self.redis_client.set("circuit_breaker:trigger_reason", reason)
                self.redis_client.set("circuit_breaker:trigger_details", json.dumps(details))
            else:
                self._state["status"] = CircuitBreakerStatus.WARNING.value
                self._state["trigger_reason"] = reason
                self._state["trigger_details"] = details

            print(f"⚠️ CIRCUIT BREAKER WARNING: {reason}")

    def start_recovery(self):
        """Start recovery process after market stabilization"""
        with self.lock:
            if self.get_status() != CircuitBreakerStatus.TRIGGERED:
                return

            recovery_started_at = datetime.now().isoformat()

            if self.use_redis:
                self.redis_client.set("circuit_breaker:status", CircuitBreakerStatus.RECOVERING.value)
                self.redis_client.set("circuit_breaker:recovery_started_at", recovery_started_at)
            else:
                self._state["status"] = CircuitBreakerStatus.RECOVERING.value
                self._state["recovery_started_at"] = recovery_started_at

            print("🔄 Circuit breaker: Starting recovery process...")

    def clear(self, capital_saved: float = 0.0):
        """
        Clear circuit breaker and return to SAFE status

        Args:
            capital_saved: Estimated capital saved by circuit breaker activation
        """
        with self.lock:
            # Calculate downtime
            downtime_seconds = 0
            if self.use_redis:
                triggered_at_str = self.redis_client.get("circuit_breaker:triggered_at")
                if triggered_at_str:
                    triggered_at = datetime.fromisoformat(triggered_at_str)
                    downtime_seconds = int((datetime.now() - triggered_at).total_seconds())
            else:
                if self._state["triggered_at"]:
                    triggered_at = datetime.fromisoformat(self._state["triggered_at"])
                    downtime_seconds = int((datetime.now() - triggered_at).total_seconds())

            if self.use_redis:
                self.redis_client.set("circuit_breaker:status", CircuitBreakerStatus.SAFE.value)
                self.redis_client.set("circuit_breaker:downtime_seconds", downtime_seconds)
                if capital_saved > 0:
                    current_saved = float(self.redis_client.get("circuit_breaker:capital_saved") or 0)
                    self.redis_client.set("circuit_breaker:capital_saved", current_saved + capital_saved)
                # Clear trigger info
                self.redis_client.delete("circuit_breaker:triggered_at")
                self.redis_client.delete("circuit_breaker:trigger_reason")
                self.redis_client.delete("circuit_breaker:trigger_details")
                self.redis_client.delete("circuit_breaker:recovery_started_at")
            else:
                self._state["status"] = CircuitBreakerStatus.SAFE.value
                self._state["downtime_seconds"] = downtime_seconds
                self._state["capital_saved"] += capital_saved
                self._state["triggered_at"] = None
                self._state["trigger_reason"] = None
                self._state["trigger_details"] = {}
                self._state["recovery_started_at"] = None

            print(f"✅ Circuit breaker cleared. Downtime: {downtime_seconds}s. Capital saved: ${capital_saved:.2f}")

    def get_full_state(self) -> Dict[str, Any]:
        """Get complete circuit breaker state"""
        with self.lock:
            if self.use_redis:
                return {
                    "status": self.redis_client.get("circuit_breaker:status") or CircuitBreakerStatus.SAFE.value,
                    "triggered_at": self.redis_client.get("circuit_breaker:triggered_at"),
                    "trigger_reason": self.redis_client.get("circuit_breaker:trigger_reason"),
                    "trigger_details": json.loads(self.redis_client.get("circuit_breaker:trigger_details") or "{}"),
                    "recovery_started_at": self.redis_client.get("circuit_breaker:recovery_started_at"),
                    "market_snapshot": json.loads(self.redis_client.get("circuit_breaker:market_snapshot") or "{}"),
                    "downtime_seconds": int(self.redis_client.get("circuit_breaker:downtime_seconds") or 0),
                    "capital_saved": float(self.redis_client.get("circuit_breaker:capital_saved") or 0),
                    "total_triggers": int(self.redis_client.get("circuit_breaker:total_triggers") or 0),
                    "last_check_at": self.redis_client.get("circuit_breaker:last_check_at")
                }
            return self._state.copy()

    def update_last_check(self):
        """Update last check timestamp"""
        with self.lock:
            last_check = datetime.now().isoformat()
            if self.use_redis:
                self.redis_client.set("circuit_breaker:last_check_at", last_check)
            else:
                self._state["last_check_at"] = last_check

    def get_trigger_info(self) -> Dict[str, Any]:
        """Get information about current/last trigger"""
        state = self.get_full_state()
        return {
            "status": state["status"],
            "triggered_at": state["triggered_at"],
            "reason": state["trigger_reason"],
            "details": state["trigger_details"],
            "market_snapshot": state["market_snapshot"]
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        state = self.get_full_state()
        return {
            "total_triggers": state["total_triggers"],
            "false_triggers": state.get("false_triggers", 0),
            "total_downtime_seconds": state["downtime_seconds"],
            "capital_saved": state["capital_saved"],
            "last_check_at": state["last_check_at"]
        }

    def mark_false_trigger(self):
        """Mark the last trigger as a false positive"""
        with self.lock:
            if self.use_redis:
                self.redis_client.incr("circuit_breaker:false_triggers")
            else:
                self._state["false_triggers"] += 1


# Global circuit breaker state instance
_circuit_breaker_state = None


def get_circuit_breaker_state(use_redis: bool = False, redis_config: Optional[Dict] = None) -> CircuitBreakerState:
    """
    Get global circuit breaker state instance (singleton pattern)

    Args:
        use_redis: Whether to use Redis for shared state
        redis_config: Redis configuration dict

    Returns:
        CircuitBreakerState instance
    """
    global _circuit_breaker_state
    if _circuit_breaker_state is None:
        _circuit_breaker_state = CircuitBreakerState(use_redis=use_redis, redis_config=redis_config)
    return _circuit_breaker_state


if __name__ == "__main__":
    # Test circuit breaker state manager
    print("Testing Circuit Breaker State Manager...")

    # Test in-memory state
    state = CircuitBreakerState(use_redis=False)

    print(f"\n1. Initial status: {state.get_status()}")
    print(f"   Is safe? {state.is_safe()}")
    print(f"   Is active? {state.is_active()}")

    # Trigger circuit breaker
    print("\n2. Triggering circuit breaker...")
    state.trigger(
        reason="BTC dropped 17.3% in 52 minutes",
        details={
            "btc_price_from": 50850,
            "btc_price_to": 42150,
            "drop_percent": 17.3,
            "timeframe_minutes": 52
        },
        market_snapshot={
            "btc_price": 42150,
            "eth_price": 2240,
            "market_cap_drop_percent": 18.5,
            "liquidations_1h": 687000000
        }
    )

    print(f"   Status: {state.get_status()}")
    print(f"   Is active? {state.is_active()}")

    # Get trigger info
    print("\n3. Trigger info:")
    trigger_info = state.get_trigger_info()
    print(f"   Reason: {trigger_info['reason']}")
    print(f"   Details: {trigger_info['details']}")

    # Start recovery
    print("\n4. Starting recovery...")
    state.start_recovery()
    print(f"   Status: {state.get_status()}")

    # Clear circuit breaker
    print("\n5. Clearing circuit breaker...")
    state.clear(capital_saved=4810.0)
    print(f"   Status: {state.get_status()}")

    # Get stats
    print("\n6. Statistics:")
    stats = state.get_stats()
    print(f"   Total triggers: {stats['total_triggers']}")
    print(f"   Capital saved: ${stats['capital_saved']:.2f}")
    print(f"   Downtime: {stats['total_downtime_seconds']}s")

    print("\n✅ Circuit Breaker State Manager test completed!")
