"""
M4DI~UciH4 Trading Intelligence System
Position Sizing & Risk/Reward Calculation Engine (Phase 5)
Calculates exact mathematical trade units based on Account Balance, Risk %,
Entry Price, and Stop-Loss distance with step-by-step transparent auditing.
"""
from typing import Optional, List
from risk.models import PositionSizeResult


class PositionSizer:
    """Mathematical position sizer ensuring institutional capital preservation"""

    @classmethod
    def calculate_size(
        cls,
        account_balance: float,
        risk_pct: float,
        entry_price: float,
        stop_loss: float,
        take_profit: Optional[float] = None,
        max_capital_allocation_pct: Optional[float] = None,
        fractional_units: bool = True
    ) -> PositionSizeResult:
        """
        Calculates position size strictly respecting risk constraints.

        Formula:
            Cash Risk ($) = Account Balance * (Risk Pct / 100)
            Stop Loss Distance ($) = |Entry Price - Stop Loss|
            Units = Cash Risk / Stop Loss Distance
        """
        steps: List[str] = []

        if account_balance <= 0:
            return PositionSizeResult(
                units=0.0, cash_risk=0.0, total_cost=0.0, entry_price=entry_price,
                stop_loss=stop_loss, calculation_steps=["Error: Account balance must be positive."]
            )

        if entry_price <= 0:
            return PositionSizeResult(
                units=0.0, cash_risk=0.0, total_cost=0.0, entry_price=entry_price,
                stop_loss=stop_loss, calculation_steps=["Error: Entry price must be positive."]
            )

        sl_distance = abs(entry_price - stop_loss)
        if sl_distance <= 0:
            return PositionSizeResult(
                units=0.0, cash_risk=0.0, total_cost=0.0, entry_price=entry_price,
                stop_loss=stop_loss, calculation_steps=["Error: Stop loss cannot equal entry price (Zero distance)."]
            )

        # 1. Cash Risk
        cash_risk = round(account_balance * (risk_pct / 100.0), 2)
        steps.append(f"1. Cash Risk = Balance (${account_balance:,.2f}) × Risk% ({risk_pct}%) = ${cash_risk:,.2f}")

        # 2. Stop Loss Distance
        steps.append(f"2. Stop-Loss Distance = |Entry (${entry_price:,.4f}) - StopLoss (${stop_loss:,.4f})| = ${sl_distance:,.4f} per unit")

        # 3. Raw Position Size (Units)
        raw_units = cash_risk / sl_distance
        steps.append(f"3. Raw Units = Cash Risk (${cash_risk:,.2f}) ÷ SL Distance (${sl_distance:,.4f}) = {raw_units:,.4f} units")

        # 4. Maximum Allowed Position by Portfolio Capital (if capped)
        if max_capital_allocation_pct is not None:
            max_capital_allowed = account_balance * (max_capital_allocation_pct / 100.0)
            max_units_by_capital = max_capital_allowed / entry_price
            final_units = min(raw_units, max_units_by_capital)
            steps.append(f"4. Max Units by Capital Limit ({max_capital_allocation_pct}%) = ${max_capital_allowed:,.2f} ÷ ${entry_price:,.4f} = {max_units_by_capital:,.4f} units")
        else:
            final_units = raw_units
            steps.append(f"4. Pure Risk-Based Units = {raw_units:,.4f} units")

        # 5. Final Units Sizing
        if not fractional_units:
            final_units = float(int(final_units))
            steps.append(f"5. Rounded to whole units = {final_units:,.0f} units")
        else:
            final_units = round(final_units, 4)
            steps.append(f"5. Final Sized Position = {final_units:,.4f} units")

        # 6. Total Position Value
        total_cost = round(final_units * entry_price, 2)
        steps.append(f"6. Total Position Value = {final_units:,.4f} units × ${entry_price:,.4f} = ${total_cost:,.2f}")

        # 7. Potential Loss
        potential_loss = round(final_units * sl_distance, 2)
        steps.append(f"7. Max Potential Loss = {final_units:,.4f} units × ${sl_distance:,.4f} = ${potential_loss:,.2f}")

        # 8. Potential Profit & Risk/Reward
        potential_profit = 0.0
        risk_reward = 0.0
        if take_profit is not None and take_profit > 0:
            tp_distance = abs(take_profit - entry_price)
            potential_profit = round(final_units * tp_distance, 2)
            if potential_loss > 0:
                risk_reward = round(potential_profit / potential_loss, 2)
            steps.append(f"8. Potential Profit (TP @ ${take_profit:,.4f}) = {final_units:,.4f} × ${tp_distance:,.4f} = ${potential_profit:,.2f}")
            steps.append(f"9. Risk/Reward Ratio = Profit (${potential_profit:,.2f}) ÷ Loss (${potential_loss:,.2f}) = 1 : {risk_reward:.2f}")
        else:
            steps.append("8. No Take Profit specified (R:R calculation skipped).")

        return PositionSizeResult(
            units=final_units,
            cash_risk=cash_risk,
            total_cost=total_cost,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            stop_loss_distance=sl_distance,
            potential_loss=potential_loss,
            potential_profit=potential_profit,
            risk_reward_ratio=risk_reward,
            calculation_steps=steps
        )
