"""
M4DI~UciH4 Trading Intelligence System
Bollinger Breakout Strategy (Phase 5)
Detects volatility expansion breakouts following bandwidth compression.
"""
from typing import Dict, Any, List, Optional, Tuple
from api.models import NormalizedCandle
from analytics.indicators import calculate_bollinger_bands, calculate_atr
from backtesting.strategies.base_strategy import BaseStrategy


class BollingerBreakoutStrategy(BaseStrategy):
    """Volatility Bandwidth Squeeze & Directional Breakout"""

    DEFAULT_PARAMS = {
        "period": 20,
        "num_std": 2.0,
        "atr_multiplier": 1.5,
        "risk_reward": 2.0
    }

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        combined_params = dict(self.DEFAULT_PARAMS)
        if params:
            combined_params.update(params)
        super().__init__("Bollinger Breakout", combined_params)

    def evaluate(
        self,
        historical_candles: List[NormalizedCandle],
        current_index: int
    ) -> Tuple[Optional[str], Optional[float], Optional[float]]:
        p = int(self.get_param("period", 20))
        std = float(self.get_param("num_std", 2.0))
        atr_mult = float(self.get_param("atr_multiplier", 1.5))
        rr = float(self.get_param("risk_reward", 2.0))

        if len(historical_candles) < p + 5:
            return None, None, None

        closes = [c.close for c in historical_candles]
        highs = [c.high for c in historical_candles]
        lows = [c.low for c in historical_candles]

        upper, middle, lower, bandwidth = calculate_bollinger_bands(closes, p, std)
        if not upper or len(upper) < 2 or upper[-1] is None or lower[-1] is None:
            return None, None, None

        curr_close = closes[-1]
        prev_close = closes[-2]
        up_val = upper[-1]
        low_val = lower[-1]

        atr_series = calculate_atr(highs, lows, closes, 14)
        atr_val = atr_series[-1] if atr_series and atr_series[-1] is not None else (curr_close * 0.015)

        # Bullish Breakout: Price crosses above Upper Band
        if prev_close <= upper[-2] and curr_close > up_val:
            sl = round(middle[-1] if middle[-1] is not None else curr_close - (atr_val * atr_mult), 4)
            tp = round(curr_close + ((curr_close - sl) * rr), 4)
            return "BUY", sl, tp

        # Bearish Breakdown: Price crosses below Lower Band
        elif prev_close >= lower[-2] and curr_close < low_val:
            sl = round(middle[-1] if middle[-1] is not None else curr_close + (atr_val * atr_mult), 4)
            tp = round(curr_close - ((sl - curr_close) * rr), 4)
            return "SELL", sl, tp

        return None, None, None
