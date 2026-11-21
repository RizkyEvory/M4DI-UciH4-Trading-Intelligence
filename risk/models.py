"""
M4DI~UciH4 Trading Intelligence System
Risk Management Models & Dataclasses (Phase 5)
Defines structures for Position Sizing, Risk/Reward analytics, and Risk Limit Checks.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional


@dataclass
class PositionSizeResult:
    """Detailed position size calculation output with transparent auditing steps"""
    units: float                          # Units / Shares / Contracts to trade
    cash_risk: float                      # Monetary amount risked ($)
    total_cost: float                     # Total position value ($)
    entry_price: float
    stop_loss: float
    take_profit: Optional[float] = None
    stop_loss_distance: float = 0.0       # Price difference ($ per unit)
    potential_loss: float = 0.0           # Total loss if SL hit ($)
    potential_profit: float = 0.0         # Total profit if TP hit ($)
    risk_reward_ratio: float = 0.0        # Potential profit / Potential loss
    calculation_steps: List[str] = field(default_factory=list)

    @property
    def position_units(self) -> float:
        return self.units

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RiskCheckResult:
    """Validation response indicating whether an order adheres to risk rules"""
    allowed: bool
    reason: str
    rule_violated: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AccountRiskProfile:
    """Current live risk parameters and exposure metrics of the trading account"""
    account_id: str
    balance: float
    equity: float
    initial_balance: float
    peak_equity: float
    daily_starting_equity: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    open_positions_count: int = 0
    total_invested: float = 0.0
    total_exposure_pct: float = 0.0       # (Invested / Equity) * 100
    current_drawdown_pct: float = 0.0     # ((Peak - Equity) / Peak) * 100
    daily_loss_pct: float = 0.0           # ((DailyStart - Equity) / DailyStart) * 100
    is_trading_halted: bool = False
    halt_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
