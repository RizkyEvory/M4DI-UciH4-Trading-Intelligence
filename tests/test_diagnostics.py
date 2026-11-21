"""
M4DI~UciH4 Trading Intelligence System
Diagnostics Unit Tests (Phase 6)
Verifies automated system audits: database integrity, in-memory cache status,
application runtime health, background worker status, and audit logs.
"""
import unittest
import tempfile
from pathlib import Path

from database.db_manager import DatabaseManager
from api.cache import ResponseCache
from core.task_manager import TaskManager
from diagnostics.system_diagnostics import SystemDiagnostics


class DummyContext:
    def __init__(self, db, cache, task_manager):
        self.db = db
        self.cache = cache
        self.task_manager = task_manager


class TestSystemDiagnostics(unittest.TestCase):
    """Test suite for SystemDiagnostics engine"""

    def setUp(self):
        DatabaseManager._instance = None
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_diag.db"
        self.db = DatabaseManager(self.db_path)
        self.cache = ResponseCache()
        self.tm = TaskManager()
        self.ctx = DummyContext(self.db, self.cache, self.tm)
        self.diag = SystemDiagnostics(self.ctx)

    def tearDown(self):
        try:
            self.db.close()
            self.temp_dir.cleanup()
        except Exception:
            pass
        DatabaseManager._instance = None

    def test_database_integrity_check(self):
        res = self.diag.check_database_integrity()
        self.assertTrue(res["integrity_ok"])
        self.assertEqual(res["status"], "OK")
        self.assertEqual(res["integrity_message"], "ok")
        self.assertIn("table_counts", res)

    def test_cache_telemetry_check(self):
        self.cache.set("k1", "v1", ttl_seconds=60)
        _ = self.cache.get("k1")  # Hit
        _ = self.cache.get("k2")  # Miss

        res = self.diag.check_cache_status()
        self.assertEqual(res["status"], "OPERATIONAL")
        self.assertEqual(res["hits"], 1)
        self.assertEqual(res["misses"], 1)
        self.assertEqual(res["hit_ratio_pct"], 50.0)

    def test_application_health(self):
        res = self.diag.check_application_health()
        self.assertEqual(res["status"], "HEALTHY")
        self.assertIn("python_version", res)
        self.assertIn("active_threads", res)

    def test_run_full_diagnostics(self):
        full = self.diag.run_full_diagnostics()
        self.assertIn("overall_status", full)
        self.assertIn("database_integrity", full)
        self.assertIn("cache_telemetry", full)
        self.assertIn("score", full)


if __name__ == "__main__":
    unittest.main()
