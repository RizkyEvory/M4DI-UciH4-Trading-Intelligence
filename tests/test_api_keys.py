"""
Unit Tests for API Key Management CRUD Operations
"""
import unittest
import tempfile
from pathlib import Path

from database.db_manager import DatabaseManager
from api.key_manager import ApiKeyManager
from core.event_bus import EventBus


class TestApiKeys(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_api_keys.db"
        
        DatabaseManager._instance = None
        EventBus._instance = None
        
        self.db = DatabaseManager(self.db_path)
        self.events = EventBus()
        self.api_mgr = ApiKeyManager(self.db, self.events)

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()
        DatabaseManager._instance = None
        EventBus._instance = None

    def test_add_and_get_keys_multiple_per_provider(self):
        """Verify multiple keys can be registered under the same provider"""
        k1_id = self.api_mgr.add_key("Finnhub", "Finnhub Key 1", "fh_secret_alpha_12345", is_active=True)
        k2_id = self.api_mgr.add_key("Finnhub", "Finnhub Key 2", "fh_secret_beta_67890", is_active=False)
        k3_id = self.api_mgr.add_key("Twelve Data", "Twelve Data Key 1", "td_live_key_554433", is_active=True)

        self.assertGreater(k1_id, 0)
        self.assertGreater(k2_id, 0)
        self.assertGreater(k3_id, 0)

        # Check Finnhub keys filter
        fh_keys = self.api_mgr.get_keys("Finnhub")
        self.assertEqual(len(fh_keys), 2)
        names = [k["name"] for k in fh_keys]
        self.assertIn("Finnhub Key 1", names)
        self.assertIn("Finnhub Key 2", names)

        # Check all keys
        all_keys = self.api_mgr.get_keys()
        self.assertEqual(len(all_keys), 3)

    def test_update_key(self):
        """Verify updating key name, status, and raw secret"""
        kid = self.api_mgr.add_key("NewsAPI.org", "NewsAPI Key 1", "news_init_token_111", is_active=True)

        # Update name and status
        success = self.api_mgr.update_key(kid, name="NewsAPI Key Primary", is_active=False)
        self.assertTrue(success)

        updated = self.api_mgr.get_key_by_id(kid)
        self.assertEqual(updated["name"], "NewsAPI Key Primary")
        self.assertFalse(updated["is_active"])

    def test_toggle_key_status(self):
        """Verify toggling active status"""
        kid = self.api_mgr.add_key("Twelve Data", "TD Toggle Test", "td_secret_key_998877", is_active=True)
        
        self.api_mgr.toggle_key_status(kid)
        k = self.api_mgr.get_key_by_id(kid)
        self.assertFalse(k["is_active"])

        self.api_mgr.toggle_key_status(kid)
        k = self.api_mgr.get_key_by_id(kid)
        self.assertTrue(k["is_active"])

    def test_delete_key(self):
        """Verify deleting an API key"""
        kid = self.api_mgr.add_key("Finnhub", "To Delete", "secret_to_delete_000")
        self.assertIsNotNone(self.api_mgr.get_key_by_id(kid))

        deleted = self.api_mgr.delete_key(kid)
        self.assertTrue(deleted)
        self.assertIsNone(self.api_mgr.get_key_by_id(kid))

    def test_summary_counting(self):
        """Verify count summary calculations"""
        self.api_mgr.add_key("Finnhub", "K1", "secret1", is_active=True)
        self.api_mgr.add_key("Finnhub", "K2", "secret2", is_active=False)
        self.api_mgr.add_key("Twelve Data", "K3", "secret3", is_active=True)

        summary = self.api_mgr.count_summary()
        self.assertEqual(summary["total_keys"], 3)
        self.assertEqual(summary["active_keys"], 2)
        self.assertEqual(summary["disabled_keys"], 1)
        self.assertEqual(summary["by_provider"]["Finnhub"]["total"], 2)
        self.assertEqual(summary["by_provider"]["Finnhub"]["active"], 1)


if __name__ == "__main__":
    unittest.main()
