"""
M4DI~UciH4 Trading Intelligence System
RSI Mean Reversion Strategy (Phase 5)
Capitalizes on extreme overbought and oversold boundary bounces.
"""
from typing import Dict, Any, List, Optional, Tuple
from api.models import NormalizedCandle
from analytics.indicators import calculate_rsi, calculate_atr
from backtesting.strategies.base_strategy import BaseStrategy


class RSIMeanReversionStrategy(BaseStrategy):
    """Oversold and Overbought Boundary Mean Reversion"""

    DEFAULT_PARAMS = {
        "period": 14,
        "oversold": 30.0,
        "overbought": 70.0,
        "atr_multiplier": 1.5,
        "risk_reward": 1.8
    }

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        combined_params = dict(self.DEFAULT_PARAMS)
        if params:
            combined_params.update(params)
        super().__init__("RSI Mean Reversion", combined_params)

    def evaluate(
        self,
        historical_candles: List[NormalizedCandle],
        current_index: int
    ) -> Tuple[Optional[str], Optional[float], Optional[float]]:
        p = int(self.get_param("period", 14))
        os_level = float(self.get_param("oversold", 30.0))
        ob_level = float(self.get_param("overbought", 70.0))
        atr_mult = float(self.get_param("atr_multiplier", 1.5))
        rr = float(self.get_param("risk_reward", 1.8))

        if len(historical_candles) < p + 5:
            return None, None, None

        closes = [c.close for c in historical_candles]
        highs = [c.high for c in historical_candles]
        lows = [c.low for c in historical_candles]

        rsi_series = calculate_rsi(closes, p)
        if not rsi_series or len(rsi_series) < 2 or rsi_series[-1] is None or rsi_series[-2] is None:
            return None, None, None

        curr_rsi = rsi_series[-1]
        prev_rsi = rsi_series[-2]
        curr_close = closes[-1]

        atr_series = calculate_atr(highs, lows, closes, 14)
        atr_val = atr_series[-1] if atr_series and atr_series[-1] is not None else (curr_close * 0.015)

        # Rebound from Oversold: Previous RSI <= 30 and Current RSI > 30
        if prev_rsi <= os_level and curr_rsi > os_level:
            sl = round(curr_close - (atr_val * atr_mult), 4)
            tp = round(curr_close + ((curr_close - sl) * rr), 4)
            return "BUY", sl, tp

        # Pullback from Overbought: Previous RSI >= 70 and Current RSI < 70
        elif prev_rsi >= ob_level and curr_rsi < ob_level:
            sl = round(curr_close + (atr_val * atr_mult), 4)
            tp = round(curr_close - ((sl - curr_close) * rr), 4)
            return "SELL", sl, tp

        return None, None, None
