"""
M4DI~UciH4 Trading Intelligence System
Risk Management Rules & Enforcement Engine (Phase 5)
Enforces Max Portfolio Exposure, Max Drawdown Circuit Breakers, Daily Loss Limits,
Max Open Positions, and Minimum Risk/Reward Standards.
"""
from typing import Dict, Any, List, Optional
from config.constants import (
    DEFAULT_RISK_PER_TRADE_PCT,
    DEFAULT_MAX_PORTFOLIO_EXPOSURE_PCT,
    DEFAULT_MAX_DRAWDOWN_LIMIT_PCT,
    DEFAULT_DAILY_LOSS_LIMIT_PCT,
    DEFAULT_MAX_OPEN_POSITIONS
)
from risk.models import PositionSizeResult, RiskCheckResult, AccountRiskProfile
from risk.position_sizer import PositionSizer
from core.logger import get_app_logger

logger = get_app_logger("RiskManager")


class RiskManager:
    """Institutional Portfolio Risk Governor"""

    def __init__(
        self,
        risk_per_trade_pct: float = DEFAULT_RISK_PER_TRADE_PCT,
        max_exposure_pct: float = DEFAULT_MAX_PORTFOLIO_EXPOSURE_PCT,
        max_drawdown_limit_pct: float = DEFAULT_MAX_DRAWDOWN_LIMIT_PCT,
        daily_loss_limit_pct: float = DEFAULT_DAILY_LOSS_LIMIT_PCT,
        max_open_positions: int = DEFAULT_MAX_OPEN_POSITIONS
    ):
        self.risk_per_trade_pct = risk_per_trade_pct
        self.max_exposure_pct = max_exposure_pct
        self.max_drawdown_limit_pct = max_drawdown_limit_pct
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_open_positions = max_open_positions
        self._peak_equity: float = 0.0

    def calculate_drawdown_pct(self, current_equity: float, peak_equity: Optional[float] = None) -> float:
        """Calculate drawdown percentage from peak equity"""
        if peak_equity is None or peak_equity <= 0:
            if not hasattr(self, "_peak_equity") or self._peak_equity <= 0:
                self._peak_equity = current_equity
            elif current_equity > self._peak_equity:
                self._peak_equity = current_equity
            peak_equity = self._peak_equity

        if peak_equity <= 0:
            return 0.0
        dd = ((peak_equity - current_equity) / peak_equity) * 100.0
        return max(0.0, round(dd, 2))

    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        take_profit: Optional[float] = None,
        custom_risk_pct: Optional[float] = None,
        risk_pct: Optional[float] = None,
        **kwargs
    ) -> PositionSizeResult:
        """Helper to size position using current risk configuration (supports both custom_risk_pct and risk_pct aliases)"""
        effective_risk = custom_risk_pct if custom_risk_pct is not None else (risk_pct if risk_pct is not None else self.risk_per_trade_pct)
        return PositionSizer.calculate_size(
            account_balance=account_balance,
            risk_pct=effective_risk,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            max_capital_allocation_pct=self.max_exposure_pct
        )

    def evaluate_new_order(
        self,
        profile: AccountRiskProfile,
        order_cost: float,
        potential_loss: float,
        min_rr_ratio: float = 1.0,
        risk_reward: Optional[float] = None
    ) -> RiskCheckResult:
        """
        Validates whether a candidate trade passes all institutional safety checks:
        1. Max Drawdown Circuit Breaker
        2. Daily Loss Limit Circuit Breaker
        3. Maximum Open Positions Limit
        4. Maximum Portfolio Exposure Limit
        5. Minimum Risk/Reward Ratio Threshold
        """
        # 1. Max Drawdown Circuit Breaker
        if profile.current_drawdown_pct >= self.max_drawdown_limit_pct:
            msg = f"Order REJECTED: Maximum Drawdown Limit reached ({profile.current_drawdown_pct:.1f}% >= {self.max_drawdown_limit_pct:.1f}%). Trading circuit breaker active."
            logger.warning(f"🚨 {msg}")
            return RiskCheckResult(allowed=False, reason=msg, rule_violated="MAX_DRAWDOWN")

        # 2. Daily Loss Limit Circuit Breaker
        if profile.daily_loss_pct >= self.daily_loss_limit_pct:
            msg = f"Order REJECTED: Daily Loss Limit exceeded ({profile.daily_loss_pct:.1f}% >= {self.daily_loss_limit_pct:.1f}%). Trading paused for current session."
            logger.warning(f"🚨 {msg}")
            return RiskCheckResult(allowed=False, reason=msg, rule_violated="DAILY_LOSS_LIMIT")

        # 3. Maximum Open Positions Limit
        if profile.open_positions_count >= self.max_open_positions:
            msg = f"Order REJECTED: Maximum Open Positions limit ({profile.open_positions_count} / {self.max_open_positions}) reached. Close existing trades first."
            logger.info(f"🛡️ {msg}")
            return RiskCheckResult(allowed=False, reason=msg, rule_violated="MAX_OPEN_POSITIONS")

        # 4. Maximum Portfolio Exposure Limit
        projected_invested = profile.total_invested + order_cost
        projected_exposure_pct = (projected_invested / max(1.0, profile.equity)) * 100.0
        if projected_exposure_pct > self.max_exposure_pct:
            msg = f"Order REJECTED: Portfolio exposure limit exceeded. Projected {projected_exposure_pct:.1f}% > Max {self.max_exposure_pct:.1f}%."
            logger.info(f"🛡️ {msg}")
            return RiskCheckResult(allowed=False, reason=msg, rule_violated="MAX_EXPOSURE")

        # 5. Risk/Reward Check
        if risk_reward is not None and risk_reward < min_rr_ratio:
            msg = f"Order WARNING: Risk/Reward ratio (1:{risk_reward:.2f}) is below minimum threshold (1:{min_rr_ratio:.2f})."
            # Return allowed but with advisory notice
            return RiskCheckResult(
                allowed=True,
                reason=msg,
                rule_violated="SUBOPTIMAL_RR",
                metrics={"risk_reward": risk_reward, "min_rr": min_rr_ratio}
            )

        return RiskCheckResult(
            allowed=True,
            reason="All risk parameters validated successfully. Order approved for execution.",
            metrics={"projected_exposure_pct": projected_exposure_pct}
        )

    @staticmethod
    def calculate_risk_profile(
        account_id: str,
        balance: float,
        initial_balance: float,
        peak_equity: float,
        daily_start_equity: float,
        open_positions: List[Any]
    ) -> AccountRiskProfile:
        """Constructs an instantaneous risk audit profile for the portfolio"""
        total_invested = 0.0
        total_unrealized = 0.0

        for p in open_positions:
            units = getattr(p, "units", 0.0)
            entry = getattr(p, "entry_price", 0.0)
            curr = getattr(p, "current_price", entry)
            side = getattr(p, "side", "BUY")

            cost = units * entry
            total_invested += cost

            if side == "BUY":
                pnl = (curr - entry) * units
            else:
                pnl = (entry - curr) * units
            total_unrealized += pnl

        equity = balance + total_unrealized
        new_peak = max(peak_equity, equity)

        # Drawdown from peak equity
        dd_pct = round(((new_peak - equity) / new_peak) * 100.0, 2) if new_peak > 0 else 0.0

        # Daily loss from daily starting equity
        daily_loss_pct = round(((daily_start_equity - equity) / daily_start_equity) * 100.0, 2) if daily_start_equity > 0 else 0.0
        daily_loss_pct = max(0.0, daily_loss_pct)

        # Exposure percentage
        exposure_pct = round((total_invested / equity) * 100.0, 2) if equity > 0 else 0.0

        return AccountRiskProfile(
            account_id=account_id,
            balance=round(balance, 2),
            equity=round(equity, 2),
            initial_balance=round(initial_balance, 2),
            peak_equity=round(new_peak, 2),
            daily_starting_equity=round(daily_start_equity, 2),
            unrealized_pnl=round(total_unrealized, 2),
            realized_pnl=round(balance - initial_balance, 2),
            open_positions_count=len(open_positions),
            total_invested=round(total_invested, 2),
            total_exposure_pct=exposure_pct,
            current_drawdown_pct=dd_pct,
            daily_loss_pct=daily_loss_pct
        )
