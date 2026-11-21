"""
M4DI~UciH4 Trading Intelligence System
Thread-Safe SQLite Database Manager
"""
import sqlite3
import threading
from pathlib import Path
from typing import List, Tuple, Any, Optional, Dict

from config.constants import DB_PATH
from database.schema import SCHEMA_SQL, DEFAULT_WATCHLISTS_DATA


class DatabaseManager:
    """Thread-safe SQLite Database Manager with Parameterized Execution"""

    _instance = None
    _singleton_lock = threading.Lock()

    def __new__(cls, db_path: Optional[Path] = None):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: Optional[Path] = None):
        if getattr(self, "_initialized", False):
            return
            
        self.db_path = db_path or DB_PATH
        self._lock = threading.Lock()
        self._local = threading.local()
        self._initialized = True
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize schema and seed data
        self.initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a thread-local SQLite connection with WAL enabled"""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False
            )
            # Enable Foreign Keys, WAL Mode, and High-Performance Pragmas
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA cache_size = -64000;")  # 64MB cache
            self._local.conn = conn
        return self._local.conn

    def initialize_database(self):
        """Run DDL scripts, migrate schema if needed, and seed defaults"""
        with self._lock:
            conn = self._get_connection()
            with conn:
                conn.executescript(SCHEMA_SQL)

            cur = conn.cursor()

            # Automatic Schema Migration for Phase 2: api_keys columns
            cur.execute("PRAGMA table_info(api_keys)")
            existing_cols = {row[1] for row in cur.fetchall()}

            phase2_columns = [
                ("priority", "INTEGER NOT NULL DEFAULT 1"),
                ("last_used_at", "TIMESTAMP"),
                ("last_success_at", "TIMESTAMP"),
                ("error_count", "INTEGER NOT NULL DEFAULT 0"),
                ("rate_limit_count", "INTEGER NOT NULL DEFAULT 0"),
                ("cooldown_until", "TIMESTAMP"),
                ("status", "TEXT NOT NULL DEFAULT 'UNTESTED'")
            ]

            with conn:
                for col_name, col_def in phase2_columns:
                    if col_name not in existing_cols:
                        cur.execute(f"ALTER TABLE api_keys ADD COLUMN {col_name} {col_def};")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_status ON api_keys(status);")

            # Automatic Schema Migration for Phase 6: watchlist_symbols notes & alerts
            cur.execute("PRAGMA table_info(watchlist_symbols)")
            wl_existing = {row[1] for row in cur.fetchall()}
            phase6_wl_cols = [
                ("notes", "TEXT"),
                ("alert_condition", "TEXT")
            ]
            with conn:
                for col_name, col_def in phase6_wl_cols:
                    if col_name not in wl_existing:
                        cur.execute(f"ALTER TABLE watchlist_symbols ADD COLUMN {col_name} {col_def};")

            # Seed provider_settings defaults if empty
            from config.constants import (
                PROVIDER_FINNHUB, PROVIDER_TWELVE_DATA, PROVIDER_NEWS_API,
                DEFAULT_PROVIDER_LIMITS, ROTATION_STRATEGY_PRIORITY
            )
            for prov, limits in DEFAULT_PROVIDER_LIMITS.items():
                cur.execute("SELECT COUNT(*) FROM provider_settings WHERE provider = ?", (prov,))
                if cur.fetchone()[0] == 0:
                    with conn:
                        cur.execute(
                            """
                            INSERT INTO provider_settings
                            (provider, rotation_strategy, rpm_limit, min_interval_sec, daily_limit, is_enabled)
                            VALUES (?, ?, ?, ?, ?, 1)
                            """,
                            (prov, ROTATION_STRATEGY_PRIORITY, limits["rpm"], limits["min_interval_sec"], limits.get("daily_limit"))
                        )

            # Seed default watchlists if table is empty
            cur.execute("SELECT COUNT(*) FROM watchlists")
            count = cur.fetchone()[0]
            if count == 0:
                with conn:
                    for name, desc, symbols in DEFAULT_WATCHLISTS_DATA:
                        cur.execute(
                            "INSERT INTO watchlists (name, description) VALUES (?, ?)",
                            (name, desc)
                        )
                        wid = cur.lastrowid
                        for sym, mkt in symbols:
                            cur.execute(
                                "INSERT INTO watchlist_symbols (watchlist_id, symbol, market) VALUES (?, ?, ?)",
                                (wid, sym, mkt)
                            )

    def execute(self, sql: str, params: Tuple = ()) -> int:
        """Execute a parameterized DML query (INSERT, UPDATE, DELETE). Returns lastrowid or rowcount"""
        with self._lock:
            conn = self._get_connection()
            with conn:
                cur = conn.cursor()
                cur.execute(sql, params)
                return cur.lastrowid if cur.lastrowid else cur.rowcount

    def executemany(self, sql: str, params_list: List[Tuple]) -> int:
        """Execute batch parameterized queries"""
        with self._lock:
            conn = self._get_connection()
            with conn:
                cur = conn.cursor()
                cur.executemany(sql, params_list)
                return cur.rowcount

    def fetchall(self, sql: str, params: Tuple = ()) -> List[Tuple]:
        """Fetch all rows matching parameterized query"""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()

    def fetchone(self, sql: str, params: Tuple = ()) -> Optional[Tuple]:
        """Fetch a single row matching parameterized query"""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.fetchone()

    def close(self):
        """Close thread connection safely"""
        if hasattr(self._local, "conn") and self._local.conn:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None
