"""
M4DI~UciH4 Trading Intelligence System
EMA Crossover Strategy (Phase 5)
Fast EMA crosses Slow EMA with Trend Filter and dynamic ATR-based Stop Loss.
"""
from typing import Dict, Any, List, Optional, Tuple
from api.models import NormalizedCandle
from analytics.indicators import calculate_ema, calculate_atr
from backtesting.strategies.base_strategy import BaseStrategy


class EMACrossoverStrategy(BaseStrategy):
    """Moving Average Trend Following Strategy"""

    DEFAULT_PARAMS = {
        "fast_period": 9,
        "slow_period": 21,
        "trend_period": 50,
        "atr_period": 14,
        "atr_multiplier": 1.5,
        "risk_reward": 2.0
    }

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        combined_params = dict(self.DEFAULT_PARAMS)
        if params:
            combined_params.update(params)
        super().__init__("EMA Crossover", combined_params)

    def evaluate(
        self,
        historical_candles: List[NormalizedCandle],
        current_index: int
    ) -> Tuple[Optional[str], Optional[float], Optional[float]]:
        fast_p = int(self.get_param("fast_period", 9))
        slow_p = int(self.get_param("slow_period", 21))
        trend_p = int(self.get_param("trend_period", 50))
        atr_p = int(self.get_param("atr_period", 14))
        atr_mult = float(self.get_param("atr_multiplier", 1.5))
        rr = float(self.get_param("risk_reward", 2.0))

        min_required = max(slow_p, trend_p) + 2
        if len(historical_candles) < min_required:
            return None, None, None

        closes = [c.close for c in historical_candles]
        highs = [c.high for c in historical_candles]
        lows = [c.low for c in historical_candles]

        fast_ema = calculate_ema(closes, fast_p)
        slow_ema = calculate_ema(closes, slow_p)
        trend_ema = calculate_ema(closes, trend_p)
        atr_series = calculate_atr(highs, lows, closes, atr_p)

        if fast_ema[-1] is None or slow_ema[-1] is None or fast_ema[-2] is None or slow_ema[-2] is None:
            return None, None, None

        curr_close = closes[-1]
        atr_val = atr_series[-1] if atr_series and atr_series[-1] is not None else (curr_close * 0.015)

        # Bullish Crossover: Fast crossed above Slow on previous or current bar
        if fast_ema[-2] <= slow_ema[-2] and fast_ema[-1] > slow_ema[-1]:
            # Trend filter: Close above Trend EMA if available
            t_val = trend_ema[-1]
            if t_val is None or curr_close >= t_val:
                sl = round(curr_close - (atr_val * atr_mult), 4)
                tp = round(curr_close + ((curr_close - sl) * rr), 4)
                return "BUY", sl, tp

        # Bearish Crossover: Fast crossed below Slow
        elif fast_ema[-2] >= slow_ema[-2] and fast_ema[-1] < slow_ema[-1]:
            t_val = trend_ema[-1]
            if t_val is None or curr_close <= t_val:
                sl = round(curr_close + (atr_val * atr_mult), 4)
                tp = round(curr_close - ((sl - curr_close) * rr), 4)
                return "SELL", sl, tp

        return None, None, None
