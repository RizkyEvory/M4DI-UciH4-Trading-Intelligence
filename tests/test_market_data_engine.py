"""
M4DI~UciH4 Trading Intelligence System
Tests for Market Data Manager & Scanner Engine
"""
import unittest
from unittest.mock import MagicMock
from api.models import NormalizedQuote, NormalizedCandle
from engine.market_data_engine import MarketDataManager
from engine.scanner_engine import MarketScannerEngine


class TestMarketDataEngine(unittest.TestCase):

    def setUp(self):
        self.mock_ctx = MagicMock()
        # Mock twelve data client
        self.mock_ctx.twelve_data.get_quote.return_value = NormalizedQuote("XAU/USD", bid=2650.0, ask=2650.5, last=2650.2, close=2640.0)
        # Mock finnhub client
        self.mock_ctx.finnhub.get_quote.return_value = NormalizedQuote("AAPL", bid=250.0, ask=250.2, last=250.1, close=248.0)

        # Mock candles generator
        def mock_candles(sym, timeframe="1d", count=60):
            return [
                NormalizedCandle(sym, timeframe, open=100.0 + i, high=105.0 + i, low=98.0 + i, close=103.0 + i, volume=5000.0, timestamp=f"2026-03-{min(28, 1 + i):02d} 10:00:00")
                for i in range(count)
            ]
        self.mock_ctx.twelve_data.get_time_series.side_effect = lambda sym, interval, outputsize: mock_candles(sym, interval, outputsize)
        self.mock_ctx.finnhub.get_candles.side_effect = lambda sym, resolution: mock_candles(sym, resolution, 60)

        self.mdm = MarketDataManager(self.mock_ctx)
        self.scanner = MarketScannerEngine(self.mdm)

    def test_quote_routing(self):
        # Forex / Gold routes to Twelve Data
        q_gold = self.mdm.get_quote("XAU/USD")
        self.assertEqual(q_gold.symbol, "XAU/USD")
        self.mock_ctx.twelve_data.get_quote.assert_called_with("XAU/USD")

        # Equity routes to Finnhub
        q_aapl = self.mdm.get_quote("AAPL")
        self.assertEqual(q_aapl.symbol, "AAPL")
        self.mock_ctx.finnhub.get_quote.assert_called_with("AAPL")

    def test_scanner_engine_execution(self):
        results = self.scanner.scan_symbols(["XAU/USD", "AAPL"])
        self.assertEqual(len(results), 2)
        r = results[0]
        self.assertIn("symbol", r)
        self.assertIn("technical_score", r)
        self.assertIn("rsi", r)
        self.assertIn("trend", r)
        self.assertIn("volatility", r)

    def test_scanner_filters(self):
        # Filter for bullish only
        results = self.scanner.scan_symbols(
            ["XAU/USD", "AAPL"],
            filters={"trend": "BULLISH", "rsi_min": 30.0, "rsi_max": 90.0}
        )
        self.assertTrue(all("BULLISH" in r["trend"] for r in results))


if __name__ == "__main__":
    unittest.main()
