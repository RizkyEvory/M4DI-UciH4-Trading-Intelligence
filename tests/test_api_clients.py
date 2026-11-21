"""
M4DI~UciH4 Trading Intelligence System
Tests for Finnhub, Twelve Data, and NewsAPI Clients using Mock HTTP Responses
"""
import unittest
from unittest.mock import MagicMock, patch
import requests

from api.finnhub_client import FinnhubClient
from api.twelve_data_client import TwelveDataClient
from api.newsapi_client import NewsApiClient
from api.exceptions import (
    ApiRateLimitException,
    ApiAuthenticationException,
    ApiProviderDownException,
    ApiNetworkTimeoutException,
    ApiInvalidResponseException
)


class TestApiClients(unittest.TestCase):

    # ==========================================
    # FINNHUB TESTS
    # ==========================================

    @patch("requests.Session.request")
    def test_finnhub_get_quote(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "c": 260.14, "d": 3.12, "dp": 1.21, "h": 261.0,
            "l": 258.0, "o": 258.5, "pc": 257.02, "t": 1700000000
        }
        mock_request.return_value = mock_resp

        client = FinnhubClient()
        quote = client.get_quote("AAPL")

        self.assertEqual(quote.symbol, "AAPL")
        self.assertEqual(quote.last, 260.14)
        self.assertEqual(quote.open, 258.5)
        self.assertEqual(quote.change, 3.12)
        self.assertEqual(quote.change_percent, 1.21)

    @patch("requests.Session.request")
    def test_finnhub_company_profile(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "name": "Apple Inc", "ticker": "AAPL", "currency": "USD",
            "finnhubIndustry": "Technology", "marketCapitalization": 3000000.0,
            "weburl": "https://apple.com"
        }
        mock_request.return_value = mock_resp

        client = FinnhubClient()
        profile = client.get_company_profile("AAPL")

        self.assertEqual(profile.name, "Apple Inc")
        self.assertEqual(profile.industry, "Technology")
        self.assertEqual(profile.market_cap, 3000000.0)

    @patch("requests.Session.request")
    def test_finnhub_candles(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "s": "ok",
            "o": [250.0, 252.0],
            "h": [255.0, 256.0],
            "l": [249.0, 251.0],
            "c": [253.0, 255.5],
            "v": [10000, 15000],
            "t": [1700000000, 1700086400]
        }
        mock_request.return_value = mock_resp

        client = FinnhubClient()
        candles = client.get_candles("AAPL", resolution="D")

        self.assertEqual(len(candles), 2)
        self.assertEqual(candles[0].open, 250.0)
        self.assertEqual(candles[1].close, 255.5)

    @patch("requests.Session.request")
    def test_finnhub_market_news(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [
            {
                "headline": "Markets Rally on Tech Earnings",
                "summary": "Nasdaq leads broad surge...",
                "url": "https://example.com/1",
                "source": "Bloomberg",
                "datetime": 1700000000
            }
        ]
        mock_request.return_value = mock_resp

        client = FinnhubClient()
        news = client.get_market_news("general")

        self.assertEqual(len(news), 1)
        self.assertEqual(news[0].title, "Markets Rally on Tech Earnings")
        self.assertEqual(news[0].source, "Bloomberg")

    # ==========================================
    # TWELVE DATA TESTS
    # ==========================================

    @patch("requests.Session.request")
    def test_twelve_data_get_quote(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "symbol": "XAU/USD", "name": "Gold / US Dollar",
            "open": "2650.10", "high": "2665.80", "low": "2642.50",
            "close": "2658.20", "volume": "154200", "change": "10.20",
            "percent_change": "0.385", "datetime": "2026-03-20"
        }
        mock_request.return_value = mock_resp

        client = TwelveDataClient()
        quote = client.get_quote("XAU/USD")

        self.assertEqual(quote.symbol, "XAU/USD")
        self.assertEqual(quote.last, 2658.20)
        self.assertEqual(quote.open, 2650.10)
        self.assertEqual(quote.change, 10.20)

    @patch("requests.Session.request")
    def test_twelve_data_time_series(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "ok",
            "values": [
                {"datetime": "2026-03-20", "open": "2650.0", "high": "2660.0", "low": "2645.0", "close": "2655.0", "volume": "1000"},
                {"datetime": "2026-03-19", "open": "2640.0", "high": "2652.0", "low": "2638.0", "close": "2648.0", "volume": "900"}
            ]
        }
        mock_request.return_value = mock_resp

        client = TwelveDataClient()
        candles = client.get_time_series("XAU/USD", interval="1day", outputsize=2)

        self.assertEqual(len(candles), 2)
        # Chronological order checks
        self.assertEqual(candles[0].open, 2640.0)
        self.assertEqual(candles[1].close, 2655.0)

    @patch("requests.Session.request")
    def test_twelve_data_indicator(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "ok",
            "values": [{"datetime": "2026-03-20", "rsi": "58.42"}]
        }
        mock_request.return_value = mock_resp

        client = TwelveDataClient()
        ind = client.get_technical_indicator("XAU/USD", indicator="rsi", time_period=14)
        self.assertEqual(ind["status"], "ok")

    # ==========================================
    # NEWSAPI TESTS
    # ==========================================

    @patch("requests.Session.request")
    def test_newsapi_get_everything(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "ok",
            "totalResults": 1,
            "articles": [
                {
                    "source": {"id": "reuters", "name": "Reuters"},
                    "title": "ECB Signals Rate Stabilization",
                    "description": "European Central Bank notes easing inflationary pressures.",
                    "url": "https://example.com/ecb",
                    "publishedAt": "2026-03-20T10:00:00Z"
                }
            ]
        }
        mock_request.return_value = mock_resp

        client = NewsApiClient()
        news = client.get_everything("ECB")

        self.assertEqual(len(news), 1)
        self.assertEqual(news[0].title, "ECB Signals Rate Stabilization")
        self.assertEqual(news[0].source, "Reuters")
        self.assertEqual(news[0].published_at, "2026-03-20 10:00:00")

    # ==========================================
    # ERROR & FAULT HANDLING TESTS
    # ==========================================

    @patch("requests.Session.request")
    def test_http_429_rate_limit(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.headers = {"Retry-After": "30"}
        mock_request.return_value = mock_resp

        client = FinnhubClient()
        with self.assertRaises(ApiRateLimitException):
            client.get_quote("AAPL")

    @patch("requests.Session.request")
    def test_http_401_unauthorized(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Invalid API token"
        mock_request.return_value = mock_resp

        client = FinnhubClient()
        with self.assertRaises(ApiAuthenticationException):
            client.get_quote("AAPL")

    @patch("requests.Session.request")
    def test_http_500_provider_down(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_request.return_value = mock_resp

        client = TwelveDataClient()
        with self.assertRaises(ApiProviderDownException):
            client.get_quote("EUR/USD")

    @patch("requests.Session.request")
    def test_network_timeout(self, mock_request):
        mock_request.side_effect = requests.Timeout("Gateway timed out")

        client = NewsApiClient()
        with self.assertRaises(ApiNetworkTimeoutException):
            client.get_top_headlines()

    @patch("requests.Session.request")
    def test_invalid_json_response(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("Malformed JSON payload")
        mock_resp.text = "<html>502 Bad Gateway</html>"
        mock_request.return_value = mock_resp

        client = FinnhubClient()
        with self.assertRaises(ApiInvalidResponseException):
            client.get_quote("AAPL")


if __name__ == "__main__":
    unittest.main()
