"""
M4DI~UciH4 Trading Intelligence System
Backtesting Models & Configuration (Phase 5)
Data structures for simulation parameters, trade records, equity curves, and performance metrics.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime

from config.constants import (
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_RISK_PER_TRADE_PCT,
    DEFAULT_COMMISSION_PCT,
    DEFAULT_SLIPPAGE_PCT
)


@dataclass
class BacktestConfig:
    """Historical simulation settings with fee and slippage models"""
    initial_capital: float = DEFAULT_INITIAL_CAPITAL
    risk_per_trade_pct: float = DEFAULT_RISK_PER_TRADE_PCT
    commission_pct: float = DEFAULT_COMMISSION_PCT
    slippage_pct: float = DEFAULT_SLIPPAGE_PCT
    allow_shorting: bool = True
    max_open_trades: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BacktestTrade:
    """Detailed log of a single backtest execution lifecycle"""
    trade_id: int
    symbol: str
    side: str                             # BUY or SELL
    units: float
    entry_time: str
    entry_price: float
    exit_time: str
    exit_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    exit_reason: str                      # SL, TP, SIGNAL_EXIT, END_OF_DATA
    fee: float = 0.0
    slippage: float = 0.0
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    return_pct: float = 0.0
    r_multiple: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BacktestResult:
    """Consolidated quantitative strategy backtest performance summary"""
    strategy_name: str
    symbol: str
    timeframe: str
    initial_capital: float
    final_equity: float
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0                 # Win %
    profit_factor: float = 0.0            # Gross Profit / Gross Loss
    total_return_pct: float = 0.0         # % Return
    cagr: float = 0.0                     # Compound Annual Growth Rate %
    max_drawdown_pct: float = 0.0         # Peak-to-trough drop %
    max_drawdown_duration: int = 0        # Bars underwater
    sharpe_ratio: float = 0.0             # Annualized Sharpe ratio
    sortino_ratio: float = 0.0            # Annualized Sortino ratio
    avg_trade_pnl: float = 0.0            # Mean $ per trade
    avg_win: float = 0.0                  # Mean winning trade ($)
    avg_loss: float = 0.0                 # Mean losing trade ($)
    expectancy: float = 0.0               # Expectancy ($ per trade)
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["trades"] = [t.to_dict() for t in self.trades]
        return data
