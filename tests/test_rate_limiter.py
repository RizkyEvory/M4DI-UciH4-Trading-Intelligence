"""
M4DI~UciH4 Trading Intelligence System
Tests for Provider-Aware Rate Limit Manager
"""
import time
import unittest
from api.rate_limiter import RateLimitManager
from config.constants import PROVIDER_FINNHUB, PROVIDER_TWELVE_DATA


class TestRateLimiter(unittest.TestCase):
    def setUp(self):
        self.limiter = RateLimitManager({
            PROVIDER_FINNHUB: {"rpm": 3, "min_interval_sec": 0.05},
            PROVIDER_TWELVE_DATA: {"rpm": 2, "min_interval_sec": 0.1}
        })

    def test_basic_request_allowance(self):
        allowed, wait = self.limiter.can_request(PROVIDER_FINNHUB)
        self.assertTrue(allowed)
        self.assertEqual(wait, 0.0)

    def test_interval_throttle(self):
        self.limiter.record_request(PROVIDER_FINNHUB)
        allowed, wait = self.limiter.can_request(PROVIDER_FINNHUB)
        self.assertFalse(allowed)
        self.assertGreater(wait, 0.0)

        # Wait for min_interval to elapse
        time.sleep(0.06)
        allowed, wait = self.limiter.can_request(PROVIDER_FINNHUB)
        self.assertTrue(allowed)

    def test_rpm_quota_exhaustion(self):
        # Fire 3 requests rapidly (respecting min_interval)
        for _ in range(3):
            self.limiter.record_request(PROVIDER_FINNHUB)
            time.sleep(0.06)

        # 4th request must be rejected due to RPM limit (3/min)
        allowed, wait = self.limiter.can_request(PROVIDER_FINNHUB)
        self.assertFalse(allowed)
        self.assertGreater(wait, 10.0)

    def test_cooldown_behavior(self):
        self.limiter.set_cooldown(PROVIDER_TWELVE_DATA, 0.2)
        is_cooling, rem = self.limiter.is_in_cooldown(PROVIDER_TWELVE_DATA)
        self.assertTrue(is_cooling)
        self.assertGreater(rem, 0.0)

        allowed, wait = self.limiter.can_request(PROVIDER_TWELVE_DATA)
        self.assertFalse(allowed)

        time.sleep(0.25)
        is_cooling, rem = self.limiter.is_in_cooldown(PROVIDER_TWELVE_DATA)
        self.assertFalse(is_cooling)

    def test_exponential_backoff(self):
        b0 = RateLimitManager.calculate_backoff(0, base_delay=1.0)
        b1 = RateLimitManager.calculate_backoff(1, base_delay=1.0)
        b2 = RateLimitManager.calculate_backoff(2, base_delay=1.0)

        self.assertGreaterEqual(b0, 1.0)
        self.assertGreaterEqual(b1, 2.0)
        self.assertGreaterEqual(b2, 4.0)

        # Test capping
        capped = RateLimitManager.calculate_backoff(10, base_delay=1.0, max_delay=8.0)
        self.assertLessEqual(capped, 9.0)  # 8.0 + 10% jitter


if __name__ == "__main__":
    unittest.main()
