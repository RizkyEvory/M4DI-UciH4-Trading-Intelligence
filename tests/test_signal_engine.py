"""
M4DI~UciH4 Trading Intelligence System
Trading Signal Engine Unit & Integration Tests (Phase 4)
Verifies multi-factor quantitative scoring, confidence calculation, institutional signal generation
(Strong Buy, Buy, Neutral, Sell, Strong Sell), Stop Loss / Take Profit 1 & 2 risk-reward math,
and configurable event alerts (RSI extreme, MACD cross, volume breakouts, high impact news).
"""
import unittest
from datetime import datetime, timedelta

from config.constants import (
    SIGNAL_STRONG_BUY,
    SIGNAL_BUY,
    SIGNAL_NEUTRAL,
    SIGNAL_SELL,
    SIGNAL_STRONG_SELL,
    ALERT_STRONG_BUY,
    ALERT_STRONG_SELL,
    ALERT_RSI_EXTREME,
    ALERT_MACD_CROSSOVER,
    ALERT_VOLUME_BREAKOUT,
    ALERT_HIGH_IMPACT_NEWS,
    IMPACT_CRITICAL,
    SENTIMENT_POSITIVE,
    SENTIMENT_NEGATIVE
)
from api.models import NormalizedCandle
from news.models import EnrichedNewsArticle
from signals.models import TradingSignal, SignalAlert
from signals.scoring_engine import SignalScoringEngine
from signals.confidence_engine import SignalConfidenceEngine
from signals.signal_generator import SignalGenerator
from signals.alerts_engine import AlertsEngine


def _generate_synthetic_candles(trend: str = "bullish", count: int = 40, base_price: float = 100.0):
    """Helper to generate structurally consistent candles for tests"""
    candles = []
    price = base_price
    start_time = datetime(2026, 3, 1, 9, 30)

    for i in range(count):
        ts = (start_time + timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S")
        if trend == "bullish":
            op = price
            cl = price + 1.2
            hi = cl + 0.5
            lo = op - 0.3
            vol = 15000.0 + (i * 100)
            price = cl
        elif trend == "bearish":
            op = price
            cl = price - 1.2
            hi = op + 0.3
            lo = cl - 0.5
            vol = 15000.0 + (i * 100)
            price = cl
        else:
            # Neutral / sideways
            op = price
            cl = price + (0.4 if i % 2 == 0 else -0.4)
            hi = max(op, cl) + 0.2
            lo = min(op, cl) - 0.2
            vol = 10000.0
            price = cl

        candles.append(NormalizedCandle(
            symbol="TEST",
            timeframe="1h",
            open=round(op, 2),
            high=round(hi, 2),
            low=round(lo, 2),
            close=round(cl, 2),
            volume=vol,
            timestamp=ts
        ))
    return candles


class TestSignalScoring(unittest.TestCase):
    """Test multi-factor quantitative scoring (Technical, Fundamental, Risk)"""

    def test_bullish_scoring(self):
        candles = _generate_synthetic_candles(trend="bullish", count=40, base_price=100.0)
        news_profile = {
            "symbol": "TEST",
            "sentiment": SENTIMENT_POSITIVE,
            "sentiment_score": 0.85,
            "article_count": 5,
            "has_critical_news": True
        }

        engine = SignalScoringEngine()
        breakdown, reasons = engine.calculate_score(candles, news_profile)

        self.assertGreater(breakdown.technical_score, 20.0)
        self.assertGreater(breakdown.fundamental_score, 50.0)
        self.assertGreater(breakdown.composite_score, 30.0)
        self.assertTrue(len(reasons) >= 3)
        self.assertTrue(any("Bullish" in r for r in reasons))

    def test_bearish_scoring(self):
        candles = _generate_synthetic_candles(trend="bearish", count=40, base_price=200.0)
        news_profile = {
            "symbol": "TEST",
            "sentiment": SENTIMENT_NEGATIVE,
            "sentiment_score": -0.85,
            "article_count": 4,
            "has_critical_news": True
        }

        engine = SignalScoringEngine()
        breakdown, reasons = engine.calculate_score(candles, news_profile)

        self.assertLess(breakdown.technical_score, -20.0)
        self.assertLess(breakdown.fundamental_score, -50.0)
        self.assertLess(breakdown.composite_score, -30.0)
        self.assertTrue(any("Bearish" in r for r in reasons))

    def test_custom_weights(self):
        candles = _generate_synthetic_candles(trend="bullish", count=30)
        # Heavy technical weight (0.80)
        engine = SignalScoringEngine(custom_weights={"technical": 0.80, "fundamental": 0.10, "risk": 0.10})
        breakdown, _ = engine.calculate_score(candles)
        self.assertAlmostEqual(breakdown.weights["technical"], 0.80, delta=0.01)


class TestSignalConfidence(unittest.TestCase):
    """Test model confidence calculations and agreement metrics"""

    def test_confidence_bullish_alignment(self):
        # All indicators agree and news confirms
        sub_metrics = {
            "ema_20": 110.0,
            "ema_50": 105.0,
            "rsi": 58.0,
            "macd": 1.5,
            "macd_signal": 0.8,
            "rvol": 1.8
        }
        conf = SignalConfidenceEngine.calculate_confidence(
            technical_score=60.0,
            sub_metrics=sub_metrics,
            mtf_confluence_score=75.0,
            news_sentiment_score=0.70,
            candle_count=60
        )
        self.assertGreaterEqual(conf.overall, 65.0)
        self.assertGreaterEqual(conf.indicator_agreement, 70.0)
        self.assertGreaterEqual(conf.news_confirmation, 70.0)

    def test_confidence_divergence_penalty(self):
        # Technical is Bullish (+60), but news is heavily Bearish (-0.85)
        sub_metrics = {"ema_20": 110.0, "ema_50": 105.0, "rsi": 55.0}
        conf = SignalConfidenceEngine.calculate_confidence(
            technical_score=60.0,
            sub_metrics=sub_metrics,
            mtf_confluence_score=20.0,
            news_sentiment_score=-0.85,
            candle_count=50
        )
        # News confirmation should be penalized (< 40%)
        self.assertLess(conf.news_confirmation, 40.0)


class TestSignalGenerator(unittest.TestCase):
    """Test full institutional signal generation with SL / TP1 / TP2 math"""

    def test_strong_buy_generation(self):
        candles = _generate_synthetic_candles(trend="bullish", count=45, base_price=150.0)
        news_profile = {
            "symbol": "TEST",
            "sentiment": SENTIMENT_POSITIVE,
            "sentiment_score": 0.90,
            "article_count": 6,
            "has_critical_news": True
        }

        generator = SignalGenerator()
        sig = generator.generate_signal(
            symbol="TEST",
            candles=candles,
            timeframe="1h",
            news_profile=news_profile
        )

        self.assertIn(sig.signal, [SIGNAL_STRONG_BUY, SIGNAL_BUY])
        self.assertGreater(sig.score, 25.0)
        self.assertGreater(sig.confidence, 50.0)

        # Risk parameters
        self.assertGreater(sig.entry_price, 0.0)
        self.assertLess(sig.stop_loss, sig.entry_price)
        self.assertGreater(sig.take_profit_1, sig.entry_price)
        self.assertGreater(sig.take_profit_2, sig.take_profit_1)
        self.assertGreaterEqual(sig.risk_reward, 1.4)
        self.assertTrue(len(sig.reasons) > 0)

    def test_strong_sell_generation(self):
        candles = _generate_synthetic_candles(trend="bearish", count=45, base_price=300.0)
        news_profile = {
            "symbol": "TEST",
            "sentiment": SENTIMENT_NEGATIVE,
            "sentiment_score": -0.90,
            "article_count": 6,
            "has_critical_news": True
        }

        generator = SignalGenerator()
        sig = generator.generate_signal(
            symbol="TEST",
            candles=candles,
            timeframe="1h",
            news_profile=news_profile
        )

        self.assertIn(sig.signal, [SIGNAL_STRONG_SELL, SIGNAL_SELL])
        self.assertLess(sig.score, -25.0)

        # Risk parameters for SELL
        self.assertGreater(sig.stop_loss, sig.entry_price)
        self.assertLess(sig.take_profit_1, sig.entry_price)
        self.assertLess(sig.take_profit_2, sig.take_profit_1)
        self.assertGreaterEqual(sig.risk_reward, 1.4)

    def test_neutral_signal_generation(self):
        candles = _generate_synthetic_candles(trend="neutral", count=40, base_price=100.0)
        generator = SignalGenerator()
        sig = generator.generate_signal("TEST", candles, timeframe="1h")
        self.assertEqual(sig.signal, SIGNAL_NEUTRAL)


class TestAlertsEngine(unittest.TestCase):
    """Test real-time alert triggers across signals, technicals, and news"""

    def setUp(self):
        self.alerts_engine = AlertsEngine()
        self.captured_alerts = []
        self.alerts_engine.register_listener(lambda a: self.captured_alerts.append(a))

    def test_strong_buy_alert(self):
        sig = TradingSignal(
            symbol="XAU/USD",
            signal=SIGNAL_STRONG_BUY,
            confidence=85.0,
            score=72.0,
            entry_price=2650.0,
            stop_loss=2635.0,
            take_profit_1=2675.0
        )
        fired = self.alerts_engine.check_signal_alerts(sig)
        self.assertEqual(len(fired), 1)
        self.assertEqual(fired[0].alert_type, ALERT_STRONG_BUY)
        self.assertEqual(len(self.captured_alerts), 1)

    def test_rsi_extreme_alert(self):
        # Generate candles with steep drop leading to RSI < 25
        candles = _generate_synthetic_candles(trend="bearish", count=30, base_price=100.0)
        # Progressive drop in last 10 bars
        for i in range(10):
            candles[-10 + i].close = candles[-10 + i].close - (i * 5.0)
            candles[-10 + i].high = candles[-10 + i].close + 0.5
            candles[-10 + i].low = candles[-10 + i].close - 1.0

        fired = self.alerts_engine.check_technical_alerts("TEST", candles)
        self.assertTrue(any(a.alert_type == ALERT_RSI_EXTREME for a in fired))

    def test_volume_breakout_alert(self):
        candles = _generate_synthetic_candles(trend="neutral", count=25)
        # 10x volume spike on last bar
        candles[-1].volume = candles[0].volume * 10.0

        fired = self.alerts_engine.check_technical_alerts("TEST", candles)
        self.assertTrue(any(a.alert_type == ALERT_VOLUME_BREAKOUT for a in fired))

    def test_high_impact_news_alert(self):
        article = EnrichedNewsArticle(
            title="BREAKING: Emergency Central Bank Rate Hike",
            category="Interest rates",
            impact=IMPACT_CRITICAL,
            impact_score=92.0,
            sentiment="NEGATIVE"
        )
        alert = self.alerts_engine.check_news_alerts(article)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.alert_type, ALERT_HIGH_IMPACT_NEWS)

    def test_alert_configuration_toggle(self):
        # Disable Strong Buy alert
        self.alerts_engine.configure_alert(ALERT_STRONG_BUY, False)
        sig = TradingSignal(symbol="AAPL", signal=SIGNAL_STRONG_BUY, confidence=80.0)
        fired = self.alerts_engine.check_signal_alerts(sig)
        self.assertEqual(len(fired), 0)


if __name__ == "__main__":
    unittest.main()
