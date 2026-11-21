"""
M4DI~UciH4 Trading Intelligence System
High-Precision Historical Backtest Engine (Phase 5)
Provides bar-by-bar simulation with strict zero-lookahead guarantees, intra-bar SL/TP execution,
commission fee deductions, slippage modeling, and equity tracking.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from config.constants import (
    SIDE_BUY,
    SIDE_SELL
)
from api.models import NormalizedCandle
from risk.position_sizer import PositionSizer
from backtesting.models import BacktestConfig, BacktestTrade, BacktestResult
from backtesting.strategies.base_strategy import BaseStrategy
from backtesting.metrics import PerformanceMetrics
from core.logger import get_app_logger

logger = get_app_logger("BacktestEngine")


class BacktestEngine:
    """Anti-lookahead institutional strategy backtester"""

    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()

    def run(
        self,
        strategy: BaseStrategy,
        candles: List[NormalizedCandle],
        symbol: str = "ASSET",
        timeframe: str = "1d",
        warmup_period: int = 30
    ) -> BacktestResult:
        """
        Executes historical bar-by-bar simulation.
        Guarantees zero data leakage: indicators and signals at bar [i]
        can only observe candles up to bar [i].
        """
        if not candles or len(candles) <= warmup_period:
            return BacktestResult(
                strategy_name=strategy.name,
                symbol=symbol,
                timeframe=timeframe,
                initial_capital=self.config.initial_capital,
                final_equity=self.config.initial_capital
            )

        cash = self.config.initial_capital
        equity = cash
        equity_curve: List[float] = []
        timestamps: List[str] = []
        closed_trades: List[BacktestTrade] = []

        active_trade: Optional[Dict[str, Any]] = None
        trade_counter = 0

        n_bars = len(candles)

        for i in range(warmup_period, n_bars):
            bar = candles[i]
            timestamps.append(bar.timestamp)

            # =========================================================================
            # 1. EVALUATE OPEN TRADE EXITS ON CURRENT BAR
            # =========================================================================
            if active_trade is not None:
                side = active_trade["side"]
                units = active_trade["units"]
                sl = active_trade["stop_loss"]
                tp = active_trade["take_profit"]

                exit_triggered = False
                exit_price = bar.close
                exit_reason = "SIGNAL_EXIT"

                if side == SIDE_BUY:
                    # Conservative check: if both SL and TP in bar range, assume SL hit first
                    if sl is not None and bar.low <= sl:
                        exit_price = sl
                        exit_reason = "SL"
                        exit_triggered = True
                    elif tp is not None and bar.high >= tp:
                        exit_price = tp
                        exit_reason = "TP"
                        exit_triggered = True
                else:  # SIDE_SELL
                    if sl is not None and bar.high >= sl:
                        exit_price = sl
                        exit_reason = "SL"
                        exit_triggered = True
                    elif tp is not None and bar.low <= tp:
                        exit_price = tp
                        exit_reason = "TP"
                        exit_triggered = True

                if exit_triggered:
                    # Apply slippage & fee on exit
                    slip = exit_price * (self.config.slippage_pct / 100.0)
                    real_exit = exit_price - slip if side == SIDE_BUY else exit_price + slip
                    fee = (units * real_exit) * (self.config.commission_pct / 100.0)

                    if side == SIDE_BUY:
                        gross_pnl = (real_exit - active_trade["entry_price"]) * units
                    else:
                        gross_pnl = (active_trade["entry_price"] - real_exit) * units

                    net_pnl = gross_pnl - fee - active_trade["entry_fee"]
                    capital_returned = (units * active_trade["entry_price"]) + gross_pnl - fee
                    cash += capital_returned

                    # Risk multiple calculation
                    risk_dist = abs(active_trade["entry_price"] - (sl or active_trade["entry_price"]))
                    r_mult = round(net_pnl / max(0.01, (units * risk_dist)), 2) if risk_dist > 0 else 0.0

                    trade_counter += 1
                    closed_trades.append(BacktestTrade(
                        trade_id=trade_counter,
                        symbol=symbol,
                        side=side,
                        units=units,
                        entry_time=active_trade["entry_time"],
                        entry_price=active_trade["entry_price"],
                        exit_time=bar.timestamp,
                        exit_price=real_exit,
                        stop_loss=sl,
                        take_profit=tp,
                        exit_reason=exit_reason,
                        fee=round(fee + active_trade["entry_fee"], 2),
                        slippage=round(slip + active_trade["slippage"], 4),
                        gross_pnl=round(gross_pnl, 2),
                        net_pnl=round(net_pnl, 2),
                        return_pct=round((net_pnl / max(1.0, units * active_trade["entry_price"])) * 100.0, 2),
                        r_multiple=r_mult
                    ))

                    active_trade = None

            # =========================================================================
            # 2. EVALUATE STRATEGY SIGNALS (STRICT ANTI-LOOKAHEAD: candles[:i+1])
            # =========================================================================
            if active_trade is None and i < n_bars - 1:
                # Slice candles strictly up to current bar [i]
                historical_slice = candles[:i + 1]
                sig, sl_candidate, tp_candidate = strategy.evaluate(historical_slice, i)

                if sig in ("BUY", "SELL"):
                    if sig == "SELL" and not self.config.allow_shorting:
                        pass
                    else:
                        # Next bar execution at Open (realistic execution)
                        next_bar = candles[i + 1]
                        entry_base = next_bar.open
                        slip = entry_base * (self.config.slippage_pct / 100.0)
                        entry_price = entry_base + slip if sig == "BUY" else entry_base - slip

                        # Default fallback SL if strategy omitted
                        sl = sl_candidate
                        if sl is None:
                            sl = entry_price * 0.98 if sig == "BUY" else entry_price * 1.02
                        tp = tp_candidate

                        # Size Position strictly respecting risk %
                        current_total_equity = cash
                        sizing = PositionSizer.calculate_size(
                            account_balance=current_total_equity,
                            risk_pct=self.config.risk_per_trade_pct,
                            entry_price=entry_price,
                            stop_loss=sl,
                            take_profit=tp,
                            fractional_units=True
                        )

                        fee = (sizing.units * entry_price) * (self.config.commission_pct / 100.0)
                        required_capital = sizing.total_cost + fee

                        if sizing.units > 0 and required_capital <= cash:
                            cash -= required_capital
                            active_trade = {
                                "side": sig,
                                "units": sizing.units,
                                "entry_price": entry_price,
                                "entry_time": next_bar.timestamp,
                                "stop_loss": sl,
                                "take_profit": tp,
                                "entry_fee": fee,
                                "slippage": slip
                            }

            # =========================================================================
            # 3. RECORD MARK-TO-MARKET EQUITY AT CURRENT BAR
            # =========================================================================
            unrealized = 0.0
            if active_trade is not None:
                units = active_trade["units"]
                e_price = active_trade["entry_price"]
                c_price = bar.close
                if active_trade["side"] == "BUY":
                    unrealized = (c_price - e_price) * units
                else:
                    unrealized = (e_price - c_price) * units
                equity = cash + (units * e_price) + unrealized
            else:
                equity = cash

            equity_curve.append(round(equity, 2))

        # =========================================================================
        # 4. CLOSE ANY REMAINING ACTIVE POSITION AT FINAL BAR
        # =========================================================================
        if active_trade is not None:
            last_bar = candles[-1]
            units = active_trade["units"]
            real_exit = last_bar.close
            fee = (units * real_exit) * (self.config.commission_pct / 100.0)

            if active_trade["side"] == "BUY":
                gross_pnl = (real_exit - active_trade["entry_price"]) * units
            else:
                gross_pnl = (active_trade["entry_price"] - real_exit) * units

            net_pnl = gross_pnl - fee - active_trade["entry_fee"]
            cash += (units * active_trade["entry_price"]) + gross_pnl - fee

            trade_counter += 1
            closed_trades.append(BacktestTrade(
                trade_id=trade_counter,
                symbol=symbol,
                side=active_trade["side"],
                units=units,
                entry_time=active_trade["entry_time"],
                entry_price=active_trade["entry_price"],
                exit_time=last_bar.timestamp,
                exit_price=real_exit,
                stop_loss=active_trade["stop_loss"],
                take_profit=active_trade["take_profit"],
                exit_reason="END_OF_DATA",
                fee=round(fee + active_trade["entry_fee"], 2),
                slippage=round(active_trade["slippage"], 4),
                gross_pnl=round(gross_pnl, 2),
                net_pnl=round(net_pnl, 2),
                return_pct=round((net_pnl / max(1.0, units * active_trade["entry_price"])) * 100.0, 2),
                r_multiple=0.0
            ))
            if equity_curve:
                equity_curve[-1] = round(cash, 2)

        # =========================================================================
        # 5. COMPILE QUANTITATIVE METRICS
        # =========================================================================
        perf = PerformanceMetrics.calculate_all(
            trades=closed_trades,
            equity_curve=equity_curve,
            initial_capital=self.config.initial_capital
        )

        return BacktestResult(
            strategy_name=strategy.name,
            symbol=symbol,
            timeframe=timeframe,
            initial_capital=self.config.initial_capital,
            final_equity=equity_curve[-1] if equity_curve else self.config.initial_capital,
            total_trades=perf["total_trades"],
            winning_trades=perf["winning_trades"],
            losing_trades=perf["losing_trades"],
            win_rate=perf["win_rate"],
            profit_factor=perf["profit_factor"],
            total_return_pct=perf["total_return_pct"],
            cagr=perf["cagr"],
            max_drawdown_pct=perf["max_drawdown_pct"],
            max_drawdown_duration=perf["max_drawdown_duration"],
            sharpe_ratio=perf["sharpe_ratio"],
            sortino_ratio=perf["sortino_ratio"],
            avg_trade_pnl=perf["avg_trade_pnl"],
            avg_win=perf["avg_win"],
            avg_loss=perf["avg_loss"],
            expectancy=perf["expectancy"],
            trades=closed_trades,
            equity_curve=equity_curve,
            drawdown_curve=perf.get("drawdown_curve", []),
            timestamps=timestamps
        )
