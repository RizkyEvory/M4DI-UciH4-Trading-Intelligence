"""
M4DI~UciH4 Trading Intelligence System
Tests for In-Memory Response Cache
"""
import time
import unittest
from api.cache import ResponseCache, make_quote_key, make_candle_key


class TestResponseCache(unittest.TestCase):
    def setUp(self):
        self.cache = ResponseCache()

    def test_set_and_get(self):
        key = make_quote_key("Finnhub", "AAPL")
        payload = {"price": 250.0}
        self.cache.set(key, payload, ttl_seconds=5.0)

        res = self.cache.get(key)
        self.assertIsNotNone(res)
        self.assertEqual(res["price"], 250.0)

    def test_ttl_expiry(self):
        key = make_quote_key("Twelve Data", "EURUSD")
        self.cache.set(key, {"rate": 1.0850}, ttl_seconds=0.1)

        # Immediate hit
        self.assertIsNotNone(self.cache.get(key))

        # Wait for TTL to expire
        time.sleep(0.15)
        self.assertIsNone(self.cache.get(key))

    def test_invalidation(self):
        key = make_quote_key("Finnhub", "MSFT")
        self.cache.set(key, {"price": 420.0}, ttl_seconds=10.0)
        self.assertTrue(self.cache.invalidate(key))
        self.assertIsNone(self.cache.get(key))

    def test_prefix_invalidation(self):
        self.cache.set("finnhub:quote:AAPL", {"p": 1}, ttl_seconds=10.0)
        self.cache.set("finnhub:quote:GOOGL", {"p": 2}, ttl_seconds=10.0)
        self.cache.set("twelvedata:quote:EURUSD", {"p": 3}, ttl_seconds=10.0)

        deleted = self.cache.invalidate_prefix("finnhub:quote:")
        self.assertEqual(deleted, 2)
        self.assertIsNone(self.cache.get("finnhub:quote:AAPL"))
        self.assertIsNotNone(self.cache.get("twelvedata:quote:EURUSD"))

    def test_stats_and_hit_rate(self):
        key = "test:stat:item"
        self.cache.set(key, "data", ttl_seconds=5.0)

        # 2 hits
        self.cache.get(key)
        self.cache.get(key)
        # 1 miss
        self.cache.get("nonexistent")

        stats = self.cache.stats()
        self.assertEqual(stats["hits"], 2)
        self.assertEqual(stats["misses"], 1)
        self.assertAlmostEqual(stats["hit_rate_pct"], 66.67, places=1)


if __name__ == "__main__":
    unittest.main()
