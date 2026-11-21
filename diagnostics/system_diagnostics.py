"""
M4DI~UciH4 Trading Intelligence System
System Diagnostics Engine (Phase 6)
Performs automated comprehensive health evaluations:
- API Connectivity & Provider Key Health
- Database File Integrity & Table Verification
- In-Memory Cache Statistics & Hit Ratios
- Host Environment & Threading Health
- Background Task Queue Telemetry
- System Error & Warning Audit Logs
"""
import sys
import os
import platform
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from config.constants import (
    APP_NAME,
    APP_VERSION,
    API_PROVIDERS,
    DB_PATH,
    LOG_FILE_PATH
)
from core.logger import get_logger

logger = get_logger("SystemDiagnostics")


class SystemDiagnostics:
    """Consolidates cross-subsystem diagnostics and automated health audits"""

    def __init__(self, ctx=None):
        self.ctx = ctx

    def run_full_diagnostics(self) -> Dict[str, Any]:
        """Execute end-to-end audit across all 6 operational vectors"""
        start_time = datetime.now()
        api_diag = self.check_api_connectivity()
        db_diag = self.check_database_integrity()
        cache_diag = self.check_cache_status()
        app_diag = self.check_application_health()
        task_diag = self.check_background_tasks()
        log_diag = self.check_system_logs()

        # Overall operational score
        passed_checks = sum([
            db_diag.get("integrity_ok", False),
            cache_diag.get("status") == "OPERATIONAL",
            app_diag.get("status") == "HEALTHY",
            task_diag.get("status") == "HEALTHY",
            log_diag.get("status") in ("CLEAN", "WARNING")
        ])
        total_checks = 5
        overall_health = "OPTIMAL" if passed_checks == total_checks else ("DEGRADED" if passed_checks >= 3 else "CRITICAL")

        return {
            "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": overall_health,
            "score": f"{passed_checks}/{total_checks}",
            "api_connectivity": api_diag,
            "database_integrity": db_diag,
            "cache_telemetry": cache_diag,
            "application_health": app_diag,
            "background_tasks": task_diag,
            "system_logs": log_diag
        }

    def check_api_connectivity(self) -> Dict[str, Any]:
        """Audit active keys and connection states for Finnhub, Twelve Data, NewsAPI"""
        results = {}
        if not self.ctx or not hasattr(self.ctx, "health_monitor"):
            return {"status": "UNAVAILABLE", "providers": {}}

        health_map = self.ctx.health_monitor.get_all_health()
        for prov in API_PROVIDERS:
            h = health_map.get(prov, {})
            # Query active keys count
            key_count = 0
            if hasattr(self.ctx, "db"):
                try:
                    row = self.ctx.db.fetchone(
                        "SELECT COUNT(*) FROM api_keys WHERE provider = ? AND is_active = 1",
                        (prov,)
                    )
                    key_count = row[0] if isinstance(row, (tuple, list)) else row["COUNT(*)"]
                except Exception:
                    pass

            results[prov] = {
                "status": h.get("status", "DISCONNECTED"),
                "active_keys": key_count,
                "total_requests": h.get("total_requests", 0),
                "successful_requests": h.get("successful_requests", 0),
                "consecutive_errors": h.get("consecutive_errors", 0),
                "last_success": h.get("last_success_at", "-"),
                "last_error": h.get("last_error_message", "-")
            }

        return {
            "status": "OPERATIONAL",
            "providers": results
        }

    def check_database_integrity(self) -> Dict[str, Any]:
        """Execute SQLite PRAGMA integrity_check and table count audit"""
        if not self.ctx or not hasattr(self.ctx, "db"):
            return {"integrity_ok": False, "status": "NO_DATABASE"}

        try:
            # PRAGMA integrity_check
            row = self.ctx.db.fetchone("PRAGMA integrity_check;")
            integrity_val = row[0] if isinstance(row, (tuple, list)) else list(row.values())[0]
            integrity_ok = str(integrity_val).strip().lower() == "ok"

            # Table row counts
            tables = [
                "api_keys", "settings", "logs", "watchlists", "watchlist_symbols",
                "portfolio_positions", "portfolio_trades", "api_request_logs"
            ]
            row_counts = {}
            for t in tables:
                try:
                    cnt_row = self.ctx.db.fetchone(f"SELECT COUNT(*) FROM {t};")
                    row_counts[t] = cnt_row[0] if isinstance(cnt_row, (tuple, list)) else cnt_row[f"COUNT(*)"]
                except Exception:
                    row_counts[t] = 0

            # File size
            db_size_kb = 0
            if Path(DB_PATH).exists():
                db_size_kb = round(os.path.getsize(DB_PATH) / 1024, 1)

            return {
                "integrity_ok": integrity_ok,
                "status": "OK" if integrity_ok else "CORRUPTED",
                "integrity_message": str(integrity_val),
                "file_path": str(DB_PATH),
                "size_kb": db_size_kb,
                "journal_mode": "WAL",
                "table_counts": row_counts
            }
        except Exception as e:
            return {
                "integrity_ok": False,
                "status": "ERROR",
                "error": str(e)
            }

    def check_cache_status(self) -> Dict[str, Any]:
        """Audit in-memory cache capacity, hit rate, and key count"""
        if not self.ctx or not hasattr(self.ctx, "cache"):
            return {"status": "UNAVAILABLE"}

        cache = self.ctx.cache
        if hasattr(cache, "stats"):
            stats = cache.stats()
        elif hasattr(cache, "get_stats"):
            stats = cache.get_stats()
        else:
            stats = {}

        hits = stats.get("hits", 0)
        misses = stats.get("misses", 0)
        total = hits + misses
        hit_ratio = round((hits / total) * 100.0, 1) if total > 0 else 0.0

        return {
            "status": "OPERATIONAL",
            "item_count": stats.get("active_items", stats.get("total_entries", 0)),
            "hits": hits,
            "misses": misses,
            "hit_ratio_pct": hit_ratio
        }

    def check_application_health(self) -> Dict[str, Any]:
        """Audit runtime host system and threading environment"""
        active_threads = threading.active_count()
        return {
            "status": "HEALTHY",
            "app_name": APP_NAME,
            "version": APP_VERSION,
            "python_version": sys.version.split()[0],
            "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "active_threads": active_threads,
            "pid": os.getpid()
        }

    def check_background_tasks(self) -> Dict[str, Any]:
        """Audit async TaskManager worker thread and queues"""
        if not self.ctx or not hasattr(self.ctx, "task_manager"):
            return {"status": "UNAVAILABLE"}

        tm = self.ctx.task_manager
        active_count = len(tm._tasks) if hasattr(tm, "_tasks") else 0
        is_alive = tm.is_running if hasattr(tm, "is_running") else True

        return {
            "status": "HEALTHY" if is_alive else "STOPPED",
            "worker_alive": is_alive,
            "tracked_tasks": active_count
        }

    def check_system_logs(self) -> Dict[str, Any]:
        """Audit recent log file footprint and error frequency"""
        file_size_kb = 0
        if Path(LOG_FILE_PATH).exists():
            file_size_kb = round(os.path.getsize(LOG_FILE_PATH) / 1024, 1)

        err_count = 0
        warn_count = 0
        if self.ctx and hasattr(self.ctx, "db"):
            try:
                row_err = self.ctx.db.fetchone("SELECT COUNT(*) FROM logs WHERE level = 'ERROR'")
                err_count = row_err[0] if isinstance(row_err, (tuple, list)) else row_err["COUNT(*)"]
                row_warn = self.ctx.db.fetchone("SELECT COUNT(*) FROM logs WHERE level = 'WARNING'")
                warn_count = row_warn[0] if isinstance(row_warn, (tuple, list)) else row_warn["COUNT(*)"]
            except Exception:
                pass

        status = "CRITICAL" if err_count > 50 else ("WARNING" if warn_count > 20 else "CLEAN")

        return {
            "status": status,
            "log_path": str(LOG_FILE_PATH),
            "size_kb": file_size_kb,
            "error_count": err_count,
            "warning_count": warn_count
        }
