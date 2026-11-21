"""
M4DI~UciH4 Trading Intelligence System
Tests for Provider Health Monitor
"""
import unittest
from api.health_monitor import ProviderHealthMonitor
from core.event_bus import EventBus
from config.constants import (
    PROVIDER_FINNHUB,
    HEALTH_CONNECTED,
    HEALTH_RATE_LIMITED,
    HEALTH_INVALID_KEY,
    HEALTH_ERROR,
    HEALTH_DISCONNECTED
)


class TestProviderHealth(unittest.TestCase):
    def setUp(self):
        self.events = EventBus()
        self.monitor = ProviderHealthMonitor(self.events)

    def test_initial_state(self):
        h = self.monitor.get_health(PROVIDER_FINNHUB)
        self.assertEqual(h["status"], HEALTH_DISCONNECTED)
        self.assertEqual(h["consecutive_errors"], 0)

    def test_record_success_transitions_connected(self):
        self.monitor.record_success(PROVIDER_FINNHUB)
        h = self.monitor.get_health(PROVIDER_FINNHUB)
        self.assertEqual(h["status"], HEALTH_CONNECTED)
        self.assertIsNotNone(h["last_success_at"])
        self.assertEqual(h["successful_requests"], 1)

    def test_record_rate_limit_transitions(self):
        self.monitor.record_rate_limit(PROVIDER_FINNHUB, cooldown_sec=45.0)
        h = self.monitor.get_health(PROVIDER_FINNHUB)
        self.assertEqual(h["status"], HEALTH_RATE_LIMITED)
        self.assertEqual(h["rate_limited_count"], 1)

    def test_record_auth_error_transitions(self):
        self.monitor.record_auth_error(PROVIDER_FINNHUB, "HTTP 401 Unauthorized")
        h = self.monitor.get_health(PROVIDER_FINNHUB)
        self.assertEqual(h["status"], HEALTH_INVALID_KEY)
        self.assertIn("401", h["last_error_message"])

    def test_record_error_streak(self):
        self.monitor.record_error(PROVIDER_FINNHUB, "Server timeout")
        self.monitor.record_error(PROVIDER_FINNHUB, "Connection reset")
        h = self.monitor.get_health(PROVIDER_FINNHUB)
        self.assertEqual(h["status"], HEALTH_ERROR)
        self.assertEqual(h["consecutive_errors"], 2)


if __name__ == "__main__":
    unittest.main()
