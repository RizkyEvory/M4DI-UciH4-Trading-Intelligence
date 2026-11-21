"""
M4DI~UciH4 Trading Intelligence System
Twelve Data Institutional Multi-Asset API Client
Covers Quotes, Time Series Candles, Symbol Search, Market State, and Technical Indicators (RSI, EMA, MACD, etc.).
"""
from datetime import datetime
from typing import List, Dict, Any, Optional

from config.constants import (
    PROVIDER_TWELVE_DATA,
    CACHE_TTL_QUOTE,
    CACHE_TTL_CANDLE,
    CACHE_TTL_SEARCH
)
from api.base_client import BaseApiClient
from api.models import (
    NormalizedQuote,
    NormalizedCandle,
    NormalizedSymbol
)
from api.cache import (
    make_quote_key,
    make_candle_key,
    make_search_key
)
from core.logger import get_app_logger

logger = get_app_logger("TwelveDataClient")


class TwelveDataClient(BaseApiClient):
    """Twelve Data API Client with Institutional Data Normalization"""

    def __init__(
        self,
        base_url: str = "https://api.twelvedata.com",
        rate_limiter=None,
        key_rotation=None,
        health_monitor=None,
        cache=None
    ):
        super().__init__(
            provider_name=PROVIDER_TWELVE_DATA,
            base_url=base_url,
            rate_limiter=rate_limiter,
            key_rotation=key_rotation,
            health_monitor=health_monitor,
            cache=cache,
            timeout_sec=12.0
        )

    def _inject_auth(self, params: Dict[str, Any], headers: Dict[str, str], api_key: Optional[str]):
        """Twelve Data authentication passes 'apikey' in query parameters"""
        if api_key:
            params["apikey"] = api_key
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
            return isinstance(res, dict) and ("close" in res or "symbol" in res)
        except Exception as e:
            logger.warning(f"Twelve Data connection test failed: {e}")
            raise

    def get_quote(self, symbol: str) -> NormalizedQuote:
        """Retrieve multi-asset quote (FX, Metals, Crypto, Equities) and normalize"""
        sym = symbol.strip()
        cache_key = make_quote_key(PROVIDER_TWELVE_DATA, sym)

        data = self.request(
            method="GET",
            endpoint="quote",
            params={"symbol": sym},
            cache_key=cache_key,
            cache_ttl=CACHE_TTL_QUOTE
        )

        close_price = float(data.get("close", 0.0) or 0.0)
        open_price = float(data.get("open", 0.0) or 0.0)
        high_price = float(data.get("high", 0.0) or 0.0)
        low_price = float(data.get("low", 0.0) or 0.0)
        prev_close = float(data.get("previous_close", 0.0) or 0.0)
        volume = float(data.get("volume", 0.0) or 0.0)
        change = float(data.get("change", 0.0) or 0.0)
        percent_change = float(data.get("percent_change", 0.0) or 0.0)
        dt_str = str(data.get("datetime", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        return NormalizedQuote(
            symbol=data.get("symbol", sym),
            bid=close_price,
            ask=close_price,
            last=close_price,
            open=open_price,
            high=high_price,
            low=low_price,
            close=prev_close,
            volume=volume,
            change=change,
            change_percent=percent_change,
            timestamp=dt_str,
            provider_source=PROVIDER_TWELVE_DATA
        )

    def get_time_series(
        self,
        symbol: str,
        interval: str = "1day",
        outputsize: int = 30
    ) -> List[NormalizedCandle]:
        """
        Fetch OHLCV candlestick time series.
        Intervals: 1min, 5min, 15min, 30min, 1h, 4h, 1day, 1week
        """
        sym = symbol.strip()
        cache_key = make_candle_key(PROVIDER_TWELVE_DATA, sym, interval)

        data = self.request(
            method="GET",
            endpoint="time_series",
            params={
                "symbol": sym,
                "interval": interval,
                "outputsize": min(outputsize, 500)
            },
            cache_key=cache_key,
            cache_ttl=CACHE_TTL_CANDLE
        )

        values = data.get("values", [])
        candles: List[NormalizedCandle] = []

        if isinstance(values, list):
            for bar in reversed(values):  # Chronological order
                candles.append(NormalizedCandle(
                    symbol=sym,
                    timeframe=interval,
                    open=float(bar.get("open", 0.0) or 0.0),
                    high=float(bar.get("high", 0.0) or 0.0),
                    low=float(bar.get("low", 0.0) or 0.0),
                    close=float(bar.get("close", 0.0) or 0.0),
                    volume=float(bar.get("volume", 0.0) or 0.0),
                    timestamp=str(bar.get("datetime", ""))
                ))
        return candles

    def search_symbols(self, query: str) -> List[NormalizedSymbol]:
        """Search instruments across global exchanges"""
        q = query.strip()
        cache_key = make_search_key(PROVIDER_TWELVE_DATA, q)

        data = self.request(
            method="GET",
            endpoint="symbol_search",
            params={"symbol": q},
            cache_key=cache_key,
            cache_ttl=CACHE_TTL_SEARCH
        )

        symbols: List[NormalizedSymbol] = []
        raw_list = data.get("data", [])
        if isinstance(raw_list, list):
            for item in raw_list[:25]:
                symbols.append(NormalizedSymbol(
                    symbol=item.get("symbol", ""),
                    name=item.get("instrument_name", ""),
                    type=item.get("type", ""),
                    exchange=item.get("exchange", ""),
                    currency=item.get("currency", ""),
                    country=item.get("country", ""),
                    provider_source=PROVIDER_TWELVE_DATA
                ))
        return symbols

    def get_market_state(self, exchange: str = "NYSE") -> Dict[str, Any]:
        """Fetch current open/closed status for an exchange or market"""
        data = self.request(
            method="GET",
            endpoint="market_state",
            params={"exchange": exchange},
            cache_key=f"twelvedata:market_state:{exchange}",
            cache_ttl=300
        )
        if isinstance(data, list) and data:
            return data[0]
        return data if isinstance(data, dict) else {}

    def get_technical_indicator(
        self,
        symbol: str,
        indicator: str = "rsi",
        interval: str = "1day",
        time_period: int = 14,
        **extra_params
    ) -> Dict[str, Any]:
        """
        Fetch calculated technical indicators directly from Twelve Data API.
        Indicators: rsi, ema, sma, macd, bbands, atr, etc.
        """
        sym = symbol.strip()
        ind = indicator.lower().strip()
        params = {
            "symbol": sym,
            "interval": interval,
            "time_period": time_period,
            **extra_params
        }
        cache_key = f"twelvedata:{ind}:{sym}:{interval}:{time_period}"

        data = self.request(
            method="GET",
            endpoint=ind,
            params=params,
            cache_key=cache_key,
            cache_ttl=CACHE_TTL_CANDLE
        )
        return data if isinstance(data, dict) else {}
