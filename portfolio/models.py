"""
M4DI~UciH4 Trading Intelligence System
Portfolio & Paper Trading Data Models (Phase 5)
Defines Position, TradeRecord, and PortfolioSummary structures.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime

from config.constants import (
    SIDE_BUY,
    SIDE_SELL,
    POSITION_OPEN,
    POSITION_CLOSED,
    TRADE_ENTRY,
    TRADE_EXIT
)


@dataclass
class Position:
    """Represents an active or closed paper trading position"""
    id: str
    account_id: str
    symbol: str
    side: str = SIDE_BUY                  # BUY or SELL
    units: float = 0.0
    entry_price: float = 0.0
    current_price: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: str = POSITION_OPEN           # OPEN or CLOSED
    realized_pnl: float = 0.0
    opened_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    closed_at: Optional[str] = None
    notes: str = ""

    @property
    def position_id(self) -> str:
        return self.id

    @property
    def market_value(self) -> float:
        """Total current asset value"""
        return round(self.units * self.current_price, 2)

    @property
    def cost_basis(self) -> float:
        """Total original entry capital cost"""
        return round(self.units * self.entry_price, 2)

    @property
    def unrealized_pnl(self) -> float:
        """Current paper profit or loss"""
        if self.status == POSITION_CLOSED:
            return 0.0
        if self.side == SIDE_BUY:
            return round((self.current_price - self.entry_price) * self.units, 2)
        else:
            return round((self.entry_price - self.current_price) * self.units, 2)

    @property
    def unrealized_pnl_pct(self) -> float:
        """Return percentage on capital committed"""
        if self.status == POSITION_CLOSED or self.cost_basis <= 0:
            return 0.0
        return round((self.unrealized_pnl / self.cost_basis) * 100.0, 2)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["market_value"] = self.market_value
        data["cost_basis"] = self.cost_basis
        data["unrealized_pnl"] = self.unrealized_pnl
        data["unrealized_pnl_pct"] = self.unrealized_pnl_pct
        return data


@dataclass
class TradeRecord:
    """Immutable ledger record of an individual buy or sell execution"""
    id: str
    account_id: str
    position_id: str
    symbol: str
    side: str                             # BUY or SELL
    units: float
    price: float
    fee: float = 0.0
    slippage: float = 0.0
    pnl: float = 0.0
    trade_type: str = TRADE_ENTRY         # ENTRY, EXIT, SL_HIT, TP_HIT
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PortfolioSummary:
    """Consolidated institutional portfolio telemetry"""
    account_id: str
    name: str
    cash: float
    invested_capital: float
    total_equity: float
    initial_balance: float
    unrealized_pnl: float
    realized_pnl: float
    total_return_pct: float
    exposure_pct: float
    open_positions_count: int
    allocations: Dict[str, float] = field(default_factory=dict)  # Symbol -> % of Equity
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
