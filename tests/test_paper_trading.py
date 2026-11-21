"""
M4DI~UciH4 Trading Intelligence System
Paper Trading Unit Tests (Phase 5)
Verifies simulated order routing, risk enforcement, fee/slippage modeling,
and automated Stop-Loss / Take-Profit bar trigger evaluations.
"""
import unittest
import tempfile
from pathlib import Path

from config.constants import SIDE_BUY, SIDE_SELL, POSITION_CLOSED
from database.db_manager import DatabaseManager
from portfolio.portfolio_manager import PortfolioManager
from risk.risk_manager import RiskManager
from portfolio.paper_trader import PaperTrader


class TestPaperTrader(unittest.TestCase):
    """Test PaperTrader order workflow and automated limit triggers"""

    def setUp(self):
        DatabaseManager._instance = None
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_paper.db"
        self.db = DatabaseManager(self.db_path)
        self.pm = PortfolioManager(self.db)
        self.rm = RiskManager(risk_per_trade_pct=1.0, max_open_positions=3)
        self.trader = PaperTrader(self.pm, self.rm, commission_pct=0.05, slippage_pct=0.02)
        self.account_id = "default_paper"

    def tearDown(self):
        try:
            self.db.close()
            self.temp_dir.cleanup()
        except Exception:
            pass
        DatabaseManager._instance = None

    def test_execute_paper_order_success(self):
        ok, msg, pos = self.trader.execute_paper_order(
            symbol="XAU/USD",
            side=SIDE_BUY,
            entry_price=2600.0,
            stop_loss=2580.0,
            take_profit=2650.0
        )

        self.assertTrue(ok)
        self.assertIsNotNone(pos)
        self.assertEqual(pos.symbol, "XAU/USD")
        self.assertGreater(pos.units, 0.0)

    def test_automated_stop_loss_hit(self):
        # Open Buy with SL at $2,580.00
        ok, _, pos = self.trader.execute_paper_order(
            symbol="XAU/USD",
            side=SIDE_BUY,
            entry_price=2600.0,
            stop_loss=2580.0,
            take_profit=2650.0
        )
        self.assertTrue(ok)

        # Incoming candle plunges with Low = $2,575.00 (below SL)
        closed = self.trader.check_sl_tp_triggers(
            symbol="XAU/USD",
            high=2595.0,
            low=2575.0
        )

        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0].status, POSITION_CLOSED)
        self.assertLess(closed[0].realized_pnl, 0.0)

    def test_automated_take_profit_hit(self):
        # Open Buy with TP at $2,650.00
        ok, _, pos = self.trader.execute_paper_order(
            symbol="XAU/USD",
            side=SIDE_BUY,
            entry_price=2600.0,
            stop_loss=2580.0,
            take_profit=2650.0
        )
        self.assertTrue(ok)

        # Incoming candle spikes with High = $2,655.00 (above TP)
        closed = self.trader.check_sl_tp_triggers(
            symbol="XAU/USD",
            high=2655.0,
            low=2610.0
        )

        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0].status, POSITION_CLOSED)
        self.assertGreater(closed[0].realized_pnl, 0.0)


if __name__ == "__main__":
    unittest.main()
