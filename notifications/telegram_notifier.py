"""
M4DI~UciH4 Trading Intelligence System
Optional Telegram Notification Dispatcher (Phase 6)
Dispatches formatted institutional alerts for Trading Signals, High-Impact News,
Risk Circuit Breakers, and Portfolio / Paper Trading events.
Completely optional: falls back gracefully if not configured or disabled.
"""
import json
import threading
from typing import Dict, Any, Optional, Tuple
import requests

from core.logger import get_logger
from config.settings import SettingsManager
from config.constants import (
    SETTING_TELEGRAM_ENABLED,
    SETTING_TELEGRAM_BOT_TOKEN,
    SETTING_TELEGRAM_CHAT_ID,
    SETTING_TELEGRAM_NOTIFY_SIGNALS,
    SETTING_TELEGRAM_NOTIFY_NEWS,
    SETTING_TELEGRAM_NOTIFY_RISK,
    SETTING_TELEGRAM_NOTIFY_PORTFOLIO,
    APP_NAME
)

logger = get_logger("TelegramNotifier")


class TelegramNotifier:
    """Thread-safe, non-blocking optional Telegram alert dispatcher"""

    def __init__(self, settings: Optional[SettingsManager] = None):
        self.settings = settings
        self._lock = threading.Lock()
        self._timeout_sec = 8.0

    @property
    def is_enabled(self) -> bool:
        """Check if Telegram integration is explicitly enabled with credentials"""
        if not self.settings:
            return False
        enabled = self.settings.get(SETTING_TELEGRAM_ENABLED, "false").lower() == "true"
        token = self.settings.get(SETTING_TELEGRAM_BOT_TOKEN, "").strip()
        chat_id = self.settings.get(SETTING_TELEGRAM_CHAT_ID, "").strip()
        return enabled and bool(token) and bool(chat_id)

    def _get_credentials(self) -> Tuple[str, str]:
        if not self.settings:
            return "", ""
        token = self.settings.get(SETTING_TELEGRAM_BOT_TOKEN, "").strip()
        chat_id = self.settings.get(SETTING_TELEGRAM_CHAT_ID, "").strip()
        return token, chat_id

    def send_message(self, text: str, parse_mode: str = "HTML") -> Tuple[bool, str]:
        """
        Send raw formatted message to configured Telegram chat.
        Synchronous execution with short timeout.
        """
        token, chat_id = self._get_credentials()
        if not token or not chat_id:
            return False, "Telegram Bot Token or Chat ID is not configured."

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            resp = requests.post(url, json=payload, timeout=self._timeout_sec)
            data = resp.json()
            if resp.status_code == 200 and data.get("ok"):
                return True, "Message delivered successfully."
            error_desc = data.get("description", f"HTTP {resp.status_code}")
            logger.warning(f"Telegram dispatch failed: {error_desc}")
            return False, f"Telegram API error: {error_desc}"
        except requests.exceptions.Timeout:
            logger.warning("Telegram request timed out.")
            return False, "Connection to Telegram API timed out."
        except Exception as e:
            logger.warning(f"Telegram dispatch error: {e}")
            return False, f"Network error: {str(e)}"

    def send_async(self, text: str, parse_mode: str = "HTML"):
        """Fire-and-forget asynchronous dispatch in background daemon thread"""
        if not self.is_enabled:
            return

        def _worker():
            self.send_message(text, parse_mode=parse_mode)

        threading.Thread(target=_worker, daemon=True).start()

    def test_connection(self) -> Tuple[bool, str]:
        """Verify bot token via getMe and send test message to chat_id"""
        token, chat_id = self._get_credentials()
        if not token:
            return False, "Telegram Bot Token is empty."
        if not chat_id:
            return False, "Telegram Chat ID is empty."

        try:
            # 1. Check Bot validity
            me_url = f"https://api.telegram.org/bot{token}/getMe"
            resp = requests.get(me_url, timeout=self._timeout_sec)
            if resp.status_code != 200 or not resp.json().get("ok"):
                desc = resp.json().get("description", f"HTTP {resp.status_code}")
                return False, f"Invalid Bot Token: {desc}"

            bot_user = resp.json().get("result", {}).get("username", "UnknownBot")

            # 2. Send ping message
            test_msg = (
                f"✅ <b>{APP_NAME}</b>\n"
                f"📡 <b>Telegram Integration Verified</b>\n\n"
                f"Connected Bot: @{bot_user}\n"
                f"Chat ID: <code>{chat_id}</code>\n"
                f"Status: Operational & Ready to transmit institutional alerts."
            )
            ok, msg = self.send_message(test_msg)
            if ok:
                return True, f"Connection verified! Test alert sent via @{bot_user}."
            return False, f"Bot token valid (@{bot_user}), but could not send to Chat ID: {msg}"
        except Exception as e:
            return False, f"Verification failed: {str(e)}"

    def notify_signal(self, signal: Any) -> bool:
        """Format and dispatch Trading Signal alert"""
        if not self.is_enabled:
            return False
        if self.settings and self.settings.get(SETTING_TELEGRAM_NOTIFY_SIGNALS, "true").lower() != "true":
            return False

        emoji = "🟢" if "BUY" in str(getattr(signal, "signal", "")).upper() else "🔴"
        action = getattr(signal, "signal", "NEUTRAL")
        symbol = getattr(signal, "symbol", "UNKNOWN")
        entry = getattr(signal, "entry_price", 0.0)
        sl = getattr(signal, "stop_loss", 0.0)
        tp1 = getattr(signal, "take_profit_1", 0.0)
        tp2 = getattr(signal, "take_profit_2", 0.0)
        conf = getattr(signal, "confidence", getattr(signal, "confidence_pct", 0.0))
        score = getattr(signal, "score", 0.0)
        timeframe = getattr(signal, "timeframe", "1h")

        msg = (
            f"{emoji} <b>INSTITUTIONAL SIGNAL ALERT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Asset:</b> <code>{symbol}</code> ({timeframe})\n"
            f"<b>Setup:</b> <b>{action}</b> (Confidence: {conf:.1f}% | Score: {score:+.1f})\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Entry:</b> <code>{entry:,.4f}</code>\n"
            f"🛑 <b>Stop Loss:</b> <code>{sl:,.4f}</code>\n"
            f"💎 <b>Target 1:</b> <code>{tp1:,.4f}</code>\n"
            f"🚀 <b>Target 2:</b> <code>{tp2:,.4f}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>{APP_NAME} Quantitative Engine</i>"
        )
        self.send_async(msg)
        return True

    def notify_news(self, article: Any) -> bool:
        """Format and dispatch High-Impact News catalyst alert"""
        if not self.is_enabled:
            return False
        if self.settings and self.settings.get(SETTING_TELEGRAM_NOTIFY_NEWS, "true").lower() != "true":
            return False

        title = getattr(article, "title", "Breaking Market News")
        impact = getattr(article, "impact_tier", "HIGH")
        category = getattr(article, "category", "Macro")
        sentiment = getattr(article, "sentiment_label", "NEUTRAL")
        url = getattr(article, "url", "")

        msg = (
            f"🚨 <b>HIGH-IMPACT NEWS CATALYST</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Impact Tier:</b> <b>{impact}</b>\n"
            f"<b>Category:</b> {category}\n"
            f"<b>Sentiment:</b> {sentiment}\n\n"
            f"📰 <b>{title}</b>\n"
        )
        if url:
            msg += f"\n🔗 <a href='{url}'>Read Full Report</a>\n"
        msg += f"\n<i>{APP_NAME} Macro Intelligence</i>"

        self.send_async(msg)
        return True

    def notify_risk(self, alert_type: str, details: str) -> bool:
        """Format and dispatch Risk Management circuit breaker alert"""
        if not self.is_enabled:
            return False
        if self.settings and self.settings.get(SETTING_TELEGRAM_NOTIFY_RISK, "true").lower() != "true":
            return False

        msg = (
            f"🛡️ <b>RISK CIRCUIT BREAKER TRIGGERED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Event:</b> <b>{alert_type}</b>\n"
            f"<b>Details:</b> {details}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <i>Trading operations paused / order rejected to protect capital.</i>"
        )
        self.send_async(msg)
        return True

    def notify_portfolio(self, event_type: str, details: Dict[str, Any]) -> bool:
        """Format and dispatch Paper Trading portfolio activity"""
        if not self.is_enabled:
            return False
        if self.settings and self.settings.get(SETTING_TELEGRAM_NOTIFY_PORTFOLIO, "true").lower() != "true":
            return False

        sym = details.get("symbol", "-")
        side = details.get("side", "-")
        units = details.get("units", 0.0)
        price = details.get("price", 0.0)
        pnl = details.get("pnl", 0.0)

        msg = (
            f"💼 <b>PAPER TRADING LEDGER UPDATE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Action:</b> {event_type}\n"
            f"<b>Position:</b> {side} {units:,.2f} {sym} @ {price:,.4f}\n"
        )
        if "pnl" in details:
            sign = "+" if pnl >= 0 else ""
            msg += f"<b>Realized P&L:</b> <code>${sign}{pnl:,.2f}</code>\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━\n<i>{APP_NAME} Simulation Desk</i>"

        self.send_async(msg)
        return True
