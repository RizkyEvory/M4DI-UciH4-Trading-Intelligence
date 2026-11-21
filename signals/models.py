"""
M4DI~UciH4 Trading Intelligence System
Trading Signal Models & Dataclasses
Defines quantitative signal structures, score breakdowns, confidence metrics, and alert triggers.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime

from config.constants import (
    SIGNAL_STRONG_BUY,
    SIGNAL_BUY,
    SIGNAL_NEUTRAL,
    SIGNAL_SELL,
    SIGNAL_STRONG_SELL
)


@dataclass
class SignalConfidence:
    """Detailed confidence metric components (0.0 to 100.0%)"""
    overall: float = 50.0
    indicator_agreement: float = 50.0
    mtf_alignment: float = 50.0
    news_confirmation: float = 50.0
    data_quality: float = 100.0

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class SignalScoreBreakdown:
    """Transparent score components enabling institutional auditing"""
    technical_score: float = 0.0      # -100 to +100
    fundamental_score: float = 0.0    # -100 to +100
    risk_score: float = 0.0           # 0 to 100
    composite_score: float = 0.0      # -100 to +100
    weights: Dict[str, float] = field(default_factory=lambda: {
        "technical": 0.50,
        "fundamental": 0.25,
        "risk": 0.25
    })
    sub_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TradingSignal:
    """Full-featured actionable algorithmic trading signal"""
    symbol: str
    signal: str = SIGNAL_NEUTRAL
    confidence: float = 0.0           # 0.0 to 100.0 %
    score: float = 0.0                # -100.0 to +100.0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    risk_reward: float = 0.0
    timeframe: str = "1d"
    reasons: List[str] = field(default_factory=list)
    score_breakdown: Optional[SignalScoreBreakdown] = None
    confidence_breakdown: Optional[SignalConfidence] = None
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @property
    def risk_reward_ratio(self) -> float:
        return self.risk_reward

    @property
    def confidence_pct(self) -> float:
        return self.confidence

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.score_breakdown:
            data["score_breakdown"] = self.score_breakdown.to_dict()
        if self.confidence_breakdown:
            data["confidence_breakdown"] = self.confidence_breakdown.to_dict()
        return data


@dataclass
class SignalAlert:
    """Real-time signal alert triggered by significant technical or news events"""
    alert_id: str
    alert_type: str                   # Strong Buy, RSI Extreme, etc.
    symbol: str
    message: str
    severity: str = "INFO"            # INFO, WARNING, CRITICAL
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
