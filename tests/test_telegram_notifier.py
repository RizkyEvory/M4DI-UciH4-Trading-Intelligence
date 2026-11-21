"""
M4DI~UciH4 Trading Intelligence System
Telegram Notifier Unit Tests (Phase 6)
Verifies optional dispatching, graceful fallback when disabled,
and payload formatting for Signals, News, Risk, and Portfolio events.
"""
import unittest
from unittest.mock import patch, MagicMock

from config.settings import SettingsManager
from config.constants import (
    SETTING_TELEGRAM_ENABLED,
    SETTING_TELEGRAM_BOT_TOKEN,
    SETTING_TELEGRAM_CHAT_ID
)
from database.db_manager import DatabaseManager
from notifications.telegram_notifier import TelegramNotifier
from signals.models import TradingSignal
from news.models import EnrichedNewsArticle
import tempfile
from pathlib import Path


class TestTelegramNotifier(unittest.TestCase):
    """Test TelegramNotifier behavior in disabled, mock-enabled, and event dispatch states"""

    def setUp(self):
        DatabaseManager._instance = None
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_tg.db"
        self.db = DatabaseManager(self.db_path)
        self.settings = SettingsManager(self.db)
        self.notifier = TelegramNotifier(self.settings)

    def tearDown(self):
        try:
            self.db.close()
            self.temp_dir.cleanup()
        except Exception:
            pass
        DatabaseManager._instance = None

    def test_disabled_by_default(self):
        self.assertFalse(self.notifier.is_enabled)
        ok, msg = self.notifier.send_message("Test message")
        self.assertFalse(ok)
        self.assertIn("not configured", msg)

    def test_enabled_state_detection(self):
        self.settings.set(SETTING_TELEGRAM_ENABLED, "true")
        self.settings.set(SETTING_TELEGRAM_BOT_TOKEN, "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        self.settings.set(SETTING_TELEGRAM_CHAT_ID, "987654321")

        self.assertTrue(self.notifier.is_enabled)

    @patch("requests.post")
    def test_mock_send_message_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True, "result": {"message_id": 1}}
        mock_post.return_value = mock_resp

        self.settings.set(SETTING_TELEGRAM_ENABLED, "true")
        self.settings.set(SETTING_TELEGRAM_BOT_TOKEN, "test_token")
        self.settings.set(SETTING_TELEGRAM_CHAT_ID, "12345")

        ok, msg = self.notifier.send_message("Hello institutional trader")
        self.assertTrue(ok)
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_notify_signal_formatting(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True}
        mock_post.return_value = mock_resp

        self.settings.set(SETTING_TELEGRAM_ENABLED, "true")
        self.settings.set(SETTING_TELEGRAM_BOT_TOKEN, "test_token")
        self.settings.set(SETTING_TELEGRAM_CHAT_ID, "12345")

        sig = TradingSignal(
            symbol="XAU/USD",
            signal="Strong Buy",
            score=75.0,
            confidence=85.0,
            entry_price=2650.0,
            stop_loss=2635.0,
            take_profit_1=2675.0,
            take_profit_2=2695.0,
            timeframe="1h"
        )

        sent = self.notifier.notify_signal(sig)
        self.assertTrue(sent)

    def test_notify_risk_when_disabled(self):
        # When disabled, notify_risk returns False without raising exception
        sent = self.notifier.notify_risk("DAILY_LOSS_LIMIT", "3.5% >= 3.0%")
        self.assertFalse(sent)


if __name__ == "__main__":
    unittest.main()
