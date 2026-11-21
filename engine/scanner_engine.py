"""
M4DI~UciH4 Trading Intelligence System
Market Scanner Engine
Scans watchlists & asset classes, computes technical indicators, and applies multi-parameter filters.
"""
from typing import List, Dict, Any, Optional

from config.constants import TF_1D
from api.models import NormalizedCandle
from analytics.indicators import calculate_rsi, calculate_macd, calculate_atr, calculate_ema, calculate_sma
from analytics.trend import TrendAnalyzer
from analytics.volatility import VolatilityAnalyzer
from analytics.volume import VolumeAnalyzer
from analytics.technical_score import TechnicalScoreCalculator
from core.logger import get_app_logger

logger = get_app_logger("ScannerEngine")


class MarketScannerEngine:
    """Quantitative Screener & Scanner Engine across Multi-Asset Instruments"""

    def __init__(self, market_data_manager):
        self.mdm = market_data_manager

    def scan_symbol(self, symbol: str, timeframe: str = TF_1D) -> Optional[Dict[str, Any]]:
        """
        Scan a single instrument, compute its complete technical indicators & score.
        """
        try:
            candles = self.mdm.get_candles(symbol, timeframe=timeframe, count=60)
            if not candles or len(candles) < 15:
                # Need at least 15 bars for basic indicators
                return None

            highs = [c.high for c in candles]
            lows = [c.low for c in candles]
            closes = [c.close for c in candles]
            volumes = [c.volume for c in candles]

            curr_price = closes[-1]
            prev_close = closes[-2] if len(closes) >= 2 else curr_price
            change_val = curr_price - prev_close
            change_pct = round((change_val / prev_close * 100.0), 2) if prev_close > 0 else 0.0

            # Technical Indicators
            rsi_series = calculate_rsi(closes, 14)
            latest_rsi = round(rsi_series[-1], 1) if rsi_series[-1] is not None else 50.0

            macd_l, sig_l, hist_l = calculate_macd(closes, 12, 26, 9)
            latest_macd_hist = round(hist_l[-1], 4) if hist_l[-1] is not None else 0.0
            macd_status = "BULLISH" if latest_macd_hist > 0 else ("BEARISH" if latest_macd_hist < 0 else "NEUTRAL")

            atr_series = calculate_atr(highs, lows, closes, 14)
            latest_atr = round(atr_series[-1], 4) if atr_series[-1] is not None else 0.0

            ema21_series = calculate_ema(closes, 21)
            ema50_series = calculate_ema(closes, 50)
            latest_ema21 = round(ema21_series[-1], 2) if ema21_series[-1] is not None else curr_price
            latest_ema50 = round(ema50_series[-1], 2) if ema50_series[-1] is not None else curr_price

            # Multi-Dimensional Analytics
            trend_info = TrendAnalyzer.analyze(highs, lows, closes)
            vol_regime_info = VolatilityAnalyzer.analyze(highs, lows, closes)
            volume_info = VolumeAnalyzer.analyze(closes, volumes)

            # Institutional Technical Score
            tech_score = TechnicalScoreCalculator.calculate_score(
                trend_info=trend_info,
                rsi_val=latest_rsi,
                macd_hist=latest_macd_hist,
                volatility_info=vol_regime_info,
                volume_info=volume_info
            )

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "price": curr_price,
                "change": round(change_val, 4),
                "change_percent": change_pct,
                "volume": volumes[-1],
                "rvol": volume_info["rvol"],
                "rsi": latest_rsi,
                "macd_status": macd_status,
                "macd_hist": latest_macd_hist,
                "atr": latest_atr,
                "ema21": latest_ema21,
                "ema50": latest_ema50,
                "trend": trend_info["overall_trend"],
                "trend_strength": trend_info["trend_strength"],
                "adx": trend_info["adx"],
                "volatility": vol_regime_info["regime"],
                "volatility_pct": vol_regime_info["atr_percent"],
                "technical_score": tech_score,
                "timestamp": candles[-1].timestamp
            }

        except Exception as e:
            logger.warning(f"Scan failed for symbol {symbol}: {e}")
            return None

    def scan_symbols(
        self,
        symbols: List[str],
        filters: Optional[Dict[str, Any]] = None,
        timeframe: str = TF_1D
    ) -> List[Dict[str, Any]]:
        """
        Scan a batch of symbols and filter results according to quantitative criteria.
        """
        f = filters or {}
        min_p = f.get("min_price")
        max_p = f.get("max_price")
        min_v = f.get("min_volume")
        trend_req = f.get("trend")
        vol_req = f.get("volatility")
        rsi_min = f.get("rsi_min")
        rsi_max = f.get("rsi_max")
        search_query = f.get("search", "").strip().upper()

        results: List[Dict[str, Any]] = []

        for sym in symbols:
            clean_sym = sym.strip().upper()
            if search_query and search_query not in clean_sym:
                continue

            record = self.scan_symbol(clean_sym, timeframe=timeframe)
            if not record:
                continue

            # Apply filters
            if min_p is not None and record["price"] < min_p:
                continue
            if max_p is not None and record["price"] > max_p:
                continue
            if min_v is not None and record["volume"] < min_v:
                continue
            if trend_req and trend_req != "ALL" and trend_req not in record["trend"]:
                continue
            if vol_req and vol_req != "ALL" and record["volatility"] != vol_req:
                continue
            if rsi_min is not None and record["rsi"] < rsi_min:
                continue
            if rsi_max is not None and record["rsi"] > rsi_max:
                continue

            results.append(record)

        # Sort by technical score descending by default
        results.sort(key=lambda r: -r["technical_score"])
        return results
