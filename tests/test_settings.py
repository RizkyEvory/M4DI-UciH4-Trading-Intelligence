"""
Unit Tests for Settings Management and Persistence
"""
import unittest
import tempfile
from pathlib import Path

from database.db_manager import DatabaseManager
from config.settings import SettingsManager


class TestSettings(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_settings.db"
        
        DatabaseManager._instance = None
        self.db = DatabaseManager(self.db_path)
        self.settings = SettingsManager(self.db)

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()
        DatabaseManager._instance = None

    def test_default_settings_retrieval(self):
        """Verify fallback default values"""
        tf = self.settings.get("default_timeframe")
        self.assertEqual(tf, "M5")
        
        sound = self.settings.get_bool("sound_notifications")
        self.assertTrue(sound)

    def test_set_and_persist_setting(self):
        """Verify setting updates and persists across reload"""
        self.settings.set("default_timeframe", "H1")
        self.assertEqual(self.settings.get("default_timeframe"), "H1")

        # Create new manager pointing to same DB to test persistence
        fresh_manager = SettingsManager(self.db)
        fresh_manager.load_all()
        self.assertEqual(fresh_manager.get("default_timeframe"), "H1")

    def test_save_bulk_settings(self):
        """Verify bulk settings save"""
        payload = {
            "default_market": "Indices (US30 / NAS100 / SPX500)",
            "refresh_interval_sec": "30",
            "popup_notifications": "False"
        }
        self.settings.save_bulk(payload)

        self.assertEqual(self.settings.get("default_market"), "Indices (US30 / NAS100 / SPX500)")
        self.assertEqual(self.settings.get_int("refresh_interval_sec"), 30)
        self.assertFalse(self.settings.get_bool("popup_notifications"))

    def test_reset_defaults(self):
        """Verify resetting to default settings"""
        self.settings.set("default_timeframe", "D1")
        self.assertEqual(self.settings.get("default_timeframe"), "D1")

        self.settings.reset_to_defaults()
        self.assertEqual(self.settings.get("default_timeframe"), "M5")


if __name__ == "__main__":
    unittest.main()
