"""
M4DI~UciH4 Trading Intelligence System
Universal Exporter Unit Tests (Phase 6)
Verifies CSV and JSON export pipelines for scanner, signals, news,
portfolio, and backtesting datasets.
"""
import unittest
import tempfile
import json
import csv
from pathlib import Path

from utils.exporter import UniversalExporter


class TestUniversalExporter(unittest.TestCase):
    """Test suite for UniversalExporter CSV and JSON generation"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.export_dir = Path(self.temp_dir.name)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_export_csv_basic(self):
        data = [
            {"symbol": "XAU/USD", "price": 2650.50, "rsi": 45.2, "trend": "BULLISH"},
            {"symbol": "EUR/USD", "price": 1.0550, "rsi": 62.1, "trend": "NEUTRAL"}
        ]
        out_file = self.export_dir / "test_data.csv"
        ok, msg = UniversalExporter.export_csv(data, out_file)

        self.assertTrue(ok)
        self.assertTrue(out_file.exists())

        # Verify contents
        with open(out_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["symbol"], "XAU/USD")
            self.assertEqual(float(rows[0]["price"]), 2650.50)

    def test_export_json_basic(self):
        data = {
            "strategy": "EMA Crossover",
            "metrics": {
                "total_return_pct": 18.5,
                "sharpe_ratio": 1.85,
                "win_rate_pct": 62.0
            }
        }
        out_file = self.export_dir / "test_data.json"
        ok, msg = UniversalExporter.export_json(data, out_file)

        self.assertTrue(ok)
        self.assertTrue(out_file.exists())

        with open(out_file, mode="r", encoding="utf-8") as f:
            loaded = json.load(f)
            self.assertEqual(loaded["strategy"], "EMA Crossover")
            self.assertEqual(loaded["metrics"]["win_rate_pct"], 62.0)

    def test_export_empty_data_rejection(self):
        out_file = self.export_dir / "empty.csv"
        ok, msg = UniversalExporter.export_csv([], out_file)
        self.assertFalse(ok)
        self.assertIn("No data", msg)


if __name__ == "__main__":
    unittest.main()
