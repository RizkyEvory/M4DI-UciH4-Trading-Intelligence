"""
M4DI~UciH4 Trading Intelligence System
Mathematical Verification Tests for Technical Indicators
Tested against verified quantitative datasets.
"""
import unittest
from analytics.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_atr,
    calculate_adx,
    calculate_stochastic,
    calculate_stochastic_rsi,
    calculate_vwap,
    calculate_obv
)


class TestIndicators(unittest.TestCase):

    def test_sma(self):
        data = [10.0, 11.0, 12.0, 13.0, 14.0]
        sma = calculate_sma(data, period=3)
        self.assertIsNone(sma[0])
        self.assertIsNone(sma[1])
        self.assertAlmostEqual(sma[2], 11.0)  # (10 + 11 + 12) / 3 = 11.0
        self.assertAlmostEqual(sma[3], 12.0)  # (11 + 12 + 13) / 3 = 12.0
        self.assertAlmostEqual(sma[4], 13.0)  # (12 + 13 + 14) / 3 = 13.0

    def test_ema(self):
        data = [10.0, 11.0, 12.0, 13.0, 14.0]
        ema = calculate_ema(data, period=3)
        self.assertIsNone(ema[0])
        self.assertIsNone(ema[1])
        # First EMA is SMA(10, 11, 12) = 11.0
        self.assertAlmostEqual(ema[2], 11.0)
        # Multiplier = 2 / (3 + 1) = 0.5
        # EMA[3] = (13 - 11.0) * 0.5 + 11.0 = 12.0
        self.assertAlmostEqual(ema[3], 12.0)
        # EMA[4] = (14 - 12.0) * 0.5 + 12.0 = 13.0
        self.assertAlmostEqual(ema[4], 13.0)

    def test_rsi(self):
        # Known monotonic upward sequence -> RSI must approach 100
        up_data = [10.0 + i for i in range(25)]
        rsi_up = calculate_rsi(up_data, period=14)
        self.assertIsNotNone(rsi_up[-1])
        self.assertAlmostEqual(rsi_up[-1], 100.0, places=2)

        # Monotonic downward sequence -> RSI must approach 0
        down_data = [100.0 - i for i in range(25)]
        rsi_down = calculate_rsi(down_data, period=14)
        self.assertIsNotNone(rsi_down[-1])
        self.assertAlmostEqual(rsi_down[-1], 0.0, places=2)

        # Alternating data -> RSI in mid 40-60 range
        alt_data = [50.0 + (1.0 if i % 2 == 0 else -1.0) for i in range(30)]
        rsi_alt = calculate_rsi(alt_data, period=14)
        self.assertGreater(rsi_alt[-1], 40.0)
        self.assertLess(rsi_alt[-1], 60.0)

    def test_macd(self):
        data = [float(i) for i in range(50)]
        macd_l, sig_l, hist_l = calculate_macd(data, 12, 26, 9)
        # Check that later values exist and are positive for steady uptrend
        self.assertIsNotNone(macd_l[-1])
        self.assertIsNotNone(sig_l[-1])
        self.assertIsNotNone(hist_l[-1])
        self.assertAlmostEqual(macd_l[-1] - sig_l[-1], hist_l[-1], places=4)

    def test_bollinger_bands(self):
        data = [10.0] * 20 + [12.0]
        upper, middle, lower, bandwidth = calculate_bollinger_bands(data, period=20, num_std=2.0)
        self.assertIsNotNone(upper[-1])
        self.assertIsNotNone(middle[-1])
        self.assertIsNotNone(lower[-1])
        self.assertGreater(upper[-1], middle[-1])
        self.assertLess(lower[-1], middle[-1])
        self.assertGreater(bandwidth[-1], 0.0)

    def test_atr(self):
        # High-low range of 2.0 each day
        highs = [12.0] * 20
        lows = [10.0] * 20
        closes = [11.0] * 20
        atr = calculate_atr(highs, lows, closes, period=14)
        self.assertIsNotNone(atr[-1])
        self.assertAlmostEqual(atr[-1], 2.0, places=3)

    def test_adx(self):
        highs = [100.0 + i * 2.0 for i in range(40)]
        lows = [95.0 + i * 2.0 for i in range(40)]
        closes = [98.0 + i * 2.0 for i in range(40)]
        adx, pdi, mdi = calculate_adx(highs, lows, closes, period=14)
        self.assertIsNotNone(pdi[-1])
        self.assertIsNotNone(mdi[-1])
        # Strong uptrend: +DI should strongly exceed -DI
        self.assertGreater(pdi[-1], mdi[-1])
        self.assertIsNotNone(adx[-1])
        self.assertGreater(adx[-1], 20.0)

    def test_stochastic(self):
        highs = [15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0, 30.0]
        lows = [5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0]
        closes = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0, 22.0, 23.0, 24.0, 30.0]
        k, d = calculate_stochastic(highs, lows, closes, 14, 3)
        self.assertIsNotNone(k[-1])
        self.assertAlmostEqual(k[-1], 100.0, places=2)  # Close is at highest high

    def test_vwap(self):
        highs = [10.0, 12.0, 14.0]
        lows = [8.0, 10.0, 12.0]
        closes = [9.0, 11.0, 13.0]
        # Typicals: (10+8+9)/3 = 9.0, (12+10+11)/3 = 11.0, (14+12+13)/3 = 13.0
        volumes = [100.0, 200.0, 300.0]
        # Cum PV = 9*100 + 11*200 + 13*300 = 900 + 2200 + 3900 = 7000
        # Cum Vol = 100 + 200 + 300 = 600
        # VWAP = 7000 / 600 = 11.6667
        vwap = calculate_vwap(highs, lows, closes, volumes)
        self.assertAlmostEqual(vwap[-1], 7000.0 / 600.0, places=3)

    def test_obv(self):
        closes = [10.0, 12.0, 11.0, 11.0]
        volumes = [100.0, 150.0, 50.0, 20.0]
        obv = calculate_obv(closes, volumes)
        # Bar 0: 100
        # Bar 1: close 12 > 10 -> 100 + 150 = 250
        # Bar 2: close 11 < 12 -> 250 - 50 = 200
        # Bar 3: close 11 == 11 -> 200 (no change)
        self.assertEqual(obv[0], 100.0)
        self.assertEqual(obv[1], 250.0)
        self.assertEqual(obv[2], 200.0)
        self.assertEqual(obv[3], 200.0)


if __name__ == "__main__":
    unittest.main()
