"""
M4DI~UciH4 Trading Intelligence System
Trend Analysis & Market Structure Engine
Combines Multi-EMA alignment, Higher Highs/Lows structure, and ADX strength.
"""
from typing import List, Dict, Any, Optional

from config.constants import (
    TREND_STRONG_BULLISH,
    TREND_BULLISH,
    TREND_NEUTRAL,
    TREND_BEARISH,
    TREND_STRONG_BEARISH
)
from analytics.indicators import calculate_ema, calculate_sma, calculate_adx


class TrendAnalyzer:
    """Institutional Market Structure & Trend Confluence Analyzer"""

    @staticmethod
    def detect_market_structure(highs: List[float], lows: List[float], window: int = 3) -> Dict[str, Any]:
        """
        Detects Swing Highs and Swing Lows to identify structural Higher Highs (HH),
        Higher Lows (HL), Lower Highs (LH), and Lower Lows (LL).
        """
        n = len(highs)
        if n < window * 2 + 1:
            return {
                "structure_bias": TREND_NEUTRAL,
                "recent_hh": False,
                "recent_hl": False,
                "recent_lh": False,
                "recent_ll": False,
                "swing_highs": [],
                "swing_lows": []
            }

        swing_highs = []
        swing_lows = []

        for i in range(window, n - window):
            # Check swing high
            if all(highs[i] >= highs[j] for j in range(i - window, i + window + 1) if j != i):
                swing_highs.append((i, highs[i]))

            # Check swing low
            if all(lows[i] <= lows[j] for j in range(i - window, i + window + 1) if j != i):
                swing_lows.append((i, lows[i]))

        recent_hh = False
        recent_lh = False
        recent_hl = False
        recent_ll = False

        if len(swing_highs) >= 2:
            last_sh = swing_highs[-1][1]
            prev_sh = swing_highs[-2][1]
            if last_sh > prev_sh:
                recent_hh = True
            elif last_sh < prev_sh:
                recent_lh = True

        if len(swing_lows) >= 2:
            last_sl = swing_lows[-1][1]
            prev_sl = swing_lows[-2][1]
            if last_sl > prev_sl:
                recent_hl = True
            elif last_sl < prev_sl:
                recent_ll = True

        # Determine structural bias
        if recent_hh and recent_hl:
            bias = TREND_BULLISH
        elif recent_lh and recent_ll:
            bias = TREND_BEARISH
        else:
            bias = TREND_NEUTRAL

        return {
            "structure_bias": bias,
            "recent_hh": recent_hh,
            "recent_hl": recent_hl,
            "recent_lh": recent_lh,
            "recent_ll": recent_ll,
            "swing_highs": swing_highs[-5:],
            "swing_lows": swing_lows[-5:]
        }

    @classmethod
    def analyze(
        cls,
        highs: List[float],
        lows: List[float],
        closes: List[float]
    ) -> Dict[str, Any]:
        """
        Complete Multi-Term Trend Evaluation.
        Short-Term (EMA 9 vs EMA 21)
        Medium-Term (EMA 21 vs EMA 50)
        Long-Term (EMA 50 vs SMA 200 & Price vs SMA 200)
        """
        n = len(closes)
        if n < 10:
            return {
                "overall_trend": TREND_NEUTRAL,
                "short_term": TREND_NEUTRAL,
                "medium_term": TREND_NEUTRAL,
                "long_term": TREND_NEUTRAL,
                "trend_strength": 0.0,
                "adx": 0.0,
                "structure": cls.detect_market_structure(highs, lows)
            }

        ema9 = calculate_ema(closes, min(9, n))
        ema21 = calculate_ema(closes, min(21, n))
        ema50 = calculate_ema(closes, min(50, n))
        sma200 = calculate_sma(closes, min(200, n))

        adx_line, plus_di, minus_di = calculate_adx(highs, lows, closes, 14)
        latest_adx = adx_line[-1] if adx_line[-1] is not None else 20.0

        current_price = closes[-1]
        e9 = ema9[-1] or current_price
        e21 = ema21[-1] or current_price
        e50 = ema50[-1] or current_price
        s200 = sma200[-1] or current_price

        # 1. Short-Term Trend
        threshold = 0.001 * current_price
        if e9 - e21 > threshold:
            short_trend = TREND_BULLISH
        elif e21 - e9 > threshold:
            short_trend = TREND_BEARISH
        else:
            short_trend = TREND_NEUTRAL

        # 2. Medium-Term Trend
        if e21 - e50 > threshold:
            med_trend = TREND_BULLISH
        elif e50 - e21 > threshold:
            med_trend = TREND_BEARISH
        else:
            med_trend = TREND_NEUTRAL

        # 3. Long-Term Trend
        if current_price > s200 and e50 >= s200:
            long_trend = TREND_BULLISH
        elif current_price < s200 and e50 <= s200:
            long_trend = TREND_BEARISH
        else:
            long_trend = TREND_NEUTRAL

        # 4. Market Structure Confluence
        structure = cls.detect_market_structure(highs, lows)
        struct_bias = structure["structure_bias"]

        # Composite Trend Classification
        bull_score = sum([
            short_trend == TREND_BULLISH,
            med_trend == TREND_BULLISH,
            long_trend == TREND_BULLISH,
            struct_bias == TREND_BULLISH
        ])
        bear_score = sum([
            short_trend == TREND_BEARISH,
            med_trend == TREND_BEARISH,
            long_trend == TREND_BEARISH,
            struct_bias == TREND_BEARISH
        ])

        if bull_score >= 3 or (short_trend == TREND_BULLISH and med_trend == TREND_BULLISH and bear_score == 0):
            overall = TREND_STRONG_BULLISH if latest_adx >= 25 else TREND_BULLISH
        elif bear_score >= 3 or (short_trend == TREND_BEARISH and med_trend == TREND_BEARISH and bull_score == 0):
            overall = TREND_STRONG_BEARISH if latest_adx >= 25 else TREND_BEARISH
        else:
            overall = TREND_NEUTRAL

        # Trend Strength Score (0 to 100)
        adx_factor = min(1.0, latest_adx / 50.0)
        alignment_factor = max(bull_score, bear_score) / 4.0
        trend_strength = round((adx_factor * 0.5 + alignment_factor * 0.5) * 100.0, 1)

        return {
            "overall_trend": overall,
            "short_term": short_trend,
            "medium_term": med_trend,
            "long_term": long_trend,
            "trend_strength": trend_strength,
            "adx": round(latest_adx, 2),
            "ema9": round(e9, 4),
            "ema21": round(e21, 4),
            "ema50": round(e50, 4),
            "sma200": round(s200, 4),
            "structure": structure
        }
