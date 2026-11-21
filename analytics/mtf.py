"""
M4DI~UciH4 Trading Intelligence System
Multi-Timeframe (MTF) Confluence Engine
Analyzes trend alignment across 5m, 15m, 1h, 4h, 1d, and 1w timeframes.
"""
from typing import Dict, List, Any, Optional

from api.models import NormalizedCandle
from config.constants import (
    TREND_STRONG_BULLISH,
    TREND_BULLISH,
    TREND_NEUTRAL,
    TREND_BEARISH,
    TREND_STRONG_BEARISH
)
from analytics.trend import TrendAnalyzer


class MultiTimeframeAnalyzer:
    """Analyzes directional confluence across multiple timeframe dimensions"""

    # Weights by timeframe importance (Higher Timeframes dominate market regime)
    TIMEFRAME_WEIGHTS = {
        "1w": 2.5,
        "1d": 2.5,
        "4h": 2.0,
        "1h": 1.5,
        "15m": 1.0,
        "5m": 0.5
    }

    @classmethod
    def analyze_confluence(
        cls,
        tf_candles_map: Dict[str, List[NormalizedCandle]]
    ) -> Dict[str, Any]:
        """
        Analyzes dictionary of {timeframe: candles} across 5m, 15m, 1h, 4h, 1d, 1w.
        Determines if timeframes are in harmonious confluence or conflicting.
        """
        trends_by_tf: Dict[str, str] = {}
        strengths_by_tf: Dict[str, float] = {}

        weighted_score = 0.0
        total_weight = 0.0

        for tf, candles in tf_candles_map.items():
            if not candles or len(candles) < 5:
                continue

            highs = [c.high for c in candles]
            lows = [c.low for c in candles]
            closes = [c.close for c in candles]

            trend_info = TrendAnalyzer.analyze(highs, lows, closes)
            direction = trend_info["overall_trend"]
            trends_by_tf[tf] = direction
            strengths_by_tf[tf] = trend_info["trend_strength"]

            weight = cls.TIMEFRAME_WEIGHTS.get(tf.lower(), 1.0)
            total_weight += weight

            if "BULLISH" in direction:
                mult = 1.0 if direction == TREND_STRONG_BULLISH else 0.7
                weighted_score += mult * weight
            elif "BEARISH" in direction:
                mult = -1.0 if direction == TREND_STRONG_BEARISH else -0.7
                weighted_score += mult * weight

        confluence_index = round((weighted_score / total_weight * 100.0), 1) if total_weight > 0 else 0.0

        # Classify Alignment State
        htf_tfs = [tf for tf in ("1w", "1d", "4h") if tf in trends_by_tf]
        ltf_tfs = [tf for tf in ("1h", "15m", "5m") if tf in trends_by_tf]

        htf_bulls = sum(1 for tf in htf_tfs if "BULLISH" in trends_by_tf[tf])
        htf_bears = sum(1 for tf in htf_tfs if "BEARISH" in trends_by_tf[tf])
        ltf_bulls = sum(1 for tf in ltf_tfs if "BULLISH" in trends_by_tf[tf])
        ltf_bears = sum(1 for tf in ltf_tfs if "BEARISH" in trends_by_tf[tf])

        if confluence_index >= 75.0:
            status = "STRONG_BULLISH_CONFLUENCE"
            summary_msg = "All major timeframes are in full bullish alignment."
        elif confluence_index <= -75.0:
            status = "STRONG_BEARISH_CONFLUENCE"
            summary_msg = "All major timeframes are in full bearish alignment."
        elif htf_bulls > htf_bears and ltf_bears > ltf_bulls:
            status = "PULLBACK_AGAINST_HTF_BULLISH"
            summary_msg = "HTF is Bullish; LTF is experiencing a counter-trend retracement."
        elif htf_bears > htf_bulls and ltf_bulls > ltf_bears:
            status = "PULLBACK_AGAINST_HTF_BEARISH"
            summary_msg = "HTF is Bearish; LTF is experiencing a counter-trend relief rally."
        elif abs(confluence_index) < 25.0:
            status = "MIXED_CONFLICTING"
            summary_msg = "Timeframes are conflicting; choppy consolidation regime."
        else:
            status = "MODERATE_CONFLUENCE"
            direction_str = "Bullish" if confluence_index > 0 else "Bearish"
            summary_msg = f"Moderate {direction_str} confluence across timeframes."

        return {
            "alignment_status": status,
            "confluence_score": confluence_index,
            "summary": summary_msg,
            "timeframe_trends": trends_by_tf,
            "timeframe_strengths": strengths_by_tf
        }
