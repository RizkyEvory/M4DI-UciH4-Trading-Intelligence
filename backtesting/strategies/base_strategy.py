"""
M4DI~UciH4 Trading Intelligence System
Abstract Base Strategy Framework (Phase 5)
Enforces modularity, parameter configurability, and strict anti-lookahead guarantees.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from api.models import NormalizedCandle


class BaseStrategy(ABC):
    """Abstract Strategy Interface guaranteeing zero data leakage"""

    def __init__(self, name: str, params: Optional[Dict[str, Any]] = None):
        self.name = name
        self.params: Dict[str, Any] = params or {}

    def get_param(self, key: str, default: Any = None) -> Any:
        return self.params.get(key, default)

    def set_param(self, key: str, value: Any):
        self.params[key] = value

    @abstractmethod
    def evaluate(
        self,
        historical_candles: List[NormalizedCandle],
        current_index: int
    ) -> Tuple[Optional[str], Optional[float], Optional[float]]:
        """
        Evaluate entry/exit condition at current bar index.
        CRITICAL: historical_candles MUST ONLY contain bars [0 : current_index + 1].

        Returns:
            (signal, stop_loss, take_profit)
            signal: "BUY", "SELL", or None
        """
        pass
