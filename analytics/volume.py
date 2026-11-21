"""
M4DI~UciH4 Trading Intelligence System
Volume Dynamics & Relative Volume (RVOL) Engine
Analyzes institutional volume surges, breakouts, confirmation, and OBV flow.
"""
from typing import List, Dict, Any, Optional

from analytics.indicators import calculate_obv, calculate_sma


class VolumeAnalyzer:
    """Quantitative Volume & Institutional Participation Analyzer"""

    @classmethod
    def analyze(
        cls,
        closes: List[float],
        volumes: List[float],
        avg_period: int = 20
    ) -> Dict[str, Any]:
        """
        Calculates RVOL, Volume Trend, Breakouts, Price-Volume Confirmation, and OBV Direction.
        """
        n = len(volumes)
        if n == 0:
            return {
                "rvol": 1.0,
                "current_volume": 0.0,
                "avg_volume": 0.0,
                "volume_trend": "NORMAL",
                "volume_breakout": False,
                "volume_confirmation": "NEUTRAL",
                "obv_trend": "NEUTRAL"
            }

        curr_vol = volumes[-1]
        prior_vols = volumes[-(avg_period + 1):-1] if n > 1 else [curr_vol]
        avg_vol = sum(prior_vols) / len(prior_vols) if prior_vols else curr_vol
        rvol = round(curr_vol / avg_vol, 2) if avg_vol > 0 else 1.0

        # Volume Trend (Last 3 bars vs previous 3 bars)
        if n >= 6:
            recent_3_avg = sum(volumes[-3:]) / 3.0
            prev_3_avg = sum(volumes[-6:-3]) / 3.0
            if recent_3_avg > prev_3_avg * 1.2:
                vol_trend = "INCREASING"
            elif recent_3_avg < prev_3_avg * 0.8:
                vol_trend = "DECREASING"
            else:
                vol_trend = "STEADY"
        else:
            vol_trend = "STEADY"

        # Volume Breakout (> 2.0x average volume)
        volume_breakout = (rvol >= 2.0)

        # Price-Volume Confirmation
        if n >= 2:
            price_change = closes[-1] - closes[-2]
            if price_change > 0 and rvol >= 1.2:
                confirmation = "BULLISH_CONFIRMATION"  # Healthy accumulation on volume
            elif price_change < 0 and rvol >= 1.2:
                confirmation = "BEARISH_CONFIRMATION"  # Heavy distribution / selling pressure
            elif abs(price_change) > 0 and rvol < 0.7:
                confirmation = "LOW_VOLUME_DIVERGENCE" # Movement without institutional volume
            else:
                confirmation = "NORMAL"
        else:
            confirmation = "NORMAL"

        # OBV Trend (20-period slope or SMA check)
        obv = calculate_obv(closes, volumes)
        if len(obv) >= 10:
            obv_sma = calculate_sma(obv, period=min(10, len(obv)))
            latest_obv_sma = obv_sma[-1]
            if latest_obv_sma is not None and obv[-1] > latest_obv_sma:
                obv_trend = "ACCUMULATION"
            elif latest_obv_sma is not None and obv[-1] < latest_obv_sma:
                obv_trend = "DISTRIBUTION"
            else:
                obv_trend = "NEUTRAL"
        else:
            obv_trend = "NEUTRAL"

        return {
            "current_volume": curr_vol,
            "avg_volume": round(avg_vol, 2),
            "rvol": rvol,
            "volume_trend": vol_trend,
            "volume_breakout": volume_breakout,
            "volume_confirmation": confirmation,
            "obv_trend": obv_trend,
            "latest_obv": obv[-1] if obv else 0.0
        }
