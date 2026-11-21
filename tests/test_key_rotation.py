"""
M4DI~UciH4 Trading Intelligence System
Tests for Intelligent Multi-Key Rotation Manager
"""
import os
import tempfile
import unittest
from pathlib import Path

from database.db_manager import DatabaseManager
from api.key_manager import ApiKeyManager
from api.key_rotation import KeyRotationManager
from config.constants import (
    PROVIDER_FINNHUB,
    ROTATION_STRATEGY_PRIORITY,
    ROTATION_STRATEGY_ROUND_ROBIN,
    ROTATION_STRATEGY_LEAST_USED,
    ROTATION_STRATEGY_FAILOVER
)


class TestKeyRotation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_rotation.db"
        DatabaseManager._instance = None
        self.db = DatabaseManager(self.db_path)
        self.key_manager = ApiKeyManager(self.db)
        self.rotation = KeyRotationManager(self.db)

        # Seed 3 Finnhub keys with different priorities
        self.k1 = self.key_manager.add_key(PROVIDER_FINNHUB, "FH Low", "token_low_priority", priority=1)
        self.k2 = self.key_manager.add_key(PROVIDER_FINNHUB, "FH Mid", "token_mid_priority", priority=5)
        self.k3 = self.key_manager.add_key(PROVIDER_FINNHUB, "FH High", "token_high_priority", priority=10)

    def tearDown(self):
        self.db.close()
        DatabaseManager._instance = None
        self.temp_dir.cleanup()

    def test_priority_selection(self):
        self.rotation.set_strategy(PROVIDER_FINNHUB, ROTATION_STRATEGY_PRIORITY)
        selected = self.rotation.select_key(PROVIDER_FINNHUB)
        self.assertIsNotNone(selected)
        self.assertEqual(selected["id"], self.k3)  # Highest priority (10)

    def test_round_robin_selection(self):
        self.rotation.set_strategy(PROVIDER_FINNHUB, ROTATION_STRATEGY_ROUND_ROBIN)
        ids = [self.rotation.select_key(PROVIDER_FINNHUB)["id"] for _ in range(3)]
        # All 3 keys should have been picked
        self.assertEqual(set(ids), {self.k1, self.k2, self.k3})

    def test_least_used_selection(self):
        self.rotation.set_strategy(PROVIDER_FINNHUB, ROTATION_STRATEGY_LEAST_USED)
        # Mark k3 and k2 as recently used
        self.rotation.record_key_success(self.k3)
        self.rotation.record_key_success(self.k2)

        # k1 has never been used (last_used_at is NULL) -> should be selected
        selected = self.rotation.select_key(PROVIDER_FINNHUB)
        self.assertEqual(selected["id"], self.k1)

    def test_failover_cooldown_skipping(self):
        self.rotation.set_strategy(PROVIDER_FINNHUB, ROTATION_STRATEGY_PRIORITY)

        # Put high priority key k3 in cooldown
        self.rotation.record_key_rate_limit(self.k3, cooldown_sec=120)

        # Selection should now failover to k2 (next highest priority)
        selected = self.rotation.select_key(PROVIDER_FINNHUB)
        self.assertEqual(selected["id"], self.k2)

        # Put k2 in cooldown too
        self.rotation.record_key_rate_limit(self.k2, cooldown_sec=120)

        # Now fails over to k1
        selected = self.rotation.select_key(PROVIDER_FINNHUB)
        self.assertEqual(selected["id"], self.k1)

    def test_auth_error_exclusion(self):
        # Mark k3 with invalid key error (HTTP 401)
        self.rotation.record_key_auth_error(self.k3)

        # k3 should no longer be eligible
        eligible = self.rotation.get_eligible_keys(PROVIDER_FINNHUB)
        eligible_ids = [k["id"] for k in eligible]
        self.assertNotIn(self.k3, eligible_ids)

    def test_decrypted_key_retrieval(self):
        key_data = self.rotation.get_key_for_request(PROVIDER_FINNHUB)
        self.assertIsNotNone(key_data)
        self.assertIn("raw_key", key_data)
        self.assertEqual(key_data["raw_key"], "token_high_priority")


if __name__ == "__main__":
    unittest.main()
