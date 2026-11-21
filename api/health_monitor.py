"""
M4DI~UciH4 Trading Intelligence System
Provider Health Monitor & Telemetry Engine
Monitors live operational health, connectivity status, and error telemetry.
"""
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List

from config.constants import (
    API_PROVIDERS,
    HEALTH_CONNECTED,
    HEALTH_DISCONNECTED,
    HEALTH_RATE_LIMITED,
    HEALTH_INVALID_KEY,
    HEALTH_ERROR
)
from core.logger import get_app_logger

logger = get_app_logger("HealthMonitor")


class ProviderHealthMonitor:
    """
    Real-time Provider Health and Telemetry Tracker.
    Maintains status, error streak, timestamps, request logs, failover logs,
    and broadcasts updates via EventBus.
    """

    def __init__(self, event_bus=None, db=None):
        self.event_bus = event_bus
        self.db = db
        self._lock = threading.RLock()
        self._health: Dict[str, Dict[str, Any]] = {}
        self._failover_history: List[Dict[str, Any]] = []
        self._recent_requests: List[Dict[str, Any]] = []
        self._recent_errors: List[Dict[str, Any]] = []

        for p in API_PROVIDERS:
            self._health[p] = {
                "provider": p,
                "status": HEALTH_DISCONNECTED,
                "last_success_at": None,
                "last_error_at": None,
                "last_error_message": "",
                "consecutive_errors": 0,
                "total_requests": 0,
                "successful_requests": 0,
                "rate_limited_count": 0,
                "avg_response_time_ms": 0.0,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def record_request(
        self,
        provider: str,
        endpoint: str,
        status_code: int,
        is_success: bool,
        response_time_ms: float = 0.0,
        error_message: str = "",
        key_id: Optional[int] = None
    ):
        """Log granular API request telemetry into in-memory ring buffer & SQLite"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "provider": provider,
            "key_id": key_id,
            "endpoint": endpoint,
            "status_code": status_code,
            "is_success": is_success,
            "response_time_ms": round(response_time_ms, 1),
            "error_message": str(error_message)[:200] if error_message else "",
            "timestamp": now_str
        }

        with self._lock:
            # Memory buffer (capped at 200 items)
            self._recent_requests.insert(0, entry)
            if len(self._recent_requests) > 200:
                self._recent_requests.pop()

            if not is_success:
                self._recent_errors.insert(0, entry)
                if len(self._recent_errors) > 100:
                    self._recent_errors.pop()

            # Update rolling avg response time
            h = self._health.setdefault(provider, {})
            prev_avg = h.get("avg_response_time_ms", 0.0)
            if prev_avg == 0.0:
                h["avg_response_time_ms"] = round(response_time_ms, 1)
            else:
                h["avg_response_time_ms"] = round((prev_avg * 0.8) + (response_time_ms * 0.2), 1)

        # Persist to database asynchronously or direct execute
        if self.db:
            try:
                self.db.execute(
                    """
                    INSERT INTO api_request_logs (
                        provider, key_id, endpoint, status_code, is_success,
                        response_time_ms, error_message, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (provider, key_id, endpoint, status_code, 1 if is_success else 0,
                     response_time_ms, str(error_message)[:200], now_str)
                )
            except Exception as e:
                logger.debug(f"Could not persist api_request_log: {e}")

    def record_failover(
        self,
        provider: str,
        from_key: str,
        to_key: str,
        reason: str
    ):
        """Record an automated API key failover event"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "provider": provider,
            "from_key": from_key,
            "to_key": to_key,
            "reason": reason,
            "timestamp": now_str
        }
        with self._lock:
            self._failover_history.insert(0, entry)
            if len(self._failover_history) > 100:
                self._failover_history.pop()

        logger.warning(f"Key failover for [{provider}]: '{from_key}' -> '{to_key}' (Reason: {reason})")
        if self.event_bus:
            self.event_bus.emit("KEY_FAILOVER_TRIGGERED", entry)

    def get_failover_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent failover events"""
        with self._lock:
            return list(self._failover_history[:limit])

    def get_recent_requests(self, provider: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent API requests from buffer"""
        with self._lock:
            if provider:
                return [r for r in self._recent_requests if r["provider"] == provider][:limit]
            return list(self._recent_requests[:limit])

    def get_recent_errors(self, provider: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent API errors from buffer"""
        with self._lock:
            if provider:
                return [r for r in self._recent_errors if r["provider"] == provider][:limit]
            return list(self._recent_errors[:limit])

    def record_success(self, provider: str):
        """Record a successful live API response"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            h = self._health.setdefault(provider, {})
            old_status = h.get("status")
            h["status"] = HEALTH_CONNECTED
            h["last_success_at"] = now_str
            h["consecutive_errors"] = 0
            h["total_requests"] = h.get("total_requests", 0) + 1
            h["successful_requests"] = h.get("successful_requests", 0) + 1
            h["updated_at"] = now_str

            if old_status != HEALTH_CONNECTED:
                logger.info(f"Provider [{provider}] health status transitioned to {HEALTH_CONNECTED}")
                if self.event_bus:
                    self.event_bus.emit("PROVIDER_HEALTH_CHANGED", {"provider": provider, "status": HEALTH_CONNECTED})

    def record_error(self, provider: str, error_msg: str):
        """Record a network or server error"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            h = self._health.setdefault(provider, {})
            h["status"] = HEALTH_ERROR
            h["last_error_at"] = now_str
            h["last_error_message"] = str(error_msg)[:200]
            h["consecutive_errors"] = h.get("consecutive_errors", 0) + 1
            h["total_requests"] = h.get("total_requests", 0) + 1
            h["updated_at"] = now_str

            logger.warning(f"Provider [{provider}] health status transitioned to {HEALTH_ERROR}: {error_msg}")
            if self.event_bus:
                self.event_bus.emit("PROVIDER_HEALTH_CHANGED", {"provider": provider, "status": HEALTH_ERROR, "error": error_msg})

    def record_rate_limit(self, provider: str, cooldown_sec: float = 60.0):
        """Record rate limit hit (HTTP 429)"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            h = self._health.setdefault(provider, {})
            h["status"] = HEALTH_RATE_LIMITED
            h["last_error_at"] = now_str
            h["last_error_message"] = f"Rate limit reached. Cooldown {cooldown_sec:.0f}s"
            h["rate_limited_count"] = h.get("rate_limited_count", 0) + 1
            h["total_requests"] = h.get("total_requests", 0) + 1
            h["updated_at"] = now_str

            logger.warning(f"Provider [{provider}] health status transitioned to {HEALTH_RATE_LIMITED}")
            if self.event_bus:
                self.event_bus.emit("PROVIDER_HEALTH_CHANGED", {"provider": provider, "status": HEALTH_RATE_LIMITED, "cooldown": cooldown_sec})

    def record_auth_error(self, provider: str, error_msg: str = "Invalid API Key or unauthorized"):
        """Record 401/403 credential rejection"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            h = self._health.setdefault(provider, {})
            h["status"] = HEALTH_INVALID_KEY
            h["last_error_at"] = now_str
            h["last_error_message"] = str(error_msg)[:200]
            h["consecutive_errors"] = h.get("consecutive_errors", 0) + 1
            h["total_requests"] = h.get("total_requests", 0) + 1
            h["updated_at"] = now_str

            logger.error(f"Provider [{provider}] health status transitioned to {HEALTH_INVALID_KEY}: {error_msg}")
            if self.event_bus:
                self.event_bus.emit("PROVIDER_HEALTH_CHANGED", {"provider": provider, "status": HEALTH_INVALID_KEY, "error": error_msg})

    def set_disconnected(self, provider: str):
        """Mark provider disconnected when all keys are disabled or none exist"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            h = self._health.setdefault(provider, {})
            h["status"] = HEALTH_DISCONNECTED
            h["updated_at"] = now_str
            if self.event_bus:
                self.event_bus.emit("PROVIDER_HEALTH_CHANGED", {"provider": provider, "status": HEALTH_DISCONNECTED})

    def get_health(self, provider: str) -> Dict[str, Any]:
        """Get live health dictionary for specific provider"""
        with self._lock:
            return dict(self._health.get(provider, {
                "provider": provider,
                "status": HEALTH_DISCONNECTED,
                "last_success_at": None,
                "last_error_at": None,
                "last_error_message": "",
                "consecutive_errors": 0,
                "total_requests": 0,
                "successful_requests": 0,
                "rate_limited_count": 0,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }))

    def get_all_health(self) -> Dict[str, Dict[str, Any]]:
        """Get dictionary of health states for all providers"""
        with self._lock:
            return {p: dict(self._health[p]) for p in self._health}
