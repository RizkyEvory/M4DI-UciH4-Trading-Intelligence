"""
M4DI~UciH4 Trading Intelligence System
Signal Alerts Engine
Monitors real-time conditions, evaluating rules across Strong Buy/Sell signals,
Trend Breakouts, RSI Extremes, MACD Crossovers, Volume Breakouts, and High-Impact News releases.
"""
import uuid
import threading
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from config.constants import (
    SIGNAL_STRONG_BUY,
    SIGNAL_STRONG_SELL,
    ALERT_STRONG_BUY,
    ALERT_STRONG_SELL,
    ALERT_TREND_BREAKOUT,
    ALERT_RSI_EXTREME,
    ALERT_MACD_CROSSOVER,
    ALERT_VOLUME_BREAKOUT,
    ALERT_HIGH_IMPACT_NEWS,
    ALERT_TYPES,
    IMPACT_CRITICAL,
    IMPACT_HIGH
)
from api.models import NormalizedCandle
from analytics.indicators import TechnicalIndicators
from analytics.volume import VolumeAnalyzer
from news.models import EnrichedNewsArticle
from signals.models import TradingSignal, SignalAlert
from core.logger import get_app_logger

logger = get_app_logger("AlertsEngine")


class AlertsEngine:
    """Configurable multi-event alert dispatcher"""

    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self._lock = threading.RLock()
        self._alert_history: List[SignalAlert] = []
        self._listeners: List[Callable[[SignalAlert], None]] = []

        # Configurable alert preferences (all enabled by default)
        self.alert_configs: Dict[str, bool] = {alert_type: True for alert_type in ALERT_TYPES}

    def configure_alert(self, alert_type: str, enabled: bool):
        """Enable or disable a specific alert rule"""
        with self._lock:
            if alert_type in self.alert_configs:
                self.alert_configs[alert_type] = enabled

    def register_listener(self, callback: Callable[[SignalAlert], None]):
        """Register a GUI or notification callback for fired alerts"""
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def _dispatch_alert(self, alert: SignalAlert):
        """Record in history and dispatch to listeners & event bus"""
        with self._lock:
            self._alert_history.insert(0, alert)
            if len(self._alert_history) > 200:
                self._alert_history.pop()

        logger.info(f"🚨 ALERT [{alert.alert_type}] {alert.symbol}: {alert.message}")

        if self.event_bus:
            try:
                self.event_bus.publish("signal_alert", alert.to_dict())
            except Exception as e:
                logger.warning(f"Failed to publish alert to event bus: {e}")

        # Notify direct subscribers
        for listener in list(self._listeners):
            try:
                listener(alert)
            except Exception as e:
                logger.warning(f"Alert listener failed: {e}")

    def check_signal_alerts(self, signal: TradingSignal) -> List[SignalAlert]:
        """Check if a generated signal triggers Strong Buy or Strong Sell alerts"""
        alerts: List[SignalAlert] = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Strong Buy Alert
        if signal.signal == SIGNAL_STRONG_BUY and self.alert_configs.get(ALERT_STRONG_BUY, True):
            alert = SignalAlert(
                alert_id=str(uuid.uuid4())[:8],
                alert_type=ALERT_STRONG_BUY,
                symbol=signal.symbol,
                message=f"Strong Buy Signal generated with {signal.confidence:.1f}% confidence. Entry: {signal.entry_price:.2f}, SL: {signal.stop_loss:.2f}, TP: {signal.take_profit_1:.2f}",
                severity="CRITICAL",
                timestamp=now_str,
                metadata={"signal": signal.to_dict()}
            )
            self._dispatch_alert(alert)
            alerts.append(alert)

        # Strong Sell Alert
        elif signal.signal == SIGNAL_STRONG_SELL and self.alert_configs.get(ALERT_STRONG_SELL, True):
            alert = SignalAlert(
                alert_id=str(uuid.uuid4())[:8],
                alert_type=ALERT_STRONG_SELL,
                symbol=signal.symbol,
                message=f"Strong Sell Signal generated with {signal.confidence:.1f}% confidence. Entry: {signal.entry_price:.2f}, SL: {signal.stop_loss:.2f}, TP: {signal.take_profit_1:.2f}",
                severity="CRITICAL",
                timestamp=now_str,
                metadata={"signal": signal.to_dict()}
            )
            self._dispatch_alert(alert)
            alerts.append(alert)

        return alerts

    def check_technical_alerts(self, symbol: str, candles: List[NormalizedCandle]) -> List[SignalAlert]:
        """Check technical anomalies: RSI Extremes, MACD Crossovers, Trend Breakouts, Volume Breakouts"""
        alerts: List[SignalAlert] = []
        if not candles or len(candles) < 20:
            return alerts

        sym = symbol.upper().strip()
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. RSI Extreme Alert (< 25 or > 75)
        if self.alert_configs.get(ALERT_RSI_EXTREME, True):
            rsi = TechnicalIndicators.rsi(closes, 14)
            if rsi:
                curr_rsi = rsi[-1]
                if curr_rsi <= 25.0:
                    alert = SignalAlert(
                        alert_id=str(uuid.uuid4())[:8],
                        alert_type=ALERT_RSI_EXTREME,
                        symbol=sym,
                        message=f"RSI Deep Oversold ({curr_rsi:.1f}). Extreme institutional discount zone.",
                        severity="WARNING",
                        timestamp=now_str,
                        metadata={"rsi": curr_rsi}
                    )
                    self._dispatch_alert(alert)
                    alerts.append(alert)
                elif curr_rsi >= 75.0:
                    alert = SignalAlert(
                        alert_id=str(uuid.uuid4())[:8],
                        alert_type=ALERT_RSI_EXTREME,
                        symbol=sym,
                        message=f"RSI Deep Overbought ({curr_rsi:.1f}). Extreme institutional premium zone.",
                        severity="WARNING",
                        timestamp=now_str,
                        metadata={"rsi": curr_rsi}
                    )
                    self._dispatch_alert(alert)
                    alerts.append(alert)

        # 2. MACD Crossover Alert
        if self.alert_configs.get(ALERT_MACD_CROSSOVER, True):
            macd_line, sig_line, _ = TechnicalIndicators.macd(closes)
            if len(macd_line) >= 2 and len(sig_line) >= 2 and macd_line[-1] is not None and sig_line[-1] is not None and macd_line[-2] is not None and sig_line[-2] is not None:
                # Bullish Crossover (MACD crossed above Signal on current bar)
                if macd_line[-2] <= sig_line[-2] and macd_line[-1] > sig_line[-1]:
                    alert = SignalAlert(
                        alert_id=str(uuid.uuid4())[:8],
                        alert_type=ALERT_MACD_CROSSOVER,
                        symbol=sym,
                        message=f"Bullish MACD Crossover confirmed on {sym}. Momentum turning positive.",
                        severity="INFO",
                        timestamp=now_str,
                        metadata={"macd": macd_line[-1], "signal": sig_line[-1]}
                    )
                    self._dispatch_alert(alert)
                    alerts.append(alert)
                # Bearish Crossover (MACD crossed below Signal on current bar)
                elif macd_line[-2] >= sig_line[-2] and macd_line[-1] < sig_line[-1]:
                    alert = SignalAlert(
                        alert_id=str(uuid.uuid4())[:8],
                        alert_type=ALERT_MACD_CROSSOVER,
                        symbol=sym,
                        message=f"Bearish MACD Crossover confirmed on {sym}. Momentum turning negative.",
                        severity="INFO",
                        timestamp=now_str,
                        metadata={"macd": macd_line[-1], "signal": sig_line[-1]}
                    )
                    self._dispatch_alert(alert)
                    alerts.append(alert)

        # 3. Volume Breakout Alert (RVOL > 2.0)
        if self.alert_configs.get(ALERT_VOLUME_BREAKOUT, True):
            volumes = [c.volume for c in candles]
            vol_res = VolumeAnalyzer.analyze(closes, volumes)
            rvol = vol_res.get("rvol", 1.0)
            if rvol >= 2.0:
                alert = SignalAlert(
                    alert_id=str(uuid.uuid4())[:8],
                    alert_type=ALERT_VOLUME_BREAKOUT,
                    symbol=sym,
                    message=f"Institutional Volume Surge (RVOL {rvol:.2f}x average volume) detected.",
                    severity="WARNING",
                    timestamp=now_str,
                    metadata={"rvol": rvol}
                )
                self._dispatch_alert(alert)
                alerts.append(alert)

        # 4. Trend Breakout Alert (Price crossing EMA 50 with momentum)
        if self.alert_configs.get(ALERT_TREND_BREAKOUT, True):
            ema_p = min(50, len(closes))
            ema_50 = TechnicalIndicators.ema(closes, ema_p)
            if ema_50 and len(closes) >= 2:
                prev_c = closes[-2]
                curr_c = closes[-1]
                prev_e = ema_50[-2]
                curr_e = ema_50[-1]

                if prev_e is not None and curr_e is not None:
                    if prev_c <= prev_e and curr_c > curr_e:
                        alert = SignalAlert(
                            alert_id=str(uuid.uuid4())[:8],
                            alert_type=ALERT_TREND_BREAKOUT,
                            symbol=sym,
                            message=f"Bullish Trend Breakout: Price crossed above EMA ({curr_e:.2f}) on {sym}.",
                            severity="WARNING",
                            timestamp=now_str,
                            metadata={"ema": curr_e}
                        )
                        self._dispatch_alert(alert)
                        alerts.append(alert)
                    elif prev_c >= prev_e and curr_c < curr_e:
                        alert = SignalAlert(
                            alert_id=str(uuid.uuid4())[:8],
                            alert_type=ALERT_TREND_BREAKOUT,
                            symbol=sym,
                            message=f"Bearish Trend Breakdown: Price dropped below EMA ({curr_e:.2f}) on {sym}.",
                            severity="WARNING",
                            timestamp=now_str,
                            metadata={"ema": curr_e}
                        )
                        self._dispatch_alert(alert)
                        alerts.append(alert)

        return alerts

    def check_news_alerts(self, article: EnrichedNewsArticle) -> Optional[SignalAlert]:
        """Check for high-impact or market-moving breaking news"""
        if not self.alert_configs.get(ALERT_HIGH_IMPACT_NEWS, True):
            return None

        if article.impact in (IMPACT_CRITICAL, IMPACT_HIGH):
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            alert = SignalAlert(
                alert_id=str(uuid.uuid4())[:8],
                alert_type=ALERT_HIGH_IMPACT_NEWS,
                symbol=article.symbol or "MACRO",
                message=f"[{article.impact}] {article.category}: {article.title} (Sentiment: {article.sentiment})",
                severity="CRITICAL" if article.impact == IMPACT_CRITICAL else "WARNING",
                timestamp=now_str,
                metadata={"url": article.url, "source": article.source}
            )
            self._dispatch_alert(alert)
            return alert

        return None

    def get_recent_alerts(self, limit: int = 50) -> List[SignalAlert]:
        """Return history of triggered alerts"""
        with self._lock:
            return list(self._alert_history[:limit])

    def clear_alerts(self):
        """Clear the alert backlog"""
        with self._lock:
            self._alert_history.clear()
