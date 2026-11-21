"""
M4DI~UciH4 Trading Intelligence System
Advanced API Management & Telemetry Unit Tests (Phase 6)
Verifies request logging into memory ring buffer & database, failover tracking,
and error telemetry.
"""
import unittest
import tempfile
from pathlib import Path

from config.constants import PROVIDER_FINNHUB, PROVIDER_TWELVE_DATA
from database.db_manager import DatabaseManager
from api.health_monitor import ProviderHealthMonitor


class TestAdvancedApiManagement(unittest.TestCase):
    """Test suite for advanced API telemetry and failover tracking"""

    def setUp(self):
        DatabaseManager._instance = None
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_api_mgmt.db"
        self.db = DatabaseManager(self.db_path)
        self.hm = ProviderHealthMonitor(event_bus=None, db=self.db)

    def tearDown(self):
        try:
            self.db.close()
            self.temp_dir.cleanup()
        except Exception:
            pass
        DatabaseManager._instance = None

    def test_record_request_and_history(self):
        # Record success
        self.hm.record_request(
            provider=PROVIDER_FINNHUB,
            endpoint="quote?symbol=AAPL",
            status_code=200,
            is_success=True,
            response_time_ms=125.4,
            key_id=1
        )

        # Record error
        self.hm.record_request(
            provider=PROVIDER_TWELVE_DATA,
            endpoint="time_series?symbol=XAU/USD",
            status_code=429,
            is_success=False,
            response_time_ms=88.2,
            error_message="Rate limit 429",
            key_id=2
        )

        # Retrieve from memory buffer
        reqs = self.hm.get_recent_requests()
        self.assertEqual(len(reqs), 2)
        self.assertEqual(reqs[0]["provider"], PROVIDER_TWELVE_DATA)
        self.assertEqual(reqs[1]["provider"], PROVIDER_FINNHUB)

        errors = self.hm.get_recent_errors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["status_code"], 429)

        # Retrieve from database
        db_rows = self.db.fetchall("SELECT provider, status_code, is_success FROM api_request_logs ORDER BY id ASC")
        self.assertEqual(len(db_rows), 2)
        self.assertEqual(db_rows[0][0], PROVIDER_FINNHUB)
        self.assertEqual(db_rows[0][1], 200)

    def test_record_failover_history(self):
        self.hm.record_failover(
            provider=PROVIDER_FINNHUB,
            from_key="Key 1 (Primary)",
            to_key="Key 2 (Backup)",
            reason="Rate limit HTTP 429 hit"
        )

        fos = self.hm.get_failover_history()
        self.assertEqual(len(fos), 1)
        self.assertEqual(fos[0]["from_key"], "Key 1 (Primary)")
        self.assertEqual(fos[0]["to_key"], "Key 2 (Backup)")
        self.assertIn("Rate limit", fos[0]["reason"])


if __name__ == "__main__":
    unittest.main()
