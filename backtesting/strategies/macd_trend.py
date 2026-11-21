"""
M4DI~UciH4 Trading Intelligence System
MACD Trend Following Strategy (Phase 5)
Capitalizes on MACD line and signal crossovers with histogram expansion.
"""
from typing import Dict, Any, List, Optional, Tuple
from api.models import NormalizedCandle
from analytics.indicators import calculate_macd, calculate_atr
from backtesting.strategies.base_strategy import BaseStrategy


class MACDTrendFollowingStrategy(BaseStrategy):
    """MACD Line Crossover & Momentum Expansion"""

    DEFAULT_PARAMS = {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9,
        "atr_multiplier": 1.5,
        "risk_reward": 2.0
    }

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        combined_params = dict(self.DEFAULT_PARAMS)
        if params:
            combined_params.update(params)
        super().__init__("MACD Trend Following", combined_params)

    def evaluate(
        self,
        historical_candles: List[NormalizedCandle],
        current_index: int
    ) -> Tuple[Optional[str], Optional[float], Optional[float]]:
        fast_p = int(self.get_param("fast_period", 12))
        slow_p = int(self.get_param("slow_period", 26))
        sig_p = int(self.get_param("signal_period", 9))
        atr_mult = float(self.get_param("atr_multiplier", 1.5))
        rr = float(self.get_param("risk_reward", 2.0))

        if len(historical_candles) < slow_p + sig_p + 2:
            return None, None, None

        closes = [c.close for c in historical_candles]
        highs = [c.high for c in historical_candles]
        lows = [c.low for c in historical_candles]

        macd_line, sig_line, hist = calculate_macd(closes, fast_p, slow_p, sig_p)
        if not macd_line or len(macd_line) < 2 or macd_line[-1] is None or sig_line[-1] is None:
            return None, None, None

        if macd_line[-2] is None or sig_line[-2] is None:
            return None, None, None

        curr_close = closes[-1]
        atr_series = calculate_atr(highs, lows, closes, 14)
        atr_val = atr_series[-1] if atr_series and atr_series[-1] is not None else (curr_close * 0.015)

        # Bullish Crossover with positive histogram
        if macd_line[-2] <= sig_line[-2] and macd_line[-1] > sig_line[-1]:
            sl = round(curr_close - (atr_val * atr_mult), 4)
            tp = round(curr_close + ((curr_close - sl) * rr), 4)
            return "BUY", sl, tp

        # Bearish Crossover with negative histogram
        elif macd_line[-2] >= sig_line[-2] and macd_line[-1] < sig_line[-1]:
            sl = round(curr_close + (atr_val * atr_mult), 4)
            tp = round(curr_close - ((sl - curr_close) * rr), 4)
            return "SELL", sl, tp

        return None, None, None
