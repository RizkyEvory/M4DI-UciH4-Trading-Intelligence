"""
M4DI~UciH4 Trading Intelligence System
Provider-Aware Rate Limit Manager & Exponential Backoff Engine
Enforces sliding-window RPM, inter-request intervals, cooldowns, and capped retries.
"""
import time
import math
import random
import threading
from typing import Dict, List, Optional, Tuple, Any

from config.constants import (
    PROVIDER_FINNHUB, PROVIDER_TWELVE_DATA, PROVIDER_NEWS_API, DEFAULT_PROVIDER_LIMITS
)
from core.logger import get_app_logger

logger = get_app_logger("RateLimiter")


class RateLimitManager:
    """
    Thread-safe Rate Limit Manager for API providers.
    Prevents HTTP 429 quota exhaustion with sliding window and pacing throttles.
    """

    def __init__(self, limits_config: Optional[Dict[str, Dict[str, Any]]] = None):
        self._lock = threading.RLock()
        self.limits: Dict[str, Dict[str, Any]] = limits_config or {
            k: dict(v) for k, v in DEFAULT_PROVIDER_LIMITS.items()
        }
        # provider -> list of monotonic timestamps for requests in last 60 seconds
        self._request_history: Dict[str, List[float]] = {p: [] for p in self.limits}
        # provider -> float timestamp of most recent outbound request
        self._last_request_time: Dict[str, float] = {p: 0.0 for p in self.limits}
        # provider -> float timestamp until which the provider is cooled down
        self._cooldown_until: Dict[str, float] = {p: 0.0 for p in self.limits}

    def update_provider_limit(self, provider: str, rpm: int, min_interval_sec: float):
        """Dynamically update rate limit parameters for a provider"""
        with self._lock:
            if provider not in self.limits:
                self.limits[provider] = {}
            self.limits[provider]["rpm"] = max(1, rpm)
            self.limits[provider]["min_interval_sec"] = max(0.05, min_interval_sec)

    def is_in_cooldown(self, provider: str) -> Tuple[bool, float]:
        """Check if provider is under active temporary cooldown. Returns (is_cooling, remaining_seconds)"""
        now = time.time()
        with self._lock:
            cooldown_target = self._cooldown_until.get(provider, 0.0)
            if cooldown_target > now:
                remaining = cooldown_target - now
                return True, round(remaining, 2)
            return False, 0.0

    def set_cooldown(self, provider: str, duration_seconds: float):
        """Put provider into cooldown (e.g. after HTTP 429)"""
        with self._lock:
            now = time.time()
            self._cooldown_until[provider] = max(self._cooldown_until.get(provider, 0.0), now + duration_seconds)
            logger.warning(f"Provider [{provider}] placed in cooldown for {duration_seconds:.1f}s")

    def clear_cooldown(self, provider: str):
        """Manually clear cooldown for provider"""
        with self._lock:
            self._cooldown_until[provider] = 0.0

    def can_request(self, provider: str) -> Tuple[bool, float]:
        """
        Check if an outbound call is permitted right now.
        Returns: (allowed: bool, wait_time_seconds: float)
        """
        now = time.time()
        with self._lock:
            # 1. Check cooldown
            is_cooling, remaining = self.is_in_cooldown(provider)
            if is_cooling:
                return False, remaining

            config = self.limits.get(provider, {"rpm": 60, "min_interval_sec": 1.0})
            rpm = config.get("rpm", 60)
            min_interval = config.get("min_interval_sec", 1.0)

            # 2. Check minimum pacing interval
            last_req = self._last_request_time.get(provider, 0.0)
            elapsed_since_last = now - last_req
            if elapsed_since_last < min_interval:
                interval_wait = min_interval - elapsed_since_last
                return False, round(interval_wait, 3)

            # 3. Check sliding window requests in the last 60 seconds
            history = self._request_history.setdefault(provider, [])
            cutoff = now - 60.0
            # Prune old timestamps
            while history and history[0] <= cutoff:
                history.pop(0)

            if len(history) >= rpm:
                # Need to wait until the oldest request in the window expires past 60s
                window_wait = 60.0 - (now - history[0]) + 0.05
                return False, round(max(0.05, window_wait), 3)

            return True, 0.0

    def acquire_permit(self, provider: str, timeout_sec: float = 15.0) -> bool:
        """
        Block and throttle until a permit is granted, or timeout occurs.
        Returns True if permit granted, False if timed out.
        """
        start_time = time.time()
        while True:
            allowed, wait_sec = self.can_request(provider)
            if allowed:
                self.record_request(provider)
                return True

            elapsed = time.time() - start_time
            if elapsed + wait_sec > timeout_sec:
                logger.warning(f"RateLimit acquire_permit timed out for [{provider}] (needed {wait_sec:.2f}s, timeout={timeout_sec}s)")
                return False

            sleep_dur = min(wait_sec, 1.0)
            time.sleep(sleep_dur)

    def record_request(self, provider: str):
        """Register that a request was sent to provider"""
        now = time.time()
        with self._lock:
            history = self._request_history.setdefault(provider, [])
            history.append(now)
            self._last_request_time[provider] = now

    @staticmethod
    def calculate_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 16.0, factor: float = 2.0) -> float:
        """
        Calculate exponential backoff with mild jitter to prevent thundering herd.
        Capped at max_delay.
        """
        delay = min(max_delay, base_delay * (factor ** attempt))
        # Add 10% random jitter
        jitter = random.uniform(0.0, 0.1 * delay)
        return round(delay + jitter, 2)

    def get_provider_status(self, provider: str) -> Dict[str, Any]:
        """Return rate limit health statistics for UI display"""
        now = time.time()
        with self._lock:
            history = self._request_history.get(provider, [])
            cutoff = now - 60.0
            active_calls = sum(1 for ts in history if ts > cutoff)
            config = self.limits.get(provider, {"rpm": 60, "min_interval_sec": 1.0})
            is_cooling, rem_cooldown = self.is_in_cooldown(provider)

            return {
                "provider": provider,
                "active_calls_last_min": active_calls,
                "rpm_limit": config.get("rpm", 60),
                "min_interval_sec": config.get("min_interval_sec", 1.0),
                "is_rate_limited": is_cooling,
                "remaining_cooldown_sec": rem_cooldown,
                "last_call_timestamp": self._last_request_time.get(provider, 0.0)
            }
