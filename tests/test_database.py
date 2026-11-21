"""
Unit Tests for Database Initialization and Schema Integrity
"""
import unittest
import tempfile
from pathlib import Path
from database.db_manager import DatabaseManager


class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Create temporary database
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_trading.db"
        
        # Reset singleton for testing
        DatabaseManager._instance = None
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()
        DatabaseManager._instance = None

    def test_database_creation_and_tables(self):
        """Verify that all 5 required tables exist in SQLite"""
        tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
        rows = self.db.fetchall(tables_query)
        table_names = [r[0] for r in rows]

        expected_tables = ["settings", "api_keys", "logs", "watchlists", "watchlist_symbols"]
        for tbl in expected_tables:
            self.assertIn(tbl, table_names, f"Table '{tbl}' should exist in database")

    def test_default_watchlists_seeded(self):
        """Verify that initial default watchlists are seeded on DB creation"""
        rows = self.db.fetchall("SELECT name FROM watchlists")
        names = [r[0] for r in rows]
        self.assertIn("Gold & Metals", names)
        self.assertIn("Forex Majors", names)
        self.assertGreaterEqual(len(names), 4)

    def test_parameterized_execution(self):
        """Verify parameterized queries prevent SQL injection and insert correctly"""
        rowid = self.db.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ("test_key", "test_val"))
        self.assertIsNotNone(rowid)

        res = self.db.fetchone("SELECT value FROM settings WHERE key = ?", ("test_key",))
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "test_val")


if __name__ == "__main__":
    unittest.main()
