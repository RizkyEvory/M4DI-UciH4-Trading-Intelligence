"""
M4DI~UciH4 Trading Intelligence System
Risk Management Unit Tests (Phase 5)
Verifies position sizing math, risk/reward calculations, and institutional safety circuit breakers.
"""
import unittest

from risk.position_sizer import PositionSizer
from risk.risk_manager import RiskManager
from risk.models import AccountRiskProfile


class TestPositionSizing(unittest.TestCase):
    """Test exact mathematical position sizing and risk/reward analytics"""

    def test_standard_position_sizing(self):
        # Balance = $100,000, Risk = 1.0% ($1,000)
        # Entry = $2,650.00, SL = $2,630.00 (Distance = $20.00)
        # Units = $1,000 / $20 = 50.0 units
        # TP = $2,690.00 (Distance = $40.00, RR = 2.0)
        res = PositionSizer.calculate_size(
            account_balance=100000.0,
            risk_pct=1.0,
            entry_price=2650.00,
            stop_loss=2630.00,
            take_profit=2690.00
        )

        self.assertEqual(res.cash_risk, 1000.0)
        self.assertEqual(res.stop_loss_distance, 20.0)
        self.assertAlmostEqual(res.units, 50.0, places=2)
        self.assertEqual(res.potential_loss, 1000.0)
        self.assertEqual(res.potential_profit, 2000.0)
        self.assertEqual(res.risk_reward_ratio, 2.0)
        self.assertTrue(len(res.calculation_steps) >= 7)

    def test_capital_allocation_cap(self):
        # If SL is tiny ($0.10), raw units would be 10,000, costing $26,500,000!
        # Max capital cap (e.g. 50% = $50,000) must cap the units!
        res = PositionSizer.calculate_size(
            account_balance=100000.0,
            risk_pct=1.0,
            entry_price=2650.00,
            stop_loss=2649.90,  # $0.10 distance
            max_capital_allocation_pct=50.0
        )

        max_allowed_cost = 50000.0
        self.assertLessEqual(res.total_cost, max_allowed_cost + 1.0)

    def test_zero_or_negative_inputs(self):
        res_zero_bal = PositionSizer.calculate_size(0.0, 1.0, 100.0, 95.0)
        self.assertEqual(res_zero_bal.units, 0.0)

        res_zero_dist = PositionSizer.calculate_size(100000.0, 1.0, 100.0, 100.0)
        self.assertEqual(res_zero_dist.units, 0.0)


class TestRiskCircuitBreakers(unittest.TestCase):
    """Test institutional risk enforcement rules"""

    def setUp(self):
        self.rm = RiskManager(
            risk_per_trade_pct=1.0,
            max_exposure_pct=80.0,
            max_drawdown_limit_pct=15.0,
            daily_loss_limit_pct=3.0,
            max_open_positions=5
        )

    def test_order_approved_under_normal_conditions(self):
        profile = AccountRiskProfile(
            account_id="test",
            balance=100000.0,
            equity=100000.0,
            initial_balance=100000.0,
            peak_equity=100000.0,
            daily_starting_equity=100000.0,
            open_positions_count=1,
            total_invested=10000.0,
            current_drawdown_pct=0.0,
            daily_loss_pct=0.0
        )
        check = self.rm.evaluate_new_order(profile, order_cost=15000.0, potential_loss=1000.0, risk_reward=2.0)
        self.assertTrue(check.allowed)

    def test_max_open_positions_rejection(self):
        profile = AccountRiskProfile(
            account_id="test",
            balance=100000.0,
            equity=100000.0,
            initial_balance=100000.0,
            peak_equity=100000.0,
            daily_starting_equity=100000.0,
            open_positions_count=5,  # Limit is 5
            total_invested=25000.0
        )
        check = self.rm.evaluate_new_order(profile, order_cost=5000.0, potential_loss=1000.0)
        self.assertFalse(check.allowed)
        self.assertEqual(check.rule_violated, "MAX_OPEN_POSITIONS")

    def test_max_exposure_rejection(self):
        # Invested = $75,000, new order = $15,000 -> Projected = $90,000 (90% > 80% limit)
        profile = AccountRiskProfile(
            account_id="test",
            balance=100000.0,
            equity=100000.0,
            initial_balance=100000.0,
            peak_equity=100000.0,
            daily_starting_equity=100000.0,
            open_positions_count=2,
            total_invested=75000.0
        )
        check = self.rm.evaluate_new_order(profile, order_cost=15000.0, potential_loss=1000.0)
        self.assertFalse(check.allowed)
        self.assertEqual(check.rule_violated, "MAX_EXPOSURE")

    def test_max_drawdown_circuit_breaker(self):
        # Current Drawdown = 16.5% >= 15% limit
        profile = AccountRiskProfile(
            account_id="test",
            balance=83500.0,
            equity=83500.0,
            initial_balance=100000.0,
            peak_equity=100000.0,
            daily_starting_equity=85000.0,
            current_drawdown_pct=16.5
        )
        check = self.rm.evaluate_new_order(profile, order_cost=5000.0, potential_loss=500.0)
        self.assertFalse(check.allowed)
        self.assertEqual(check.rule_violated, "MAX_DRAWDOWN")

    def test_daily_loss_circuit_breaker(self):
        # Daily loss = 3.8% >= 3.0% limit
        profile = AccountRiskProfile(
            account_id="test",
            balance=96200.0,
            equity=96200.0,
            initial_balance=100000.0,
            peak_equity=100000.0,
            daily_starting_equity=100000.0,
            daily_loss_pct=3.8
        )
        check = self.rm.evaluate_new_order(profile, order_cost=5000.0, potential_loss=500.0)
        self.assertFalse(check.allowed)
        self.assertEqual(check.rule_violated, "DAILY_LOSS_LIMIT")


if __name__ == "__main__":
    unittest.main()
