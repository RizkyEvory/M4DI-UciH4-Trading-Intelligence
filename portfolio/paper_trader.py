"""
M4DI~UciH4 Trading Intelligence System
Paper Trading Execution Engine (Phase 5)
Simulates realistic broker order routing with fees, slippage, and automated SL/TP limit monitoring.
STRICTLY PAPER / SIMULATION ONLY - NO REAL MONEY ORDERS.
"""
from typing import Dict, Any, List, Optional, Tuple

from config.constants import (
    SIDE_BUY,
    SIDE_SELL,
    TRADE_SL_HIT,
    TRADE_TP_HIT,
    TRADE_EXIT,
    DEFAULT_COMMISSION_PCT,
    DEFAULT_SLIPPAGE_PCT
)
from portfolio.models import Position, PortfolioSummary
from portfolio.portfolio_manager import PortfolioManager
from risk.risk_manager import RiskManager
from risk.models import PositionSizeResult, RiskCheckResult
from core.logger import get_app_logger

logger = get_app_logger("PaperTrader")


class PaperTrader:
    """Simulated execution desk validating against risk limits before paper fills"""

    def __init__(
        self,
        portfolio_manager: PortfolioManager,
        risk_manager: RiskManager,
        commission_pct: float = DEFAULT_COMMISSION_PCT,
        slippage_pct: float = DEFAULT_SLIPPAGE_PCT
    ):
        self.pm = portfolio_manager
        self.rm = risk_manager
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct

    def execute_paper_order(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: Optional[float] = None,
        custom_risk_pct: Optional[float] = None,
        override_units: Optional[float] = None,
        account_id: str = "default_paper",
        notes: str = ""
    ) -> Tuple[bool, str, Optional[Position]]:
        """
        Calculates position sizing, evaluates all institutional risk limits,
        and if approved, executes the simulated fill.
        """
        # 1. Fetch live balance & equity
        cash = self.pm.get_account_balance(account_id)
        open_positions = self.pm.get_open_positions(account_id)
        summary = self.pm.get_portfolio_summary(account_id)

        # 2. Position Sizing
        if override_units is not None and override_units > 0:
            units = override_units
            sl_dist = abs(entry_price - stop_loss)
            cost = units * entry_price
            pot_loss = units * sl_dist
            pot_profit = units * abs(take_profit - entry_price) if take_profit else 0.0
            rr = pot_profit / pot_loss if pot_loss > 0 else 0.0
            sizing = PositionSizeResult(
                units=units, cash_risk=pot_loss, total_cost=cost, entry_price=entry_price,
                stop_loss=stop_loss, take_profit=take_profit, stop_loss_distance=sl_dist,
                potential_loss=pot_loss, potential_profit=pot_profit, risk_reward_ratio=rr
            )
        else:
            sizing = self.rm.calculate_position_size(
                account_balance=summary.total_equity,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                custom_risk_pct=custom_risk_pct
            )

        if sizing.units <= 0:
            return False, "Sized position is 0 units. Check balance and SL distance.", None

        # 3. Risk Audit Profile Check
        risk_profile = self.rm.calculate_risk_profile(
            account_id=account_id,
            balance=cash,
            initial_balance=summary.initial_balance,
            peak_equity=summary.total_equity,
            daily_start_equity=summary.initial_balance,
            open_positions=open_positions
        )

        risk_check = self.rm.evaluate_new_order(
            profile=risk_profile,
            order_cost=sizing.total_cost,
            potential_loss=sizing.potential_loss,
            risk_reward=sizing.risk_reward_ratio
        )

        if not risk_check.allowed:
            return False, risk_check.reason, None

        # 4. Check available cash
        fee = round(sizing.total_cost * (self.commission_pct / 100.0), 2)
        slippage = round(entry_price * (self.slippage_pct / 100.0), 4)

        if (sizing.total_cost + fee) > cash:
            return False, f"Insufficient cash: Required ${sizing.total_cost + fee:,.2f}, Available ${cash:,.2f}", None

        # 5. Execute Fill via PortfolioManager
        position = self.pm.open_position(
            symbol=symbol,
            side=side,
            units=sizing.units,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            fee=fee,
            slippage=slippage,
            account_id=account_id,
            notes=notes
        )

        success_msg = f"Paper order FILLED: {side} {sizing.units} {symbol} @ {entry_price:.4f} (Fee: ${fee:.2f}, SL: {stop_loss:.4f})"
        return True, success_msg, position

    def close_paper_position(
        self,
        position_id: str,
        exit_price: float,
        exit_reason: str = "MANUAL_CLOSE",
        account_id: str = "default_paper"
    ) -> Tuple[bool, str]:
        """Manually close an open paper position at market price"""
        try:
            pos, pnl = self.pm.close_position(
                position_id=position_id,
                exit_price=exit_price,
                trade_type=exit_reason,
                account_id=account_id
            )
            return True, f"Closed position [{position_id}] {pos.symbol} @ {exit_price:.4f} (Net PnL: ${pnl:+,.2f})"
        except Exception as e:
            return False, str(e)

    def check_sl_tp_triggers(
        self,
        symbol: str,
        high: float,
        low: float,
        account_id: str = "default_paper"
    ) -> List[Position]:
        """
        Monitors incoming bar High and Low to trigger automatic Stop Loss or Take Profit exits.
        """
        closed_positions: List[Position] = []
        open_positions = self.pm.get_open_positions(account_id)

        for pos in open_positions:
            if pos.symbol.upper() != symbol.upper():
                continue

            # Check BUY position
            if pos.side == SIDE_BUY:
                # 1. Stop Loss Hit
                if pos.stop_loss is not None and low <= pos.stop_loss:
                    fee = round((pos.units * pos.stop_loss) * (self.commission_pct / 100.0), 2)
                    closed_pos, pnl = self.pm.close_position(
                        position_id=pos.id,
                        exit_price=pos.stop_loss,
                        fee=fee,
                        trade_type=TRADE_SL_HIT,
                        account_id=account_id,
                        notes=f"Automated Stop Loss triggered at {pos.stop_loss:.4f}"
                    )
                    closed_positions.append(closed_pos)
                    logger.info(f"🛑 SL Triggered on {pos.symbol}: Exited @ {pos.stop_loss:.4f} (PnL: ${pnl:+,.2f})")

                # 2. Take Profit Hit
                elif pos.take_profit is not None and high >= pos.take_profit:
                    fee = round((pos.units * pos.take_profit) * (self.commission_pct / 100.0), 2)
                    closed_pos, pnl = self.pm.close_position(
                        position_id=pos.id,
                        exit_price=pos.take_profit,
                        fee=fee,
                        trade_type=TRADE_TP_HIT,
                        account_id=account_id,
                        notes=f"Automated Take Profit triggered at {pos.take_profit:.4f}"
                    )
                    closed_positions.append(closed_pos)
                    logger.info(f"🎯 TP Triggered on {pos.symbol}: Exited @ {pos.take_profit:.4f} (PnL: ${pnl:+,.2f})")

            # Check SELL position
            elif pos.side == SIDE_SELL:
                # 1. Stop Loss Hit (Price rises above SL)
                if pos.stop_loss is not None and high >= pos.stop_loss:
                    fee = round((pos.units * pos.stop_loss) * (self.commission_pct / 100.0), 2)
                    closed_pos, pnl = self.pm.close_position(
                        position_id=pos.id,
                        exit_price=pos.stop_loss,
                        fee=fee,
                        trade_type=TRADE_SL_HIT,
                        account_id=account_id,
                        notes=f"Automated Stop Loss triggered at {pos.stop_loss:.4f}"
                    )
                    closed_positions.append(closed_pos)
                    logger.info(f"🛑 SL Triggered on Short {pos.symbol}: Exited @ {pos.stop_loss:.4f} (PnL: ${pnl:+,.2f})")

                # 2. Take Profit Hit (Price falls below TP)
                elif pos.take_profit is not None and low <= pos.take_profit:
                    fee = round((pos.units * pos.take_profit) * (self.commission_pct / 100.0), 2)
                    closed_pos, pnl = self.pm.close_position(
                        position_id=pos.id,
                        exit_price=pos.take_profit,
                        fee=fee,
                        trade_type=TRADE_TP_HIT,
                        account_id=account_id,
                        notes=f"Automated Take Profit triggered at {pos.take_profit:.4f}"
                    )
                    closed_positions.append(closed_pos)
                    logger.info(f"🎯 TP Triggered on Short {pos.symbol}: Exited @ {pos.take_profit:.4f} (PnL: ${pnl:+,.2f})")

        return closed_positions
