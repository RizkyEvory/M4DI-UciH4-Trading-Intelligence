"""
M4DI~UciH4 Trading Intelligence System
Signal Confidence Engine
Calculates institutional probability confidence metric (0-100%) based on:
1. Multi-Indicator Concordance (Indicator Agreement)
2. Multi-Timeframe Alignment (Confluence across 5m, 1h, 4h, 1d)
3. News Confirmation (Fundamental & Sentiment alignment with technicals)
4. Data Integrity (Bar sample size, continuity, and absence of anomalies)
"""
from typing import Dict, Any, List, Optional
from signals.models import SignalConfidence


class SignalConfidenceEngine:
    """Calculates statistical confidence of algorithmic trading setups"""

    @classmethod
    def calculate_confidence(
        cls,
        technical_score: float,
        sub_metrics: Dict[str, Any],
        mtf_confluence_score: float = 0.0,
        news_sentiment_score: float = 0.0,
        candle_count: int = 50,
        has_critical_news: bool = False
    ) -> SignalConfidence:
        """
        Computes composite confidence percentage.
        Confidence is NOT a guarantee of profit, but a quantitative measure of alignment.
        """
        # 1. Indicator Agreement (Concordance across EMA, RSI, MACD, Volume)
        bullish_votes = 0
        bearish_votes = 0
        total_indicators = 4

        # EMA
        ema_20 = sub_metrics.get("ema_20")
        ema_50 = sub_metrics.get("ema_50")
        if ema_20 is not None and ema_50 is not None:
            if ema_20 > ema_50:
                bullish_votes += 1
            else:
                bearish_votes += 1

        # RSI
        rsi = sub_metrics.get("rsi", 50.0)
        if rsi < 35.0:
            bullish_votes += 1  # Oversold rebound
        elif 50.0 <= rsi <= 68.0:
            bullish_votes += 1  # Trend continuation
        elif rsi > 70.0:
            bearish_votes += 1  # Overbought pullback
        elif 35.0 <= rsi < 50.0:
            bearish_votes += 1

        # MACD
        macd_val = sub_metrics.get("macd")
        macd_sig = sub_metrics.get("macd_signal")
        if macd_val is not None and macd_sig is not None:
            if macd_val > macd_sig:
                bullish_votes += 1
            else:
                bearish_votes += 1

        # Volume confirmation
        rvol = sub_metrics.get("rvol", 1.0)
        if rvol >= 1.2:
            # Volume confirms whichever side has dominance
            if technical_score >= 0:
                bullish_votes += 1
            else:
                bearish_votes += 1
        else:
            total_indicators -= 1

        dominant_votes = max(bullish_votes, bearish_votes)
        agreement_ratio = (dominant_votes / max(1, total_indicators))
        indicator_agreement_pct = round(agreement_ratio * 100.0, 1)

        # 2. Multi-Timeframe Confirmation (-100 to +100 mapped to 0-100%)
        # If technical is positive and MTF is positive, high alignment; if opposing, low
        if technical_score > 10.0:
            # Bullish signal
            mtf_alignment_pct = max(0.0, min(100.0, 50.0 + (mtf_confluence_score * 0.5)))
        elif technical_score < -10.0:
            # Bearish signal
            mtf_alignment_pct = max(0.0, min(100.0, 50.0 - (mtf_confluence_score * 0.5)))
        else:
            mtf_alignment_pct = 50.0

        # 3. News & Sentiment Confirmation
        # Check if news sentiment agrees with technical direction
        if abs(technical_score) < 15.0 or abs(news_sentiment_score) < 0.1:
            news_confirmation_pct = 60.0  # Neutral baseline
        elif (technical_score > 0 and news_sentiment_score > 0) or (technical_score < 0 and news_sentiment_score < 0):
            # Synergistic confirmation
            news_confirmation_pct = min(100.0, 75.0 + (abs(news_sentiment_score) * 25.0))
        else:
            # Divergence (e.g. Technical BUY but News Bearish)
            news_confirmation_pct = max(15.0, 50.0 - (abs(news_sentiment_score) * 35.0))

        # 4. Data Quality (Based on sample depth)
        if candle_count >= 100:
            data_quality_pct = 100.0
        elif candle_count >= 50:
            data_quality_pct = 90.0
        elif candle_count >= 20:
            data_quality_pct = 75.0
        else:
            data_quality_pct = 50.0

        # 5. Composite Overall Confidence
        # Weights: Indicator Agreement (40%), MTF Alignment (30%), News Confirmation (15%), Data Quality (15%)
        overall = (
            (indicator_agreement_pct * 0.40) +
            (mtf_alignment_pct * 0.30) +
            (news_confirmation_pct * 0.15) +
            (data_quality_pct * 0.15)
        )

        overall = max(10.0, min(99.0, round(overall, 1)))

        return SignalConfidence(
            overall=overall,
            indicator_agreement=round(indicator_agreement_pct, 1),
            mtf_alignment=round(mtf_alignment_pct, 1),
            news_confirmation=round(news_confirmation_pct, 1),
            data_quality=round(data_quality_pct, 1)
        )
