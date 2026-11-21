"""
M4DI~UciH4 Trading Intelligence System
Settings Manager for User Preferences & System Configuration
"""
import threading
from typing import Dict, Any, Optional

DEFAULT_SETTINGS: Dict[str, str] = {
    "theme": "Dark Charcoal (Default)",
    "app_title": "M4DI~UciH4 Trading Intelligence",
    "default_timeframe": "M5",
    "default_market": "Commodities (XAUUSD / Gold & Metals)",
    "default_watchlist": "Gold & Metals",
    "refresh_interval_sec": "15",
    "background_threads": "4",
    "sound_notifications": "True",
    "popup_notifications": "True",
    "log_level": "INFO",
    "max_log_rows": "500",
    "window_geometry": "1280x820",
    "startup_page": "Dashboard",
    "auto_start_scanner": "False"
}

class SettingsManager:
    """Thread-safe Settings Manager with SQLite Persistence"""

    def __init__(self, db_manager=None):
        self._db = db_manager
        self._lock = threading.Lock()
        self._cache: Dict[str, str] = dict(DEFAULT_SETTINGS)

    def set_db_manager(self, db_manager):
        """Inject DatabaseManager reference once initialized"""
        with self._lock:
            self._db = db_manager
        self.load_all()

    def load_all(self) -> Dict[str, str]:
        """Load all settings from the database into memory cache"""
        with self._lock:
            if not self._db:
                return dict(self._cache)
            try:
                rows = self._db.fetchall("SELECT key, value FROM settings")
                for key, val in rows:
                    self._cache[key] = val
            except Exception as e:
                # If table doesn't exist yet, retain defaults
                pass
            return dict(self._cache)

    def get(self, key: str, default: Optional[str] = None) -> str:
        """Get a setting value by key"""
        with self._lock:
            if default is not None:
                return self._cache.get(key, default)
            return self._cache.get(key, DEFAULT_SETTINGS.get(key, ""))

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a setting as boolean"""
        val = self.get(key, str(default))
        return val.lower() in ("true", "1", "yes")

    def get_int(self, key: str, default: int = 0) -> int:
        """Get a setting as integer"""
        try:
            return int(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default

    def set(self, key: str, value: Any, persist: bool = True):
        """Set a single setting in cache and optionally persist to SQLite"""
        str_val = str(value)
        with self._lock:
            self._cache[key] = str_val
            if persist and self._db:
                try:
                    self._db.execute(
                        "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
                        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
                        (key, str_val)
                    )
                except Exception:
                    pass

    def save_bulk(self, new_settings: Dict[str, Any]):
        """Save multiple settings in a single transaction"""
        with self._lock:
            for k, v in new_settings.items():
                self._cache[k] = str(v)
            if self._db:
                for k, v in new_settings.items():
                    self._db.execute(
                        "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
                        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
                        (k, str(v))
                    )

    def reset_to_defaults(self):
        """Reset all settings back to default values"""
        self.save_bulk(DEFAULT_SETTINGS)
