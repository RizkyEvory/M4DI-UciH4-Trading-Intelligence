"""
M4DI~UciH4 Trading Intelligence System
Signal Scoring Engine
Provides transparent multi-factor quantitative scoring across Technical, Fundamental/News, and Risk dimensions.
Fully auditable with detailed reason generation for every signal factor.
"""
from typing import List, Dict, Any, Tuple, Optional

from config.constants import (
    VOLATILITY_NORMAL,
    VOLATILITY_HIGH,
    VOLATILITY_LOW,
    VOLATILITY_EXTREME,
    SENTIMENT_POSITIVE,
    SENTIMENT_NEGATIVE
)
from api.models import NormalizedCandle
from analytics.indicators import TechnicalIndicators
from analytics.trend import TrendAnalyzer
from analytics.volatility import VolatilityAnalyzer
from analytics.volume import VolumeAnalyzer
from signals.models import SignalScoreBreakdown


class SignalScoringEngine:
    """Configurable, transparent multi-factor scoring engine"""

    DEFAULT_WEIGHTS = {
        "technical": 0.50,
        "fundamental": 0.25,
        "risk": 0.25
    }

    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        self.weights = dict(self.DEFAULT_WEIGHTS)
        if custom_weights:
            self.weights.update(custom_weights)
            # Normalize to sum to 1.0
            total_w = sum(self.weights.values())
            if total_w > 0:
                for k in self.weights:
                    self.weights[k] = round(self.weights[k] / total_w, 3)

    def calculate_score(
        self,
        candles: List[NormalizedCandle],
        news_profile: Optional[Dict[str, Any]] = None
    ) -> Tuple[SignalScoreBreakdown, List[str]]:
        """
        Calculates composite score (-100 to +100) and compiles transparent reason explanations.
        """
        reasons: List[str] = []
        sub_metrics: Dict[str, Any] = {}

        if not candles or len(candles) < 14:
            breakdown = SignalScoreBreakdown(
                technical_score=0.0,
                fundamental_score=0.0,
                risk_score=50.0,
                composite_score=0.0,
                weights=self.weights,
                sub_metrics={"error": "Insufficient candle history (<14 bars)"}
            )
            return breakdown, ["Insufficient historical bars for algorithmic evaluation"]

        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        volumes = [c.volume for c in candles]
        current_price = closes[-1]

        # =========================================================================
        # 1. TECHNICAL SCORING DIMENSION (-100 to +100)
        # =========================================================================
        tech_pts = 0.0

        # A. Trend & Moving Averages (Max 35 pts)
        ema_20 = TechnicalIndicators.ema(closes, min(20, len(closes)))
        ema_50 = TechnicalIndicators.ema(closes, min(50, len(closes)))
        trend_res = TrendAnalyzer.analyze(highs, lows, closes)

        if ema_20 and ema_50 and ema_20[-1] is not None and ema_50[-1] is not None:
            e20_val = ema_20[-1]
            e50_val = ema_50[-1]
            sub_metrics["ema_20"] = round(e20_val, 2)
            sub_metrics["ema_50"] = round(e50_val, 2)

            ma_diff_pct = abs(e20_val - e50_val) / max(0.001, current_price)

            if ma_diff_pct >= 0.002:
                if current_price > e20_val > e50_val:
                    tech_pts += 20.0
                    reasons.append(f"Bullish Moving Average Stack: Price ({current_price:.2f}) > EMA20 ({e20_val:.2f}) > EMA50 ({e50_val:.2f})")
                elif current_price < e20_val < e50_val:
                    tech_pts -= 20.0
                    reasons.append(f"Bearish Moving Average Stack: Price ({current_price:.2f}) < EMA20 ({e20_val:.2f}) < EMA50 ({e50_val:.2f})")
            else:
                reasons.append("Moving Averages are compressed/flat in sideways consolidation")

        # Trend & Market Structure
        overall_trend = trend_res.get("overall_trend", "NEUTRAL")
        if overall_trend in ("STRONG_BULLISH", "BULLISH"):
            tech_pts += 15.0
            reasons.append(f"Institutional Trend ({overall_trend}): Bullish directional bias confirmed")
        elif overall_trend in ("STRONG_BEARISH", "BEARISH"):
            tech_pts -= 15.0
            reasons.append(f"Institutional Trend ({overall_trend}): Bearish directional bias confirmed")

        # B. Momentum: RSI & MACD (Max 35 pts)
        rsi_series = TechnicalIndicators.rsi(closes, 14)
        rsi_val = rsi_series[-1] if rsi_series and rsi_series[-1] is not None else 50.0
        sub_metrics["rsi"] = round(rsi_val, 1)

        if rsi_val <= 30.0:
            tech_pts += 20.0
            reasons.append(f"RSI Oversold ({rsi_val:.1f}): High probability mean-reversion discount area")
        elif 55.0 <= rsi_val <= 75.0:
            tech_pts += 15.0
            reasons.append(f"RSI Bullish Expansion ({rsi_val:.1f}): Sustainable momentum without exhaustion")
        elif rsi_val > 75.0:
            if current_price > (ema_20[-1] if ema_20 and ema_20[-1] is not None else 0):
                tech_pts += 10.0
                reasons.append(f"RSI High Momentum ({rsi_val:.1f}): Bullish power trend")
            else:
                tech_pts -= 15.0
                reasons.append(f"RSI Overbought ({rsi_val:.1f}): Premium exhaustion zone")
        elif 25.0 <= rsi_val <= 45.0:
            tech_pts -= 15.0
            reasons.append(f"RSI Bearish Pressure ({rsi_val:.1f}): Sub-45 downward momentum")
        elif rsi_val < 25.0:
            if current_price < (ema_20[-1] if ema_20 and ema_20[-1] is not None else 999999):
                tech_pts -= 10.0
                reasons.append(f"RSI Strong Bearish Momentum ({rsi_val:.1f})")
            else:
                tech_pts += 15.0
                reasons.append(f"RSI Deep Discount ({rsi_val:.1f})")
        else:
            reasons.append(f"RSI Neutral Equilibrium ({rsi_val:.1f})")

        # MACD
        macd_line, signal_line, histogram = TechnicalIndicators.macd(closes)

        if macd_line and signal_line and histogram and macd_line[-1] is not None and signal_line[-1] is not None:
            m_val = macd_line[-1]
            s_val = signal_line[-1]
            h_val = histogram[-1] if histogram[-1] is not None else 0.0
            sub_metrics["macd"] = round(m_val, 3)
            sub_metrics["macd_signal"] = round(s_val, 3)
            sub_metrics["macd_hist"] = round(h_val, 3)

            if abs(m_val) < 0.05 and abs(s_val) < 0.05:
                reasons.append(f"MACD Neutral: Hovering near zero line ({m_val:.2f})")
            elif m_val > s_val and h_val > 0:
                tech_pts += 15.0
                reasons.append(f"MACD Bullish Crossover: MACD ({m_val:.2f}) above Signal ({s_val:.2f}) with positive expansion")
            elif m_val < s_val and h_val < 0:
                tech_pts -= 15.0
                reasons.append(f"MACD Bearish Crossover: MACD ({m_val:.2f}) below Signal ({s_val:.2f}) with negative expansion")

        # C. Volume & RVOL (Max 20 pts)
        vol_res = VolumeAnalyzer.analyze(closes, volumes)
        rvol = vol_res.get("rvol", 1.0)
        sub_metrics["rvol"] = round(rvol, 2)
        price_change = closes[-1] - closes[-2] if len(closes) > 1 else 0.0

        if rvol >= 1.5:
            if price_change > 0:
                tech_pts += 15.0
                reasons.append(f"Volume Breakout (RVOL {rvol:.2f}x): Institutional accumulation on bullish candle")
            else:
                tech_pts -= 15.0
                reasons.append(f"Volume Outflow (RVOL {rvol:.2f}x): Heavy institutional distribution on bearish candle")
        elif rvol >= 1.1:
            if price_change > 0:
                tech_pts += 5.0
            else:
                tech_pts -= 5.0

        # D. ADX Trend Strength (Max 10 pts)
        adx_line, plus_di, minus_di = TechnicalIndicators.adx(highs, lows, closes, 14)
        adx_val = adx_line[-1] if adx_line and adx_line[-1] is not None else 20.0
        sub_metrics["adx"] = round(adx_val, 1)

        if adx_val >= 25.0:
            multiplier = 1.15
            reasons.append(f"ADX Trend Strength ({adx_val:.1f}): Robust directional momentum confirmed")
            tech_pts *= multiplier

        # Normalize technical score to -100 to +100
        technical_score = max(-100.0, min(100.0, round(tech_pts, 1)))

        # =========================================================================
        # 2. FUNDAMENTAL / NEWS SENTIMENT DIMENSION (-100 to +100)
        # =========================================================================
        fundamental_score = 0.0
        if news_profile and news_profile.get("article_count", 0) > 0:
            sent_score = news_profile.get("sentiment_score", 0.0)  # -1.0 to +1.0
            sub_metrics["news_sentiment_score"] = sent_score
            sub_metrics["news_article_count"] = news_profile.get("article_count", 0)

            # Scale to -100 to +100
            fundamental_score = round(sent_score * 100.0, 1)

            if news_profile.get("sentiment") == SENTIMENT_POSITIVE:
                reasons.append(f"Positive News Sentiment (+{sent_score:.2f}) from {news_profile['article_count']} recent headlines")
            elif news_profile.get("sentiment") == SENTIMENT_NEGATIVE:
                reasons.append(f"Negative News Sentiment ({sent_score:.2f}) from {news_profile['article_count']} recent headlines")

            if news_profile.get("has_critical_news"):
                reasons.append("High/Critical Market Catalyst detected in recent news wire")
        else:
            reasons.append("No active news catalyst found for symbol (Neutral fundamental baseline)")

        # =========================================================================
        # 3. RISK & VOLATILITY DIMENSION (0 to 100 pts)
        # =========================================================================
        vol_profile = VolatilityAnalyzer.analyze(highs, lows, closes)
        regime = vol_profile.get("regime", VOLATILITY_NORMAL)
        atr_pct = vol_profile.get("atr_pct", 1.5)
        sub_metrics["volatility_regime"] = regime
        sub_metrics["atr_pct"] = round(atr_pct, 2)

        risk_score = 50.0  # Base neutral
        if regime == VOLATILITY_NORMAL:
            risk_score = 90.0
            reasons.append(f"Volatility Regime: NORMAL (ATR {atr_pct:.2f}%). Optimal environment for trend continuation")
        elif regime == VOLATILITY_HIGH:
            risk_score = 75.0
            reasons.append(f"Volatility Regime: HIGH (ATR {atr_pct:.2f}%). Wide targets with adjusted stop distances")
        elif regime == VOLATILITY_LOW:
            risk_score = 55.0
            reasons.append(f"Volatility Regime: LOW (ATR {atr_pct:.2f}%). Compression phase; wait for liquidity expansion")
        elif regime == VOLATILITY_EXTREME:
            risk_score = 35.0
            reasons.append(f"Volatility Regime: EXTREME (ATR {atr_pct:.2f}%). Elevated whipsaw risk; reduce position size")

        # =========================================================================
        # 4. COMPOSITE SCORING CALCULATION
        # =========================================================================
        w_tech = self.weights["technical"]
        w_fund = self.weights["fundamental"]
        w_risk = self.weights["risk"]

        # Risk adjustment factor: if risk_score is high (>70), it reinforces directional score; if low (<50), dampens
        risk_modifier = (risk_score - 50.0) / 50.0  # -0.3 to +1.0

        raw_composite = (technical_score * w_tech) + (fundamental_score * w_fund)
        # Apply risk factor
        if raw_composite > 0:
            final_composite = raw_composite * (1.0 + (risk_modifier * w_risk))
        else:
            final_composite = raw_composite * (1.0 - (risk_modifier * w_risk * 0.5))

        composite_score = max(-100.0, min(100.0, round(final_composite, 1)))

        breakdown = SignalScoreBreakdown(
            technical_score=technical_score,
            fundamental_score=fundamental_score,
            risk_score=risk_score,
            composite_score=composite_score,
            weights=self.weights,
            sub_metrics=sub_metrics
        )

        return breakdown, reasons
