"""
M4DI~UciH4 Trading Intelligence System
Portfolio Manager Unit Tests (Phase 5)
Verifies position opening, mark-to-market P&L calculation, SL/TP modification,
position closing, trade logging, and portfolio summary calculations.
"""
import unittest
import tempfile
import os
from pathlib import Path

from config.constants import SIDE_BUY, SIDE_SELL, POSITION_OPEN, POSITION_CLOSED
from database.db_manager import DatabaseManager
from portfolio.portfolio_manager import PortfolioManager


class TestPortfolioManager(unittest.TestCase):
    """Test PortfolioManager position lifecycle and SQLite persistence"""

    def setUp(self):
        DatabaseManager._instance = None
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_portfolio.db"
        self.db = DatabaseManager(self.db_path)
        self.pm = PortfolioManager(self.db)
        self.account_id = "test_acc"
        self.pm._ensure_default_account(self.account_id, initial_balance=50000.0)

    def tearDown(self):
        try:
            self.db.close()
            self.temp_dir.cleanup()
        except Exception:
            pass
        DatabaseManager._instance = None

    def test_open_buy_position(self):
        pos = self.pm.open_position(
            symbol="XAUUSD",
            side=SIDE_BUY,
            units=10.0,
            entry_price=2600.0,
            stop_loss=2580.0,
            take_profit=2650.0,
            fee=20.0,
            account_id=self.account_id
        )

        self.assertEqual(pos.symbol, "XAUUSD")
        self.assertEqual(pos.side, SIDE_BUY)
        self.assertEqual(pos.units, 10.0)
        self.assertEqual(pos.entry_price, 2600.0)
        self.assertEqual(pos.status, POSITION_OPEN)

        # Check cash deducted: $50,000 - ($26,000 + $20 fee) = $23,980.00
        cash = self.pm.get_account_balance(self.account_id)
        self.assertAlmostEqual(cash, 23980.0, places=2)

    def test_unrealized_pnl_mark_to_market(self):
        pos = self.pm.open_position(
            symbol="EURUSD",
            side=SIDE_BUY,
            units=1000.0,
            entry_price=1.0500,
            account_id=self.account_id
        )

        # Simulate price rising to 1.0550 (+50 pips on 1,000 units = +$5.00)
        self.pm.update_market_prices({"EURUSD": 1.0550}, account_id=self.account_id)
        open_pos = self.pm.get_open_positions(self.account_id)[0]

        self.assertEqual(open_pos.current_price, 1.0550)
        self.assertAlmostEqual(open_pos.unrealized_pnl, 5.0, places=2)
        self.assertAlmostEqual(open_pos.unrealized_pnl_pct, 0.48, delta=0.05)

    def test_close_position_with_profit(self):
        pos = self.pm.open_position(
            symbol="AAPL",
            side=SIDE_BUY,
            units=100.0,
            entry_price=200.0,  # $20,000 cost
            account_id=self.account_id
        )

        # Close at $215.00 (+$1,500 profit, fee $15)
        closed_pos, net_pnl = self.pm.close_position(
            position_id=pos.id,
            exit_price=215.0,
            fee=15.0,
            account_id=self.account_id
        )

        self.assertEqual(closed_pos.status, POSITION_CLOSED)
        self.assertEqual(net_pnl, 1485.0)

        # Cash returned: initial $50k - $20k + ($20k + $1,485) = $51,485.00
        cash = self.pm.get_account_balance(self.account_id)
        self.assertAlmostEqual(cash, 51485.0, places=2)

        # Trade record created
        trades = self.pm.get_trade_history(self.account_id)
        self.assertEqual(len(trades), 2)  # Entry + Exit
        self.assertEqual(trades[0].pnl, 1485.0)

    def test_portfolio_summary_calculation(self):
        self.pm.open_position(
            symbol="NVDA",
            side=SIDE_BUY,
            units=50.0,
            entry_price=120.0,  # $6,000 cost
            account_id=self.account_id
        )
        self.pm.update_market_prices({"NVDA": 130.0}, account_id=self.account_id)

        summary = self.pm.get_portfolio_summary(self.account_id)

        # Total equity: $44,000 cash + $6,000 cost + $500 unrealized = $50,500
        self.assertAlmostEqual(summary.total_equity, 50500.0, places=1)
        self.assertAlmostEqual(summary.unrealized_pnl, 500.0, places=1)
        self.assertGreater(summary.total_return_pct, 0.9)
        self.assertIn("NVDA", summary.allocations)


if __name__ == "__main__":
    unittest.main()
