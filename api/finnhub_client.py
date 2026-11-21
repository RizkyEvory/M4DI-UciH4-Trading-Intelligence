"""
M4DI~UciH4 Trading Intelligence System
Finnhub Institutional API Client
Covers Quotes, Profiles, Historical Candles, Market & Company News, Symbol Search, and Metrics.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from config.constants import (
    PROVIDER_FINNHUB,
    CACHE_TTL_QUOTE,
    CACHE_TTL_CANDLE,
    CACHE_TTL_COMPANY,
    CACHE_TTL_NEWS,
    CACHE_TTL_SEARCH
)
from api.base_client import BaseApiClient
from api.models import (
    NormalizedQuote,
    NormalizedCandle,
    NormalizedNews,
    NormalizedCompany,
    NormalizedSymbol
)
from api.cache import (
    make_quote_key,
    make_candle_key,
    make_company_key,
    make_news_key,
    make_search_key
)
from core.logger import get_app_logger

logger = get_app_logger("FinnhubClient")


class FinnhubClient(BaseApiClient):
    """Finnhub Market Data Client with Data Normalization"""

    def __init__(
        self,
        base_url: str = "https://finnhub.io/api/v1",
        rate_limiter=None,
        key_rotation=None,
        health_monitor=None,
        cache=None
    ):
        super().__init__(
            provider_name=PROVIDER_FINNHUB,
            base_url=base_url,
            rate_limiter=rate_limiter,
            key_rotation=key_rotation,
            health_monitor=health_monitor,
            cache=cache,
            timeout_sec=10.0
        )

    def _inject_auth(self, params: Dict[str, Any], headers: Dict[str, str], api_key: Optional[str]):
        """Finnhub authentication passes 'token' in query parameters"""
        if api_key:
            params["token"] = api_key
        return params, headers

    def test_connection(self, override_api_key: Optional[str] = None) -> bool:
        """Test API connection with a lightweight ping to /quote"""
        try:
            res = self.request(
                method="GET",
                endpoint="quote",
                params={"symbol": "AAPL"},
                override_api_key=override_api_key
            )
            return isinstance(res, dict) and "c" in res
        except Exception as e:
            logger.warning(f"Finnhub connection test failed: {e}")
            raise

    def get_quote(self, symbol: str) -> NormalizedQuote:
        """Retrieve real-time stock quote and normalize"""
        sym = symbol.upper().strip()
        cache_key = make_quote_key(PROVIDER_FINNHUB, sym)

        data = self.request(
            method="GET",
            endpoint="quote",
            params={"symbol": sym},
            cache_key=cache_key,
            cache_ttl=CACHE_TTL_QUOTE
        )

        # Finnhub keys: c=current, d=change, dp=percent, h=high, l=low, o=open, pc=prev_close, t=timestamp
        last_price = float(data.get("c", 0.0) or 0.0)
        open_price = float(data.get("o", 0.0) or 0.0)
        high_price = float(data.get("h", 0.0) or 0.0)
        low_price = float(data.get("l", 0.0) or 0.0)
        prev_close = float(data.get("pc", 0.0) or 0.0)
        change_val = float(data.get("d", 0.0) or 0.0)
        change_pct = float(data.get("dp", 0.0) or 0.0)
        raw_ts = data.get("t")
        if raw_ts:
            ts_str = datetime.fromtimestamp(raw_ts).strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return NormalizedQuote(
            symbol=sym,
            bid=last_price,
            ask=last_price,
            last=last_price,
            open=open_price,
            high=high_price,
            low=low_price,
            close=prev_close,
            volume=0.0,
            change=change_val,
            change_percent=change_pct,
            timestamp=ts_str,
            provider_source=PROVIDER_FINNHUB
        )

    def get_company_profile(self, symbol: str) -> NormalizedCompany:
        """Fetch fundamental company profile and normalize"""
        sym = symbol.upper().strip()
        cache_key = make_company_key(PROVIDER_FINNHUB, sym)

        data = self.request(
            method="GET",
            endpoint="stock/profile2",
            params={"symbol": sym},
            cache_key=cache_key,
            cache_ttl=CACHE_TTL_COMPANY
        )

        return NormalizedCompany(
            symbol=sym,
            name=data.get("name", sym),
            exchange=data.get("exchange", ""),
            currency=data.get("currency", "USD"),
            country=data.get("country", ""),
            industry=data.get("finnhubIndustry", ""),
            sector="",
            market_cap=float(data.get("marketCapitalization", 0.0) or 0.0),
            website=data.get("weburl", ""),
            logo=data.get("logo", ""),
            description="",
            provider_source=PROVIDER_FINNHUB
        )

    def get_candles(
        self,
        symbol: str,
        resolution: str = "D",
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None
    ) -> List[NormalizedCandle]:
        """
        Fetch historical candlestick bars.
        resolution: 1, 5, 15, 30, 60, D, W, M
        """
        sym = symbol.upper().strip()
        now_ts = int(datetime.now().timestamp())
        to_ts = to_timestamp or now_ts
        from_ts = from_timestamp or (to_ts - (30 * 86400))  # Default 30 days

        cache_key = make_candle_key(PROVIDER_FINNHUB, sym, resolution)

        data = self.request(
            method="GET",
            endpoint="stock/candle",
            params={
                "symbol": sym,
                "resolution": resolution,
                "from": from_ts,
                "to": to_ts
            },
            cache_key=cache_key,
            cache_ttl=CACHE_TTL_CANDLE
        )

        if data.get("s") != "ok":
            return []

        c_list = data.get("c", [])
        h_list = data.get("h", [])
        l_list = data.get("l", [])
        o_list = data.get("o", [])
        t_list = data.get("t", [])
        v_list = data.get("v", [])

        candles: List[NormalizedCandle] = []
        for i in range(len(t_list)):
            ts_str = datetime.fromtimestamp(t_list[i]).strftime("%Y-%m-%d %H:%M:%S")
            candles.append(NormalizedCandle(
                symbol=sym,
                timeframe=resolution,
                open=float(o_list[i]),
                high=float(h_list[i]),
                low=float(l_list[i]),
                close=float(c_list[i]),
                volume=float(v_list[i]),
                timestamp=ts_str
            ))
        return candles

    def get_market_news(self, category: str = "general") -> List[NormalizedNews]:
        """Fetch real-time top financial headlines"""
        cache_key = make_news_key(PROVIDER_FINNHUB, f"market_{category}")

        data = self.request(
            method="GET",
            endpoint="news",
            params={"category": category},
            cache_key=cache_key,
            cache_ttl=CACHE_TTL_NEWS
        )

        news_items: List[NormalizedNews] = []
        if isinstance(data, list):
            for item in data[:30]:
                raw_dt = item.get("datetime")
                pub_str = datetime.fromtimestamp(raw_dt).strftime("%Y-%m-%d %H:%M:%S") if raw_dt else ""
                news_items.append(NormalizedNews(
                    title=item.get("headline", ""),
                    description=item.get("summary", ""),
                    content="",
                    url=item.get("url", ""),
                    source=item.get("source", "Finnhub"),
                    author="",
                    published_at=pub_str,
                    category=category,
                    provider_source=PROVIDER_FINNHUB
                ))
        return news_items

    def get_company_news(self, symbol: str, days_back: int = 7) -> List[NormalizedNews]:
        """Fetch news specifically mentioning the symbol"""
        sym = symbol.upper().strip()
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        cache_key = make_news_key(PROVIDER_FINNHUB, f"company_{sym}_{from_date}_{to_date}")

        data = self.request(
            method="GET",
            endpoint="company-news",
            params={
                "symbol": sym,
                "from": from_date,
                "to": to_date
            },
            cache_key=cache_key,
            cache_ttl=CACHE_TTL_NEWS
        )

        news_items: List[NormalizedNews] = []
        if isinstance(data, list):
            for item in data[:25]:
                raw_dt = item.get("datetime")
                pub_str = datetime.fromtimestamp(raw_dt).strftime("%Y-%m-%d %H:%M:%S") if raw_dt else ""
                news_items.append(NormalizedNews(
                    title=item.get("headline", ""),
                    description=item.get("summary", ""),
                    content="",
                    url=item.get("url", ""),
                    source=item.get("source", "Finnhub"),
                    author="",
                    published_at=pub_str,
                    category="company",
                    provider_source=PROVIDER_FINNHUB
                ))
        return news_items

    def search_symbols(self, query: str) -> List[NormalizedSymbol]:
        """Search tickers and company names"""
        q = query.strip()
        cache_key = make_search_key(PROVIDER_FINNHUB, q)

        data = self.request(
            method="GET",
            endpoint="search",
            params={"q": q},
            cache_key=cache_key,
            cache_ttl=CACHE_TTL_SEARCH
        )

        symbols: List[NormalizedSymbol] = []
        raw_res = data.get("result", [])
        if isinstance(raw_res, list):
            for item in raw_res[:20]:
                symbols.append(NormalizedSymbol(
                    symbol=item.get("symbol", ""),
                    name=item.get("description", ""),
                    type=item.get("type", "Stock"),
                    exchange="",
                    currency="",
                    provider_source=PROVIDER_FINNHUB
                ))
        return symbols

    def get_basic_financials(self, symbol: str) -> Dict[str, Any]:
        """Fetch basic financial metrics & ratios"""
        sym = symbol.upper().strip()
        data = self.request(
            method="GET",
            endpoint="stock/metric",
            params={"symbol": sym, "metric": "all"},
            cache_key=f"finnhub:metric:{sym}",
            cache_ttl=CACHE_TTL_COMPANY
        )
        return data.get("metric", {}) if isinstance(data, dict) else {}
