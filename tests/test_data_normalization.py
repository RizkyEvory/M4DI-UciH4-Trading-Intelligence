"""
M4DI~UciH4 Trading Intelligence System
Tests for Data Normalization Models
"""
import unittest
from api.models import (
    NormalizedQuote,
    NormalizedCandle,
    NormalizedNews,
    NormalizedCompany,
    NormalizedSymbol
)


class TestDataNormalization(unittest.TestCase):
    def test_quote_normalization(self):
        quote = NormalizedQuote(
            symbol="AAPL",
            bid=260.10,
            ask=260.15,
            last=260.12,
            open=258.00,
            high=261.00,
            low=257.50,
            close=257.00,
            volume=45000000.0,
            change=3.12,
            change_percent=1.21,
            timestamp="2026-03-20 15:30:00",
            provider_source="Finnhub"
        )
        d = quote.to_dict()
        self.assertEqual(d["symbol"], "AAPL")
        self.assertEqual(d["last"], 260.12)
        self.assertEqual(d["change"], 3.12)

        restored = NormalizedQuote.from_dict(d)
        self.assertEqual(restored.symbol, "AAPL")
        self.assertEqual(restored.last, 260.12)
        self.assertEqual(restored.provider_source, "Finnhub")

    def test_candle_normalization(self):
        candle = NormalizedCandle(
            symbol="XAUUSD",
            timeframe="H1",
            open=2650.0,
            high=2665.5,
            low=2648.2,
            close=2662.0,
            volume=14200.0,
            timestamp="2026-03-20 12:00:00"
        )
        d = candle.to_dict()
        self.assertEqual(d["symbol"], "XAUUSD")
        self.assertEqual(d["high"], 2665.5)

        restored = NormalizedCandle.from_dict(d)
        self.assertEqual(restored.close, 2662.0)
        self.assertEqual(restored.timeframe, "H1")

    def test_news_normalization(self):
        news = NormalizedNews(
            title="Fed Rate Decision Cuts 25bps",
            description="Federal Open Market Committee lowers rates.",
            content="Full statement details...",
            url="https://example.com/news/1",
            source="Reuters",
            author="Macro Team",
            published_at="2026-03-20 14:00:00",
            category="macro",
            sentiment="bullish",
            provider_source="NewsAPI.org"
        )
        d = news.to_dict()
        self.assertEqual(d["title"], "Fed Rate Decision Cuts 25bps")
        self.assertEqual(d["source"], "Reuters")

        restored = NormalizedNews.from_dict(d)
        self.assertEqual(restored.url, "https://example.com/news/1")

    def test_company_normalization(self):
        comp = NormalizedCompany(
            symbol="NVDA",
            name="NVIDIA Corporation",
            exchange="NASDAQ",
            currency="USD",
            country="US",
            industry="Semiconductors",
            market_cap=3500000.0,
            website="https://nvidia.com",
            provider_source="Finnhub"
        )
        d = comp.to_dict()
        self.assertEqual(d["name"], "NVIDIA Corporation")
        self.assertEqual(d["market_cap"], 3500000.0)

        restored = NormalizedCompany.from_dict(d)
        self.assertEqual(restored.industry, "Semiconductors")

    def test_symbol_normalization(self):
        sym = NormalizedSymbol(
            symbol="EUR/USD",
            name="Euro / US Dollar",
            type="Forex",
            exchange="FX",
            currency="USD",
            provider_source="Twelve Data"
        )
        d = sym.to_dict()
        self.assertEqual(d["symbol"], "EUR/USD")
        self.assertEqual(d["type"], "Forex")


if __name__ == "__main__":
    unittest.main()
