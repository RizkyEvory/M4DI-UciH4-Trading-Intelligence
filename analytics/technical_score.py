"""
M4DI~UciH4 Trading Intelligence System
Composite Institutional Technical Score Engine
Computes a normalized score [0 to 100] synthesizing Trend, Momentum, Volatility, and Volume.
"""
from typing import Dict, Any, Optional


class TechnicalScoreCalculator:
    """Calculates overall quantitative score (0-100) for ranking instruments in scanner"""

    @classmethod
    def calculate_score(
        cls,
        trend_info: Dict[str, Any],
        rsi_val: Optional[float],
        macd_hist: Optional[float],
        volatility_info: Dict[str, Any],
        volume_info: Dict[str, Any]
    ) -> float:
        """
        Synthesizes technical dimensions:
        - Baseline: 50.0 (Neutral)
        - Trend (+/- 25 pts based on short/med/long alignment & ADX)
        - Momentum (+/- 15 pts based on RSI position and MACD histogram)
        - Volume (+/- 10 pts based on RVOL and Confirmation)
        Returns score clamped to [0.0, 100.0].
        """
        score = 50.0

        # 1. Trend Factor (+/- 25 pts)
        overall_trend = trend_info.get("overall_trend", "NEUTRAL")
        trend_strength = trend_info.get("trend_strength", 50.0) / 100.0

        if "BULLISH" in overall_trend:
            mult = 1.0 if "STRONG" in overall_trend else 0.7
            score += 25.0 * mult * trend_strength
        elif "BEARISH" in overall_trend:
            mult = 1.0 if "STRONG" in overall_trend else 0.7
            score -= 25.0 * mult * trend_strength

        # 2. Momentum: RSI (+/- 10 pts)
        if rsi_val is not None:
            if 50.0 <= rsi_val <= 65.0:
                score += 8.0  # Healthy bullish momentum
            elif 35.0 <= rsi_val < 50.0:
                score -= 8.0  # Bearish momentum
            elif rsi_val > 70.0:
                score += 3.0  # Overbought (caution)
            elif rsi_val < 30.0:
                score -= 3.0  # Oversold (caution)

        # 3. Momentum: MACD Histogram (+/- 7 pts)
        if macd_hist is not None:
            if macd_hist > 0:
                score += 7.0
            elif macd_hist < 0:
                score -= 7.0

        # 4. Volume Confirmation (+/- 8 pts)
        confirmation = volume_info.get("volume_confirmation", "NORMAL")
        rvol = volume_info.get("rvol", 1.0)

        if confirmation == "BULLISH_CONFIRMATION":
            score += min(8.0, 4.0 * rvol)
        elif confirmation == "BEARISH_CONFIRMATION":
            score -= min(8.0, 4.0 * rvol)

        # Clamp strictly between 0 and 100
        clamped_score = max(0.0, min(100.0, score))
        return round(clamped_score, 1)
