"""
M4DI~UciH4 Trading Intelligence System
API Key Manager — Multi-Provider Key Lifecycle Management, Masking, and Health Audits
"""
from datetime import datetime
from typing import List, Dict, Optional, Any

from config.constants import API_PROVIDERS, PROVIDER_FINNHUB, PROVIDER_TWELVE_DATA, PROVIDER_NEWS_API
from security.encryption import mask_api_key, encrypt_secret, decrypt_secret
from core.logger import get_app_logger

logger = get_app_logger("ApiKeyManager")


class ApiKeyManager:
    """Manages API Key registration, encrypted local storage, priority, masking, and status toggles"""

    def __init__(self, db_manager, event_bus=None):
        self.db = db_manager
        self.event_bus = event_bus

    def add_key(
        self,
        provider: str,
        name: str,
        raw_key: str,
        is_active: bool = True,
        priority: int = 1
    ) -> int:
        """
        Add a new API key to the SQLite database.
        Raw key is encrypted prior to persistence, and a masked representation is saved.
        """
        if provider not in API_PROVIDERS:
            raise ValueError(f"Unsupported provider '{provider}'. Allowed: {API_PROVIDERS}")

        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Key Name cannot be empty")

        clean_key = raw_key.strip()
        if not clean_key:
            raise ValueError("API Key cannot be empty")

        clean_priority = max(1, min(int(priority), 10))
        encrypted = encrypt_secret(clean_key)
        masked = mask_api_key(clean_key)
        active_int = 1 if is_active else 0
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sql = """
        INSERT INTO api_keys (
            provider, name, key_encrypted, key_masked, is_active,
            priority, status, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, 'UNTESTED', ?, ?)
        """
        key_id = self.db.execute(
            sql,
            (provider, clean_name, encrypted, masked, active_int, clean_priority, now_str, now_str)
        )

        logger.info(f"Added API Key [ID: {key_id}] for {provider}: '{clean_name}' (Priority: {clean_priority}, Masked: {masked})")

        if self.event_bus:
            self.event_bus.emit("API_KEY_CHANGED", {"action": "add", "id": key_id, "provider": provider})

        return key_id

    def update_key(
        self,
        key_id: int,
        name: Optional[str] = None,
        raw_key: Optional[str] = None,
        is_active: Optional[bool] = None,
        priority: Optional[int] = None
    ) -> bool:
        """Update an existing API key entry"""
        existing = self.get_key_by_id(key_id)
        if not existing:
            return False

        fields = []
        params = []

        if name is not None:
            clean_name = name.strip()
            if not clean_name:
                raise ValueError("Key Name cannot be empty")
            fields.append("name = ?")
            params.append(clean_name)

        if raw_key is not None and raw_key.strip():
            clean_key = raw_key.strip()
            encrypted = encrypt_secret(clean_key)
            masked = mask_api_key(clean_key)
            fields.append("key_encrypted = ?")
            params.append(encrypted)
            fields.append("key_masked = ?")
            params.append(masked)
            fields.append("status = 'UNTESTED'")

        if is_active is not None:
            fields.append("is_active = ?")
            params.append(1 if is_active else 0)

        if priority is not None:
            clean_prio = max(1, min(int(priority), 10))
            fields.append("priority = ?")
            params.append(clean_prio)

        if not fields:
            return True

        fields.append("updated_at = ?")
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        params.append(key_id)

        sql = f"UPDATE api_keys SET {', '.join(fields)} WHERE id = ?"
        rows_affected = self.db.execute(sql, tuple(params))

        logger.info(f"Updated API Key [ID: {key_id}] for {existing['provider']}")

        if self.event_bus:
            self.event_bus.emit("API_KEY_CHANGED", {"action": "update", "id": key_id})

        return rows_affected > 0

    def delete_key(self, key_id: int) -> bool:
        """Delete an API key entry from SQLite"""
        existing = self.get_key_by_id(key_id)
        if not existing:
            return False

        sql = "DELETE FROM api_keys WHERE id = ?"
        rows_affected = self.db.execute(sql, (key_id,))

        logger.warning(f"Deleted API Key [ID: {key_id}] for {existing['provider']}: '{existing['name']}'")

        if self.event_bus:
            self.event_bus.emit("API_KEY_CHANGED", {"action": "delete", "id": key_id})

        return rows_affected > 0

    def toggle_key_status(self, key_id: int) -> bool:
        """Toggle active / disabled state of an API key"""
        existing = self.get_key_by_id(key_id)
        if not existing:
            return False

        new_status = not existing["is_active"]
        return self.update_key(key_id, is_active=new_status)

    def get_keys(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all API keys or filtered by provider with masked secrets and usage stats"""
        cols = """
        id, provider, name, key_masked, is_active, priority,
        last_used_at, last_success_at, error_count, rate_limit_count,
        cooldown_until, status, created_at, updated_at
        """
        if provider:
            sql = f"SELECT {cols} FROM api_keys WHERE provider = ? ORDER BY priority DESC, id ASC"
            rows = self.db.fetchall(sql, (provider,))
        else:
            sql = f"SELECT {cols} FROM api_keys ORDER BY provider ASC, priority DESC, id ASC"
            rows = self.db.fetchall(sql)

        result = []
        for r in rows:
            result.append({
                "id": r[0],
                "provider": r[1],
                "name": r[2],
                "masked_key": r[3],
                "is_active": bool(r[4]),
                "status_str": "Active" if r[4] else "Disabled",
                "priority": r[5] or 1,
                "last_used_at": r[6],
                "last_success_at": r[7],
                "error_count": r[8] or 0,
                "rate_limit_count": r[9] or 0,
                "cooldown_until": r[10],
                "status": r[11] or "UNTESTED",
                "created_at": r[12],
                "updated_at": r[13]
            })
        return result

    def get_key_by_id(self, key_id: int) -> Optional[Dict[str, Any]]:
        """Get single API key details by ID"""
        sql = """
        SELECT id, provider, name, key_masked, is_active, priority,
               last_used_at, last_success_at, error_count, rate_limit_count,
               cooldown_until, status, created_at, updated_at, key_encrypted
        FROM api_keys
        WHERE id = ?
        """
        row = self.db.fetchone(sql, (key_id,))
        if not row:
            return None
        return {
            "id": row[0],
            "provider": row[1],
            "name": row[2],
            "masked_key": row[3],
            "is_active": bool(row[4]),
            "status_str": "Active" if row[4] else "Disabled",
            "priority": row[5] or 1,
            "last_used_at": row[6],
            "last_success_at": row[7],
            "error_count": row[8] or 0,
            "rate_limit_count": row[9] or 0,
            "cooldown_until": row[10],
            "status": row[11] or "UNTESTED",
            "created_at": row[12],
            "updated_at": row[13],
            "key_encrypted": row[14]
        }

    def get_decrypted_key(self, key_id: int) -> Optional[str]:
        """Safely decrypt API secret for outgoing authenticated requests"""
        key_data = self.get_key_by_id(key_id)
        if not key_data:
            return None
        return decrypt_secret(key_data["key_encrypted"])

    def test_key_connection(self, key_id: int, app_context=None) -> Dict[str, Any]:
        """
        Execute an isolated test call against the external provider for this specific key.
        Returns result dict: {"success": bool, "message": str, "provider": str}
        """
        key_data = self.get_key_by_id(key_id)
        if not key_data:
            return {"success": False, "message": "Key not found in database", "provider": ""}

        raw_secret = self.get_decrypted_key(key_id)
        if not raw_secret:
            return {"success": False, "message": "Failed to decrypt secret", "provider": key_data["provider"]}

        provider = key_data["provider"]
        try:
            from api.finnhub_client import FinnhubClient
            from api.twelve_data_client import TwelveDataClient
            from api.newsapi_client import NewsApiClient

            if provider == PROVIDER_FINNHUB:
                client = app_context.finnhub if app_context else FinnhubClient()
                client.test_connection(override_api_key=raw_secret)
            elif provider == PROVIDER_TWELVE_DATA:
                client = app_context.twelve_data if app_context else TwelveDataClient()
                client.test_connection(override_api_key=raw_secret)
            elif provider == PROVIDER_NEWS_API:
                client = app_context.newsapi if app_context else NewsApiClient()
                client.test_connection(override_api_key=raw_secret)
            else:
                return {"success": False, "message": f"Unsupported provider {provider}", "provider": provider}

            # Update key success in SQLite
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.execute(
                "UPDATE api_keys SET status = 'HEALTHY', last_success_at = ?, last_used_at = ?, cooldown_until = NULL WHERE id = ?",
                (now_str, now_str, key_id)
            )
            if self.event_bus:
                self.event_bus.emit("API_KEY_STATUS_CHANGED", {"id": key_id, "status": "HEALTHY"})

            return {
                "success": True,
                "message": f"Connection verified successfully for {provider}!",
                "provider": provider
            }

        except Exception as e:
            err_msg = str(e)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "INVALID_KEY" if ("401" in err_msg or "403" in err_msg or "unauthorized" in err_msg.lower()) else "ERROR"
            self.db.execute(
                "UPDATE api_keys SET status = ?, error_count = error_count + 1, last_used_at = ? WHERE id = ?",
                (status, now_str, key_id)
            )
            if self.event_bus:
                self.event_bus.emit("API_KEY_STATUS_CHANGED", {"id": key_id, "status": status})

            return {
                "success": False,
                "message": f"Connection test failed: {err_msg}",
                "provider": provider
            }

    def count_summary(self) -> Dict[str, Any]:
        """Get summary statistics of configured API keys"""
        rows = self.db.fetchall("SELECT provider, is_active, COUNT(*) FROM api_keys GROUP BY provider, is_active")
        total = 0
        active_total = 0
        by_provider = {p: {"total": 0, "active": 0} for p in API_PROVIDERS}

        for p, is_act, cnt in rows:
            if p in by_provider:
                by_provider[p]["total"] += cnt
                if is_act:
                    by_provider[p]["active"] += cnt
            total += cnt
            if is_act:
                active_total += cnt

        return {
            "total_keys": total,
            "active_keys": active_total,
            "disabled_keys": total - active_total,
            "by_provider": by_provider
        }
