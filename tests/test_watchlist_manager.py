"""
M4DI~UciH4 Trading Intelligence System
Watchlist Manager Unit Tests (Phase 6)
Verifies multi-watchlist lifecycle, symbol tracking, notes persistence,
alert rules evaluation, and scanner integration.
"""
import unittest
import tempfile
from pathlib import Path

from database.db_manager import DatabaseManager
from watchlist.watchlist_manager import WatchlistManager


class TestWatchlistManager(unittest.TestCase):
    """Test suite for WatchlistManager lifecycle and alert evaluation"""

    def setUp(self):
        DatabaseManager._instance = None
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_watchlist.db"
        self.db = DatabaseManager(self.db_path)
        self.wm = WatchlistManager(self.db)

    def tearDown(self):
        try:
            self.db.close()
            self.temp_dir.cleanup()
        except Exception:
            pass
        DatabaseManager._instance = None

    def test_get_seed_watchlists(self):
        wls = self.wm.get_watchlists()
        self.assertGreaterEqual(len(wls), 4)
        names = [w["name"] for w in wls]
        self.assertIn("Gold & Metals", names)
        self.assertIn("Forex Majors", names)

    def test_create_and_rename_watchlist(self):
        ok, msg, wid = self.wm.create_watchlist("Institutional Energy", "Crude oil & NatGas")
        self.assertTrue(ok)
        self.assertIsNotNone(wid)

        # Duplicate name prevention
        dup_ok, dup_msg, _ = self.wm.create_watchlist("Institutional Energy")
        self.assertFalse(dup_ok)

        # Rename
        r_ok, r_msg = self.wm.rename_watchlist(wid, "Energy & Commodities")
        self.assertTrue(r_ok)

        wls = self.wm.get_watchlists()
        names = [w["name"] for w in wls]
        self.assertIn("Energy & Commodities", names)
        self.assertNotIn("Institutional Energy", names)

    def test_add_and_remove_symbol(self):
        wls = self.wm.get_watchlists()
        wid = wls[0]["id"]

        ok, _ = self.wm.add_symbol(
            watchlist_id=wid,
            symbol="SILVER",
            market="Commodities",
            notes="Physical demand expansion",
            alert_condition="> 35.00"
        )
        self.assertTrue(ok)

        # Verify added
        symbols = self.wm.get_symbols(wid)
        sym_names = [s["symbol"] for s in symbols]
        self.assertIn("SILVER", sym_names)

        # Remove
        rem_ok, _ = self.wm.remove_symbol(wid, "SILVER")
        self.assertTrue(rem_ok)

        symbols_after = self.wm.get_symbols(wid)
        self.assertNotIn("SILVER", [s["symbol"] for s in symbols_after])

    def test_update_symbol_notes(self):
        wls = self.wm.get_watchlists()
        wid = wls[0]["id"]
        self.wm.add_symbol(wid, "TEST_SYM", "Equities", notes="Old notes")

        ok, _ = self.wm.update_symbol_notes(wid, "TEST_SYM", "Updated institutional thesis")
        self.assertTrue(ok)

        symbols = self.wm.get_symbols(wid)
        test_item = [s for s in symbols if s["symbol"] == "TEST_SYM"][0]
        self.assertEqual(test_item["notes"], "Updated institutional thesis")

    def test_evaluate_symbol_alerts(self):
        wls = self.wm.get_watchlists()
        wid = wls[0]["id"]

        self.wm.add_symbol(wid, "XAUUSD_ALERT", "Commodities", alert_condition="> 2650.00")

        # Price at 2640.00 (below threshold) -> No alert
        alerts_low = self.wm.evaluate_symbol_alerts("XAUUSD_ALERT", 2640.00)
        self.assertEqual(len(alerts_low), 0)

        # Price crosses to 2655.00 (above threshold) -> Triggers alert
        alerts_high = self.wm.evaluate_symbol_alerts("XAUUSD_ALERT", 2655.00)
        self.assertEqual(len(alerts_high), 1)
        self.assertIn("WATCHLIST ALERT", alerts_high[0])
        self.assertIn("2,655.0000", alerts_high[0])


if __name__ == "__main__":
    unittest.main()
