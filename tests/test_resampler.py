"""
M4DI~UciH4 Trading Intelligence System
Tests for Mathematical OHLCV Resampler
"""
import unittest
from api.models import NormalizedCandle
from engine.resampler import Resampler


class TestResampler(unittest.TestCase):

    def test_resample_1m_to_5m(self):
        # 5 consecutive 1-minute bars in same 5-minute bucket (12:00 to 12:04)
        c1 = NormalizedCandle("XAUUSD", "1m", open=2000.0, high=2005.0, low=1998.0, close=2002.0, volume=10.0, timestamp="2026-03-20 12:00:00")
        c2 = NormalizedCandle("XAUUSD", "1m", open=2002.0, high=2010.0, low=2001.0, close=2008.0, volume=20.0, timestamp="2026-03-20 12:01:00")
        c3 = NormalizedCandle("XAUUSD", "1m", open=2008.0, high=2012.0, low=2005.0, close=2006.0, volume=15.0, timestamp="2026-03-20 12:02:00")
        c4 = NormalizedCandle("XAUUSD", "1m", open=2006.0, high=2007.0, low=1995.0, close=1999.0, volume=30.0, timestamp="2026-03-20 12:03:00")
        c5 = NormalizedCandle("XAUUSD", "1m", open=1999.0, high=2003.0, low=1997.0, close=2001.0, volume=25.0, timestamp="2026-03-20 12:04:00")

        resampled = Resampler.resample([c1, c2, c3, c4, c5], target_timeframe="5m", source_timeframe="1m")

        self.assertEqual(len(resampled), 1)
        r = resampled[0]
        self.assertEqual(r.open, 2000.0)      # First bar open
        self.assertEqual(r.high, 2012.0)      # Max of highs (c3)
        self.assertEqual(r.low, 1995.0)       # Min of lows (c4)
        self.assertEqual(r.close, 2001.0)     # Last bar close (c5)
        self.assertEqual(r.volume, 100.0)     # 10 + 20 + 15 + 30 + 25 = 100.0
        self.assertEqual(r.timeframe, "5m")

    def test_downsample_rejection(self):
        # Trying to downsample a 1h bar into a 5m bar should raise ValueError
        c_1h = NormalizedCandle("XAUUSD", "1h", open=2000.0, high=2010.0, low=1990.0, close=2005.0, volume=100.0, timestamp="2026-03-20 12:00:00")
        with self.assertRaises(ValueError):
            Resampler.resample([c_1h], target_timeframe="5m", source_timeframe="1h")


if __name__ == "__main__":
    unittest.main()
