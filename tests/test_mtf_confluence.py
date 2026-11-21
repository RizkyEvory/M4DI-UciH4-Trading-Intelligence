"""
M4DI~UciH4 Trading Intelligence System
Tests for Multi-Timeframe Confluence Engine
"""
import unittest
from api.models import NormalizedCandle
from analytics.mtf import MultiTimeframeAnalyzer


class TestMtfConfluence(unittest.TestCase):

    def _generate_trend_candles(self, count: int, slope: float, base: float = 100.0, tf: str = "1d") -> list:
        candles = []
        for i in range(count):
            c_price = base + (i * slope)
            day = (i // 24) + 1
            hour = i % 24
            candles.append(NormalizedCandle(
                symbol="TEST",
                timeframe=tf,
                open=c_price - 1.0,
                high=c_price + 2.0,
                low=c_price - 2.0,
                close=c_price + 1.0,
                volume=1000.0,
                timestamp=f"2026-01-{day:02d} {hour:02d}:00:00"
            ))
        return candles

    def test_strong_bullish_confluence(self):
        # All timeframes trending upward with slope +2.0
        tf_map = {
            "5m": self._generate_trend_candles(30, 2.0, tf="5m"),
            "15m": self._generate_trend_candles(30, 2.0, tf="15m"),
            "1h": self._generate_trend_candles(30, 2.0, tf="1h"),
            "4h": self._generate_trend_candles(30, 2.0, tf="4h"),
            "1d": self._generate_trend_candles(30, 2.0, tf="1d"),
            "1w": self._generate_trend_candles(30, 2.0, tf="1w"),
        }
        res = MultiTimeframeAnalyzer.analyze_confluence(tf_map)
        self.assertIn("confluence_score", res)
        self.assertGreater(res["confluence_score"], 60.0)
        self.assertIn("BULLISH", res["alignment_status"])

    def test_counter_trend_pullback(self):
        # HTF (1d, 1w) are Bullish (+2.0), but LTF (5m, 15m) are in pullback (-2.0)
        tf_map = {
            "5m": self._generate_trend_candles(30, -2.0, base=200.0, tf="5m"),
            "15m": self._generate_trend_candles(30, -2.0, base=200.0, tf="15m"),
            "1h": self._generate_trend_candles(30, 1.0, base=150.0, tf="1h"),
            "1d": self._generate_trend_candles(30, 2.0, base=100.0, tf="1d"),
            "1w": self._generate_trend_candles(30, 2.0, base=100.0, tf="1w"),
        }
        res = MultiTimeframeAnalyzer.analyze_confluence(tf_map)
        self.assertIn("PULLBACK", res["alignment_status"])


if __name__ == "__main__":
    unittest.main()
