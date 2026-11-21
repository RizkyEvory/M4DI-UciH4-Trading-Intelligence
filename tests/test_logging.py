"""
Unit Tests for Multi-Target Logging and Secret Sanitization
"""
import unittest
import tempfile
import logging
from pathlib import Path

from database.db_manager import DatabaseManager
from core.logger import setup_logging, get_app_logger, sanitize_message, SQLiteLogHandler


class TestLogging(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_logs.db"
        
        DatabaseManager._instance = None
        self.db = DatabaseManager(self.db_path)
        
        # Reset m4di logger handlers
        logger = logging.getLogger("m4di")
        for h in list(logger.handlers):
            try:
                h.close()
            except Exception:
                pass
        logger.handlers.clear()
        
        self.logger = setup_logging(db_manager=self.db, log_level="DEBUG")

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()
        DatabaseManager._instance = None

    def test_message_sanitization(self):
        """Verify API keys and tokens are automatically masked from log strings"""
        raw_msg = "Attempting connect with api_key: 1234567890abcdef and secret=super_secret_token_123"
        sanitized = sanitize_message(raw_msg)

        self.assertNotIn("1234567890abcdef", sanitized)
        self.assertNotIn("super_secret_token_123", sanitized)
        self.assertIn("••••••••", sanitized)

    def test_logging_to_sqlite(self):
        """Verify log messages are inserted into the SQLite database"""
        self.logger.info("Test message for SQLite verification")
        self.logger.warning("Warning message for SQLite verification")

        rows = self.db.fetchall("SELECT level, message FROM logs WHERE message LIKE '%SQLite verification%'")
        self.assertEqual(len(rows), 2)
        levels = [r[0] for r in rows]
        self.assertIn("INFO", levels)
        self.assertIn("WARNING", levels)


if __name__ == "__main__":
    unittest.main()
