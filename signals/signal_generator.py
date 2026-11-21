"""
M4DI~UciH4 Trading Intelligence System
Core Signal Generator
Orchestrates Market Data, Technical Indicators, Multi-Timeframe Confluence,
News Intelligence, Scoring Engine, and Confidence Engine to produce institutional trading signals
complete with Stop Loss, Take Profit 1 & 2, and Risk/Reward parameters.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from config.constants import (
    SIGNAL_STRONG_BUY,
    SIGNAL_BUY,
    SIGNAL_NEUTRAL,
    SIGNAL_SELL,
    SIGNAL_STRONG_SELL
)
from api.models import NormalizedCandle
from analytics.indicators import TechnicalIndicators
from analytics.mtf import MultiTimeframeAnalyzer
from signals.models import TradingSignal
from signals.scoring_engine import SignalScoringEngine
from signals.confidence_engine import SignalConfidenceEngine
from core.logger import get_app_logger

logger = get_app_logger("SignalGenerator")


class SignalGenerator:
    """End-to-end institutional signal synthesizer"""

    def __init__(self, scoring_engine: Optional[SignalScoringEngine] = None):
        self.scoring_engine = scoring_engine or SignalScoringEngine()
        self._active_signals: List[TradingSignal] = []

    def get_active_signals(self, limit: int = 10) -> List[TradingSignal]:
        """Retrieve most recently generated active trading signals"""
        return list(self._active_signals[:limit])

    def generate_signal(
        self,
        symbol: str,
        candles: List[NormalizedCandle],
        timeframe: str = "1d",
        mtf_data: Optional[Dict[str, List[NormalizedCandle]]] = None,
        news_profile: Optional[Dict[str, Any]] = None
    ) -> TradingSignal:
        """
        Synthesize all analytic components into a structured TradingSignal.
        """
        sym = symbol.upper().strip()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not candles or len(candles) < 14:
            return TradingSignal(
                symbol=sym,
                signal=SIGNAL_NEUTRAL,
                confidence=0.0,
                score=0.0,
                entry_price=0.0,
                stop_loss=0.0,
                take_profit_1=0.0,
                take_profit_2=0.0,
                risk_reward=0.0,
                timeframe=timeframe,
                reasons=["Insufficient historical data to calculate algorithmic signal (minimum 14 bars required)"],
                timestamp=now_str
            )

        current_candle = candles[-1]
        entry_price = round(current_candle.close, 4)

        # 1. Multi-Timeframe Confluence
        mtf_score = 0.0
        if mtf_data:
            mtf_res = MultiTimeframeAnalyzer.analyze_confluence(mtf_data)
            mtf_score = mtf_res.get("confluence_score", 0.0)

        # 2. Multi-Factor Scoring
        breakdown, reasons = self.scoring_engine.calculate_score(candles, news_profile)
        composite_score = breakdown.composite_score
        sub_metrics = breakdown.sub_metrics

        # 3. Confidence Calculation
        news_sent = news_profile.get("sentiment_score", 0.0) if news_profile else 0.0
        has_critical = news_profile.get("has_critical_news", False) if news_profile else False

        confidence_obj = SignalConfidenceEngine.calculate_confidence(
            technical_score=breakdown.technical_score,
            sub_metrics=sub_metrics,
            mtf_confluence_score=mtf_score,
            news_sentiment_score=news_sent,
            candle_count=len(candles),
            has_critical_news=has_critical
        )
        conf_val = confidence_obj.overall

        # 4. Signal Type Determination
        if composite_score >= 50.0 and conf_val >= 60.0:
            signal_type = SIGNAL_STRONG_BUY
        elif composite_score >= 20.0 and conf_val >= 40.0:
            signal_type = SIGNAL_BUY
        elif composite_score <= -50.0 and conf_val >= 60.0:
            signal_type = SIGNAL_STRONG_SELL
        elif composite_score <= -20.0 and conf_val >= 40.0:
            signal_type = SIGNAL_SELL
        else:
            signal_type = SIGNAL_NEUTRAL

        # 5. Dynamic Stop Loss, Take Profit, and Risk/Reward Math
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        closes = [c.close for c in candles]
        atr_series = TechnicalIndicators.atr(highs, lows, closes, 14)
        atr_val = atr_series[-1] if atr_series and atr_series[-1] > 0 else (entry_price * 0.015)

        # Structural swing boundaries
        recent_low = min(lows[-10:])
        recent_high = max(highs[-10:])

        if signal_type in (SIGNAL_BUY, SIGNAL_STRONG_BUY):
            # SL placed below swing low or 1.5 ATR
            sl_dist = max(entry_price - recent_low, 1.5 * atr_val)
            stop_loss = round(max(0.0001, entry_price - sl_dist), 4)
            risk = entry_price - stop_loss
            tp1 = round(entry_price + (1.5 * risk), 4)
            tp2 = round(entry_price + (2.5 * risk), 4)
            rr_ratio = round((tp1 - entry_price) / max(0.0001, risk), 2)
            reasons.append(f"Setup Target: TP1 at {tp1:.2f} (1.5R), TP2 at {tp2:.2f} (2.5R), SL at {stop_loss:.2f}")

        elif signal_type in (SIGNAL_SELL, SIGNAL_STRONG_SELL):
            # SL placed above swing high or 1.5 ATR
            sl_dist = max(recent_high - entry_price, 1.5 * atr_val)
            stop_loss = round(entry_price + sl_dist, 4)
            risk = stop_loss - entry_price
            tp1 = round(max(0.0001, entry_price - (1.5 * risk)), 4)
            tp2 = round(max(0.0001, entry_price - (2.5 * risk)), 4)
            rr_ratio = round((entry_price - tp1) / max(0.0001, risk), 2)
            reasons.append(f"Setup Target: TP1 at {tp1:.2f} (1.5R), TP2 at {tp2:.2f} (2.5R), SL at {stop_loss:.2f}")

        else:
            # Neutral: no active trade setup
            stop_loss = round(entry_price - (1.5 * atr_val), 4)
            tp1 = round(entry_price + (1.5 * atr_val), 4)
            tp2 = round(entry_price + (2.5 * atr_val), 4)
            rr_ratio = 1.0
            reasons.append("Market is in balance or consolidation. No high-edge directional setup identified.")

        sig = TradingSignal(
            symbol=sym,
            signal=signal_type,
            confidence=conf_val,
            score=composite_score,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            risk_reward=rr_ratio,
            timeframe=timeframe,
            reasons=reasons,
            score_breakdown=breakdown,
            confidence_breakdown=confidence_obj,
            timestamp=now_str
        )
        self._active_signals.insert(0, sig)
        if len(self._active_signals) > 100:
            self._active_signals.pop()
        return sig
