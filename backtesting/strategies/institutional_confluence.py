"""
M4DI~UciH4 Trading Intelligence System
Institutional Confluence Strategy (Phase 5)
Multi-factor quantitative strategy combining Moving Average Alignment,
Momentum RSI confirmation, and Relative Volume (RVOL) Breakouts.
"""
from typing import Dict, Any, List, Optional, Tuple
from api.models import NormalizedCandle
from analytics.indicators import calculate_ema, calculate_rsi, calculate_atr
from analytics.volume import VolumeAnalyzer
from backtesting.strategies.base_strategy import BaseStrategy


class InstitutionalConfluenceStrategy(BaseStrategy):
    """Institutional Multi-Indicator Confluence Strategy"""

    DEFAULT_PARAMS = {
        "fast_ema": 20,
        "slow_ema": 50,
        "rsi_period": 14,
        "rsi_min": 48.0,
        "rsi_max": 68.0,
        "rvol_threshold": 1.2,
        "atr_multiplier": 1.5,
        "risk_reward": 2.2
    }

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        combined_params = dict(self.DEFAULT_PARAMS)
        if params:
            combined_params.update(params)
        super().__init__("Institutional Confluence", combined_params)

    def evaluate(
        self,
        historical_candles: List[NormalizedCandle],
        current_index: int
    ) -> Tuple[Optional[str], Optional[float], Optional[float]]:
        f_p = int(self.get_param("fast_ema", 20))
        s_p = int(self.get_param("slow_ema", 50))
        rsi_p = int(self.get_param("rsi_period", 14))
        rsi_min = float(self.get_param("rsi_min", 48.0))
        rsi_max = float(self.get_param("rsi_max", 68.0))
        rvol_thresh = float(self.get_param("rvol_threshold", 1.2))
        atr_mult = float(self.get_param("atr_multiplier", 1.5))
        rr = float(self.get_param("risk_reward", 2.2))

        if len(historical_candles) < s_p + 5:
            return None, None, None

        closes = [c.close for c in historical_candles]
        highs = [c.high for c in historical_candles]
        lows = [c.low for c in historical_candles]
        volumes = [c.volume for c in historical_candles]

        fast_ema = calculate_ema(closes, f_p)
        slow_ema = calculate_ema(closes, s_p)
        rsi_series = calculate_rsi(closes, rsi_p)
        atr_series = calculate_atr(highs, lows, closes, 14)
        vol_res = VolumeAnalyzer.analyze(closes, volumes)

        if fast_ema[-1] is None or slow_ema[-1] is None or rsi_series[-1] is None:
            return None, None, None

        curr_close = closes[-1]
        e_fast = fast_ema[-1]
        e_slow = slow_ema[-1]
        rsi_val = rsi_series[-1]
        rvol = vol_res.get("rvol", 1.0)
        atr_val = atr_series[-1] if atr_series and atr_series[-1] is not None else (curr_close * 0.015)

        # Bullish Institutional Confluence:
        # 1. Price > EMA 20 > EMA 50
        # 2. RSI between 48 and 68 (momentum expansion without overbought exhaustion)
        # 3. RVOL >= 1.2 (institutional participation)
        if curr_close > e_fast > e_slow and rsi_min <= rsi_val <= rsi_max and rvol >= rvol_thresh:
            sl = round(e_slow - (atr_val * 0.5), 4)
            if sl >= curr_close:
                sl = round(curr_close - (atr_val * atr_mult), 4)
            tp = round(curr_close + ((curr_close - sl) * rr), 4)
            return "BUY", sl, tp

        # Bearish Institutional Confluence:
        # 1. Price < EMA 20 < EMA 50
        # 2. RSI between (100 - rsi_max) and (100 - rsi_min)
        # 3. RVOL >= 1.2
        elif curr_close < e_fast < e_slow and (100.0 - rsi_max) <= rsi_val <= (100.0 - rsi_min) and rvol >= rvol_thresh:
            sl = round(e_slow + (atr_val * 0.5), 4)
            if sl <= curr_close:
                sl = round(curr_close + (atr_val * atr_mult), 4)
            tp = round(curr_close - ((sl - curr_close) * rr), 4)
            return "SELL", sl, tp

        return None, None, None
