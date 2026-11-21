"""
M4DI~UciH4 Trading Intelligence System
Tests for Trend, Volatility, Volume, and Technical Score Engines
"""
import unittest
from analytics.trend import TrendAnalyzer
from analytics.volatility import VolatilityAnalyzer
from analytics.volume import VolumeAnalyzer
from analytics.technical_score import TechnicalScoreCalculator
from config.constants import (
    TREND_STRONG_BULLISH,
    TREND_STRONG_BEARISH,
    TREND_BULLISH,
    TREND_BEARISH,
    TREND_NEUTRAL,
    VOLATILITY_LOW,
    VOLATILITY_NORMAL,
    VOLATILITY_HIGH,
    VOLATILITY_EXTREME
)


class TestTrendVolatilityVolume(unittest.TestCase):

    def test_market_structure_hh_hl(self):
        # Stepping stairs uptrend
        highs = [10, 15, 12, 18, 14, 22, 19, 25, 20]
        lows =  [ 8, 11,  9, 13, 10, 16, 15, 18, 16]
        struct = TrendAnalyzer.detect_market_structure(highs, lows, window=1)
        self.assertIn("structure_bias", struct)
        self.assertIn("swing_highs", struct)

    def test_trend_analyzer_bullish(self):
        # Continuous strong upward trend
        highs = [100.0 + i * 2.0 for i in range(50)]
        lows = [95.0 + i * 2.0 for i in range(50)]
        closes = [98.0 + i * 2.0 for i in range(50)]
        res = TrendAnalyzer.analyze(highs, lows, closes)
        self.assertIn("BULLISH", res["overall_trend"])
        self.assertGreater(res["trend_strength"], 50.0)

    def test_volatility_analyzer(self):
        # Stable low-volatility prices
        highs = [100.2] * 30
        lows = [99.8] * 30
        closes = [100.0] * 30
        res = VolatilityAnalyzer.analyze(highs, lows, closes)
        self.assertEqual(res["regime"], VOLATILITY_LOW)

        # Extreme wild volatility prices
        highs_wild = [100.0 + (i * 10 if i % 2 == 0 else -10) for i in range(30)]
        lows_wild = [h - 8.0 for h in highs_wild]
        closes_wild = [h - 4.0 for h in highs_wild]
        res_wild = VolatilityAnalyzer.analyze(highs_wild, lows_wild, closes_wild)
        self.assertIn(res_wild["regime"], (VOLATILITY_HIGH, VOLATILITY_EXTREME))

    def test_volume_analyzer(self):
        closes = [10.0, 11.0, 12.0, 13.0, 14.0]
        volumes = [100.0, 100.0, 100.0, 100.0, 300.0]  # Last volume is 3x avg
        res = VolumeAnalyzer.analyze(closes, volumes, avg_period=4)
        self.assertTrue(res["volume_breakout"])
        self.assertGreater(res["rvol"], 2.0)
        self.assertEqual(res["volume_confirmation"], "BULLISH_CONFIRMATION")

    def test_technical_score_calculator(self):
        # Bullish confluence
        trend_bull = {"overall_trend": TREND_STRONG_BULLISH, "trend_strength": 90.0}
        vol_normal = {"regime": VOLATILITY_NORMAL}
        vol_bull = {"volume_confirmation": "BULLISH_CONFIRMATION", "rvol": 1.5}
        score_bull = TechnicalScoreCalculator.calculate_score(
            trend_info=trend_bull,
            rsi_val=60.0,
            macd_hist=0.5,
            volatility_info=vol_normal,
            volume_info=vol_bull
        )
        self.assertGreater(score_bull, 75.0)

        # Bearish confluence
        trend_bear = {"overall_trend": TREND_STRONG_BEARISH, "trend_strength": 90.0}
        vol_bear = {"volume_confirmation": "BEARISH_CONFIRMATION", "rvol": 1.5}
        score_bear = TechnicalScoreCalculator.calculate_score(
            trend_info=trend_bear,
            rsi_val=40.0,
            macd_hist=-0.5,
            volatility_info=vol_normal,
            volume_info=vol_bear
        )
        self.assertLess(score_bear, 30.0)


if __name__ == "__main__":
    unittest.main()
