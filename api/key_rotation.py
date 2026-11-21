"""
M4DI~UciH4 Trading Intelligence System
Intelligent Multi-Key Rotation Manager
Implements Priority, Round-Robin, Least-Used, and Failover strategies with cooldowns.
"""
import time
import threading
from datetime import datetime
from typing import List, Dict, Optional, Any

from config.constants import (
    API_PROVIDERS,
    ROTATION_STRATEGY_PRIORITY,
    ROTATION_STRATEGY_ROUND_ROBIN,
    ROTATION_STRATEGY_LEAST_USED,
    ROTATION_STRATEGY_FAILOVER,
    ROTATION_STRATEGIES
)
from security.encryption import decrypt_secret
from core.logger import get_app_logger

logger = get_app_logger("KeyRotation")


class KeyRotationManager:
    """
    Manages multi-key selection and intelligent failover per API provider.
    Maintains cooldown status, request metrics, and respects provider rate quotas.
    """

    def __init__(self, db_manager, event_bus=None, health_monitor=None):
        self.db = db_manager
        self.event_bus = event_bus
        self.health_monitor = health_monitor
        self._lock = threading.RLock()
        self._rr_indices: Dict[str, int] = {p: 0 for p in API_PROVIDERS}

    def get_strategy(self, provider: str) -> str:
        """Get configured rotation strategy for provider"""
        row = self.db.fetchone("SELECT rotation_strategy FROM provider_settings WHERE provider = ?", (provider,))
        if row and row[0] in ROTATION_STRATEGIES:
            return row[0]
        return ROTATION_STRATEGY_PRIORITY

    def set_strategy(self, provider: str, strategy: str) -> bool:
        """Update rotation strategy for provider"""
        if strategy not in ROTATION_STRATEGIES:
            raise ValueError(f"Invalid strategy '{strategy}'. Allowed: {ROTATION_STRATEGIES}")
        sql = """
        INSERT INTO provider_settings (provider, rotation_strategy, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(provider) DO UPDATE SET rotation_strategy = excluded.rotation_strategy, updated_at = CURRENT_TIMESTAMP
        """
        self.db.execute(sql, (provider, strategy))
        logger.info(f"Updated rotation strategy for [{provider}] to '{strategy}'")
        if self.event_bus:
            self.event_bus.emit("ROTATION_STRATEGY_CHANGED", {"provider": provider, "strategy": strategy})
        return True

    def get_eligible_keys(self, provider: str) -> List[Dict[str, Any]]:
        """
        Retrieve all active API keys for provider that are NOT currently in cooldown.
        Returns list of key dictionaries.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        SELECT id, provider, name, key_encrypted, key_masked, is_active,
               priority, last_used_at, last_success_at, error_count,
               rate_limit_count, cooldown_until, status
        FROM api_keys
        WHERE provider = ? AND is_active = 1
        """
        rows = self.db.fetchall(sql, (provider,))
        eligible = []
        for r in rows:
            cooldown_target = r[11]
            # Check cooldown
            if cooldown_target and cooldown_target > now_str:
                # Key is currently in cooldown; skip for active selection
                continue

            # Don't pick keys verified as INVALID_KEY
            if r[12] == "INVALID_KEY":
                continue

            eligible.append({
                "id": r[0],
                "provider": r[1],
                "name": r[2],
                "key_encrypted": r[3],
                "key_masked": r[4],
                "is_active": bool(r[5]),
                "priority": r[6],
                "last_used_at": r[7],
                "last_success_at": r[8],
                "error_count": r[9],
                "rate_limit_count": r[10],
                "cooldown_until": r[11],
                "status": r[12]
            })
        return eligible

    def select_key(self, provider: str, strategy: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Select the best API key candidate according to provider's configured strategy.
        """
        with self._lock:
            strat = strategy or self.get_strategy(provider)
            candidates = self.get_eligible_keys(provider)

            if not candidates:
                return None

            if strat == ROTATION_STRATEGY_PRIORITY:
                # Order by priority descending (higher number = higher priority), then least errors
                candidates.sort(key=lambda k: (-k["priority"], k["error_count"], k["id"]))
                return candidates[0]

            elif strat == ROTATION_STRATEGY_ROUND_ROBIN:
                idx = self._rr_indices.get(provider, 0)
                selected = candidates[idx % len(candidates)]
                self._rr_indices[provider] = (idx + 1) % len(candidates)
                return selected

            elif strat == ROTATION_STRATEGY_LEAST_USED:
                # Pick key with oldest last_used_at (None comes first), lowest error count
                def sort_least_used(k):
                    used_ts = k["last_used_at"] or "1970-01-01 00:00:00"
                    return (used_ts, k["error_count"], -k["priority"])
                candidates.sort(key=sort_least_used)
                return candidates[0]

            elif strat == ROTATION_STRATEGY_FAILOVER:
                # Primary key is highest priority. Only falls back if errors > 0
                candidates.sort(key=lambda k: (k["error_count"], -k["priority"], k["id"]))
                return candidates[0]

            # Default fallback
            return candidates[0]

    def get_key_for_request(self, provider: str) -> Optional[Dict[str, Any]]:
        """
        Select candidate key and decrypt raw token for HTTP request.
        """
        candidate = self.select_key(provider)
        if not candidate:
            return None

        try:
            raw_key = decrypt_secret(candidate["key_encrypted"])
            candidate["raw_key"] = raw_key
            return candidate
        except Exception as e:
            logger.error(f"Failed to decrypt API key [ID: {candidate['id']}]: {e}")
            self.record_key_error(candidate["id"], error_msg=f"Decryption failure: {e}", cooldown_sec=300)
            return None

    def record_key_success(self, key_id: int):
        """Update metrics on successful HTTP 200 response"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        UPDATE api_keys
        SET last_success_at = ?,
            last_used_at = ?,
            status = 'HEALTHY',
            cooldown_until = NULL,
            error_count = MAX(0, error_count - 1),
            updated_at = ?
        WHERE id = ?
        """
        self.db.execute(sql, (now_str, now_str, now_str, key_id))
        if self.event_bus:
            self.event_bus.emit("API_KEY_STATUS_CHANGED", {"id": key_id, "status": "HEALTHY"})

    def record_key_rate_limit(self, key_id: int, cooldown_sec: int = 60):
        """Mark key rate limited (HTTP 429) and place in cooldown"""
        now = time.time()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cooldown_str = datetime.fromtimestamp(now + cooldown_sec).strftime("%Y-%m-%d %H:%M:%S")

        sql = """
        UPDATE api_keys
        SET rate_limit_count = rate_limit_count + 1,
            cooldown_until = ?,
            last_used_at = ?,
            status = 'RATE_LIMITED',
            updated_at = ?
        WHERE id = ?
        """
        self.db.execute(sql, (cooldown_str, now_str, now_str, key_id))
        logger.warning(f"API Key [ID: {key_id}] placed in cooldown until {cooldown_str} ({cooldown_sec}s)")
        if self.event_bus:
            self.event_bus.emit("API_KEY_STATUS_CHANGED", {"id": key_id, "status": "RATE_LIMITED", "cooldown": cooldown_str})

    def record_key_auth_error(self, key_id: int):
        """Mark key as unauthorized or invalid credential (HTTP 401/403)"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        UPDATE api_keys
        SET error_count = error_count + 1,
            last_used_at = ?,
            status = 'INVALID_KEY',
            updated_at = ?
        WHERE id = ?
        """
        self.db.execute(sql, (now_str, now_str, key_id))
        logger.error(f"API Key [ID: {key_id}] marked INVALID_KEY (HTTP 401/403)")
        if self.event_bus:
            self.event_bus.emit("API_KEY_STATUS_CHANGED", {"id": key_id, "status": "INVALID_KEY"})

    def record_key_error(self, key_id: int, error_msg: str = "", cooldown_sec: int = 15):
        """Mark generic failure / timeout / 5xx error and brief cooldown"""
        now = time.time()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cooldown_str = datetime.fromtimestamp(now + cooldown_sec).strftime("%Y-%m-%d %H:%M:%S")

        sql = """
        UPDATE api_keys
        SET error_count = error_count + 1,
            cooldown_until = ?,
            last_used_at = ?,
            status = 'ERROR',
            updated_at = ?
        WHERE id = ?
        """
        self.db.execute(sql, (cooldown_str, now_str, now_str, key_id))
        logger.warning(f"API Key [ID: {key_id}] recorded error: {error_msg}")
        if self.event_bus:
            self.event_bus.emit("API_KEY_STATUS_CHANGED", {"id": key_id, "status": "ERROR"})
