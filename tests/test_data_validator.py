"""
M4DI~UciH4 Trading Intelligence System
Tests for Data Validator & Integrity Engine
"""
from datetime import datetime, timedelta
import unittest
from api.models import NormalizedCandle
from engine.data_validator import DataValidator


class TestDataValidator(unittest.TestCase):

    def test_valid_candle(self):
        c = NormalizedCandle("AAPL", "1d", open=200.0, high=205.0, low=198.0, close=202.0, volume=50000.0, timestamp="2026-03-20 15:30:00")
        ok, reason = DataValidator.validate_candle(c)
        self.assertTrue(ok)
        self.assertEqual(reason, "")

    def test_invalid_ohlc_relationships(self):
        # High lower than Low
        c1 = NormalizedCandle("AAPL", "1d", open=200.0, high=195.0, low=202.0, close=200.0, volume=10.0, timestamp="2026-03-20 12:00:00")
        ok, _ = DataValidator.validate_candle(c1)
        self.assertFalse(ok)

        # High lower than Open
        c2 = NormalizedCandle("AAPL", "1d", open=205.0, high=200.0, low=190.0, close=195.0, volume=10.0, timestamp="2026-03-20 12:00:00")
        ok, _ = DataValidator.validate_candle(c2)
        self.assertFalse(ok)

        # Negative Volume
        c3 = NormalizedCandle("AAPL", "1d", open=200.0, high=205.0, low=195.0, close=202.0, volume=-5.0, timestamp="2026-03-20 12:00:00")
        ok, _ = DataValidator.validate_candle(c3)
        self.assertFalse(ok)

    def test_future_timestamp_rejection(self):
        future_ts = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        c = NormalizedCandle("AAPL", "1d", open=200.0, high=205.0, low=195.0, close=202.0, volume=100.0, timestamp=future_ts)
        ok, reason = DataValidator.validate_candle(c)
        self.assertFalse(ok)
        self.assertIn("Future timestamp", reason)

    def test_clean_deduplicate_and_sort(self):
        # 3 bars with duplicate timestamp and unordered
        c1 = NormalizedCandle("AAPL", "1d", open=200.0, high=205.0, low=195.0, close=202.0, volume=100.0, timestamp="2026-03-18 10:00:00")
        c2 = NormalizedCandle("AAPL", "1d", open=202.0, high=206.0, low=197.0, close=204.0, volume=150.0, timestamp="2026-03-20 10:00:00")
        c3_dup = NormalizedCandle("AAPL", "1d", open=202.0, high=207.0, low=197.0, close=205.0, volume=160.0, timestamp="2026-03-20 10:00:00")
        c4 = NormalizedCandle("AAPL", "1d", open=198.0, high=201.0, low=194.0, close=200.0, volume=80.0, timestamp="2026-03-19 10:00:00")

        cleaned = DataValidator.clean_and_sort_candles([c2, c1, c3_dup, c4])

        self.assertEqual(len(cleaned), 3)  # Duplicate timestamp 2026-03-20 merged
        # Order must be strictly ascending: 18th -> 19th -> 20th
        self.assertEqual(cleaned[0].timestamp, "2026-03-18 10:00:00")
        self.assertEqual(cleaned[1].timestamp, "2026-03-19 10:00:00")
        self.assertEqual(cleaned[2].timestamp, "2026-03-20 10:00:00")

    def test_detect_gaps(self):
        c1 = NormalizedCandle("AAPL", "1h", open=100.0, high=105.0, low=95.0, close=102.0, volume=10.0, timestamp="2026-03-20 10:00:00")
        c2 = NormalizedCandle("AAPL", "1h", open=102.0, high=106.0, low=98.0, close=104.0, volume=10.0, timestamp="2026-03-20 14:00:00") # 4 hours gap!
        gaps = DataValidator.detect_gaps([c1, c2], expected_interval_sec=3600)
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0][2], 14400.0)  # 4 hours


if __name__ == "__main__":
    unittest.main()
