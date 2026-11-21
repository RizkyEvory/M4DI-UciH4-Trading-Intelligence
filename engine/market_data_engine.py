"""
M4DI~UciH4 Trading Intelligence System
Central Market Data Manager
Coordinates quotes, multi-timeframe candles, validation, resampling, and symbol surveillance.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional

from config.constants import (
    PROVIDER_FINNHUB,
    PROVIDER_TWELVE_DATA,
    TF_1M, TF_5M, TF_15M, TF_30M, TF_1H, TF_4H, TF_1D, TF_1W, TF_1MO,
    CACHE_TTL_QUOTE, CACHE_TTL_CANDLE
)
from api.models import (
    NormalizedQuote,
    NormalizedCandle,
    NormalizedSymbol
)
from engine.data_validator import DataValidator
from engine.resampler import Resampler
from core.logger import get_app_logger

logger = get_app_logger("MarketDataEngine")


class MarketDataManager:
    """Central Orchestrator for Market Feeds, Resampling, and Multi-Asset Timeframes"""

    def __init__(self, app_context):
        self.ctx = app_context

    def get_quote(self, symbol: str, provider_preference: Optional[str] = None) -> NormalizedQuote:
        """
        Retrieve validated, normalized market quote for symbol.
        Automatically routes between Twelve Data and Finnhub.
        """
        sym = symbol.strip().upper()
        # Default routing logic: Forex / Metals / Indices -> Twelve Data; US Equities -> Finnhub
        if provider_preference:
            prov = provider_preference
        elif "/" in sym or "XAU" in sym or "XAG" in sym or "BTC" in sym:
            prov = PROVIDER_TWELVE_DATA
        else:
            prov = PROVIDER_FINNHUB

        if prov == PROVIDER_TWELVE_DATA:
            client = self.ctx.twelve_data
        else:
            client = self.ctx.finnhub

        quote = client.get_quote(sym)
        return quote

    def get_candles(
        self,
        symbol: str,
        timeframe: str = TF_1D,
        count: int = 100,
        provider_preference: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> List[NormalizedCandle]:
        """
        Retrieve validated historical candlestick series for symbol and timeframe.
        Applies mathematical resampling if provider does not natively support timeframe.
        Supports both 'count' and 'limit' parameter aliases.
        """
        if limit is not None:
            count = limit
        sym = symbol.strip().upper()
        tf = timeframe.lower()

        # Route provider
        if provider_preference:
            prov = provider_preference
        elif "/" in sym or "XAU" in sym or "XAG" in sym:
            prov = PROVIDER_TWELVE_DATA
        else:
            prov = PROVIDER_FINNHUB

        raw_candles: List[NormalizedCandle] = []

        if prov == PROVIDER_TWELVE_DATA:
            # Map canonical timeframe to Twelve Data interval format
            td_intervals = {
                "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
                "1h": "1h", "4h": "4h", "1d": "1day", "1w": "1week", "1m_mo": "1month"
            }
            td_interval = td_intervals.get(tf, "1day")
            try:
                raw_candles = self.ctx.twelve_data.get_time_series(sym, interval=td_interval, outputsize=count)
            except Exception as e:
                logger.warning(f"Twelve Data fetch candles failed for {sym}: {e}, falling back to Finnhub if equity")
                if prov != PROVIDER_FINNHUB and "/" not in sym:
                    raw_candles = self.ctx.finnhub.get_candles(sym, resolution="D")

        else:
            # Finnhub resolution format: 1, 5, 15, 30, 60, D, W, M
            fh_res_map = {
                "1m": "1", "5m": "5", "15m": "15", "30m": "30",
                "1h": "60", "4h": "60",  # Finnhub lacks 4h; fetch 1h and resample!
                "1d": "D", "1w": "W", "1m_mo": "M"
            }
            fh_res = fh_res_map.get(tf, "D")
            raw_candles = self.ctx.finnhub.get_candles(sym, resolution=fh_res)

            # If 4h was requested and we got 1h candles from Finnhub, mathematically resample to 4h
            if tf == "4h" and raw_candles:
                raw_candles = Resampler.resample(raw_candles, target_timeframe=TF_4H, source_timeframe=TF_1H)

        # Validate, deduplicate, and sort chronologically
        cleaned_candles = DataValidator.clean_and_sort_candles(raw_candles, expected_timeframe=tf)
        return cleaned_candles[-count:] if len(cleaned_candles) > count else cleaned_candles

    def get_intraday_candles(self, symbol: str, interval: str = TF_15M, count: int = 100) -> List[NormalizedCandle]:
        """Convenience method for intraday timeframes (1m, 5m, 15m, 30m, 1h, 4h)"""
        return self.get_candles(symbol, timeframe=interval, count=count)

    def get_daily_candles(self, symbol: str, count: int = 100) -> List[NormalizedCandle]:
        """Convenience method for daily candles (1D)"""
        return self.get_candles(symbol, timeframe=TF_1D, count=count)

    def get_weekly_candles(self, symbol: str, count: int = 52) -> List[NormalizedCandle]:
        """Convenience method for weekly candles (1W)"""
        return self.get_candles(symbol, timeframe=TF_1W, count=count)

    def get_monthly_candles(self, symbol: str, count: int = 24) -> List[NormalizedCandle]:
        """Convenience method for monthly candles (1M)"""
        return self.get_candles(symbol, timeframe=TF_1MO, count=count)

    def search_symbols(self, query: str, provider: Optional[str] = None) -> List[NormalizedSymbol]:
        """Search symbol lookup across multi-asset database"""
        prov = provider or PROVIDER_FINNHUB
        if prov == PROVIDER_TWELVE_DATA:
            return self.ctx.twelve_data.search_symbols(query)
        return self.ctx.finnhub.search_symbols(query)

    def get_watchlist_symbols(
        self,
        watchlist_name: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Retrieve symbols from SQLite watchlist database"""
        if watchlist_name:
            sql = """
            SELECT ws.symbol, ws.market, w.name
            FROM watchlist_symbols ws
            JOIN watchlists w ON ws.watchlist_id = w.id
            WHERE w.name = ?
            ORDER BY ws.id ASC
            """
            rows = self.ctx.db.fetchall(sql, (watchlist_name,))
        else:
            sql = """
            SELECT ws.symbol, ws.market, w.name
            FROM watchlist_symbols ws
            JOIN watchlists w ON ws.watchlist_id = w.id
            ORDER BY w.id ASC, ws.id ASC
            """
            rows = self.ctx.db.fetchall(sql)

        return [{"symbol": r[0], "market": r[1], "watchlist": r[2]} for r in rows]

    def get_multi_timeframe_series(
        self,
        symbol: str,
        timeframes: Optional[List[str]] = None
    ) -> Dict[str, List[NormalizedCandle]]:
        """
        Fetch candle series across multiple timeframes for Multi-Timeframe Confluence.
        Default: 5m, 15m, 1h, 4h, 1d.
        """
        tfs = timeframes or [TF_5M, TF_15M, TF_1H, TF_4H, TF_1D]
        result: Dict[str, List[NormalizedCandle]] = {}
        for tf in tfs:
            try:
                candles = self.get_candles(symbol, timeframe=tf, count=60)
                if candles:
                    result[tf] = candles
            except Exception as e:
                logger.warning(f"Could not load {tf} for {symbol}: {e}")
        return result
