"""
M4DI~UciH4 Trading Intelligence System
Volatility Analysis & Classification Engine
Evaluates ATR, Historical Volatility, and Bollinger Bandwidth to classify regime: Low, Normal, High, Extreme.
"""
import math
from typing import List, Dict, Any, Optional

from config.constants import (
    VOLATILITY_LOW,
    VOLATILITY_NORMAL,
    VOLATILITY_HIGH,
    VOLATILITY_EXTREME
)
from analytics.indicators import calculate_atr, calculate_bollinger_bands


class VolatilityAnalyzer:
    """Quantitative Volatility Regime Classifier"""

    @staticmethod
    def calculate_historical_volatility(closes: List[float], period: int = 20, annual_days: int = 252) -> float:
        """Annualized historical volatility computed from log returns (%)"""
        n = len(closes)
        if n <= period or period < 2:
            return 0.0

        # Calculate log returns for the last `period` bars
        returns = []
        start_idx = n - period
        for i in range(start_idx, n):
            prev = closes[i - 1]
            curr = closes[i]
            if prev > 0 and curr > 0:
                returns.append(math.log(curr / prev))

        if len(returns) < 2:
            return 0.0

        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
        daily_std = math.sqrt(variance)
        annualized = daily_std * math.sqrt(annual_days) * 100.0
        return round(annualized, 2)

    @classmethod
    def analyze(
        cls,
        highs: List[float],
        lows: List[float],
        closes: List[float]
    ) -> Dict[str, Any]:
        """
        Calculates ATR, ATR%, Historical Volatility, and Bollinger Bandwidth,
        then classifies into LOW, NORMAL, HIGH, or EXTREME.
        """
        n = len(closes)
        if n < 14:
            return {
                "regime": VOLATILITY_NORMAL,
                "atr": 0.0,
                "atr_percent": 0.0,
                "historical_volatility": 0.0,
                "bollinger_bandwidth": 0.0
            }

        curr_price = closes[-1]

        # 1. ATR and ATR%
        atr_series = calculate_atr(highs, lows, closes, 14)
        latest_atr = atr_series[-1] or (highs[-1] - lows[-1])
        atr_pct = (latest_atr / curr_price * 100.0) if curr_price > 0 else 0.0

        # 2. Bollinger Bandwidth
        upper, middle, lower, bandwidth = calculate_bollinger_bands(closes, 20, 2.0)
        latest_bbw = bandwidth[-1] if bandwidth[-1] is not None else 3.0

        # 3. Annualized Historical Volatility
        hv = cls.calculate_historical_volatility(closes, period=min(20, n - 1))

        # 4. Volatility Classification
        # Scoring: ATR% and BB Width thresholds
        if atr_pct >= 3.5 or latest_bbw >= 12.0 or hv >= 50.0:
            regime = VOLATILITY_EXTREME
        elif atr_pct >= 1.5 or latest_bbw >= 6.0 or hv >= 25.0:
            regime = VOLATILITY_HIGH
        elif atr_pct <= 0.4 or latest_bbw <= 1.8:
            regime = VOLATILITY_LOW
        else:
            regime = VOLATILITY_NORMAL

        return {
            "regime": regime,
            "atr": round(latest_atr, 4),
            "atr_percent": round(atr_pct, 2),
            "historical_volatility": hv,
            "bollinger_bandwidth": round(latest_bbw, 2),
            "bb_upper": round(upper[-1], 4) if upper[-1] is not None else curr_price,
            "bb_middle": round(middle[-1], 4) if middle[-1] is not None else curr_price,
            "bb_lower": round(lower[-1], 4) if lower[-1] is not None else curr_price
        }
