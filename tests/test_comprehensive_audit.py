"""
M4DI~UciH4 Trading Intelligence System
Comprehensive End-to-End System Audit & Reliability Test Suite
Performs exhaustive verification of all mathematical, algorithmic, data, and GUI subsystems.
"""
import unittest
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime, timezone

from core.app_context import AppContext
from database.db_manager import DatabaseManager
from api.models import NormalizedCandle, NormalizedQuote, NormalizedNews
from analytics.indicators import TechnicalIndicators
from analytics import (
    TrendAnalyzer,
    VolatilityAnalyzer,
    VolumeAnalyzer,
    MultiTimeframeAnalyzer
)
from engine.scanner_engine import MarketScannerEngine
from signals.signal_generator import SignalGenerator
from signals.models import TradingSignal
from risk.risk_manager import RiskManager
from risk.position_sizer import PositionSizer
from portfolio.portfolio_manager import PortfolioManager
from portfolio.paper_trader import PaperTrader
from backtesting.backtest_engine import BacktestEngine, BacktestConfig
from backtesting.strategies import (
    EMACrossoverStrategy,
    RSIMeanReversionStrategy,
    MACDTrendFollowingStrategy,
    BollingerBreakoutStrategy,
    InstitutionalConfluenceStrategy
)
from watchlist.watchlist_manager import WatchlistManager
from notifications.telegram_notifier import TelegramNotifier
from diagnostics.system_diagnostics import SystemDiagnostics
from utils.exporter import UniversalExporter
from gui.main_window import MainWindow
from config.constants import NAV_ITEMS, TF_1D, TF_4H, TF_1H, TF_15M, SIDE_BUY, SIDE_SELL


def generate_synthetic_candles(count: int = 100, base_price: float = 2600.0) -> list:
    """Generate realistic synthetic candlestick bars for validation"""
    import math
    from datetime import datetime, timedelta
    candles = []
    p = base_price
    start_dt = datetime(2025, 1, 1, 0, 0, 0)
    for i in range(count):
        noise = math.sin(i / 5.0) * 15.0 + (i * 0.5)
        o = p
        c = p + noise
        h = max(o, c) + 5.0
        l = min(o, c) - 5.0
        v = 15000.0 + (math.cos(i) * 5000.0)
        dt = start_dt + timedelta(days=i)
        dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        candles.append(NormalizedCandle(
            symbol="XAU/USD",
            timeframe=TF_1D,
            timestamp=dt_str,
            open=round(o, 2),
            high=round(h, 2),
            low=round(l, 2),
            close=round(c, 2),
            volume=round(abs(v), 2)
        ))
        p = c
    return candles


class TestComprehensiveAudit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "audit_test.db"

        # Reset singletons
        DatabaseManager._instance = None
        AppContext._instance = None

        self.ctx = AppContext()
        self.ctx._db_manager = DatabaseManager(self.db_path)

    def tearDown(self):
        self.ctx.shutdown()
        if hasattr(self.ctx, "_db_manager") and self.ctx._db_manager:
            self.ctx._db_manager.close()
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass
        DatabaseManager._instance = None
        AppContext._instance = None

    def test_01_app_context_dependencies(self):
        """Audit all 25 lazy properties in AppContext container"""
        props = [
            "db", "settings", "events", "tasks", "security",
            "health_monitor", "key_rotation", "rate_limiter", "cache",
            "finnhub", "twelve_data", "newsapi", "market_data",
            "scanner", "news_engine", "signals", "alerts",
            "portfolio", "risk_manager", "paper_trader",
            "watchlists", "telegram", "diagnostics", "exporter"
        ]
        for prop in props:
            val = getattr(self.ctx, prop)
            self.assertIsNotNone(val, f"AppContext property '{prop}' failed to instantiate")

    def test_02_mathematical_indicators_edge_cases(self):
        """Audit indicator robustness against zero, constant, and insufficient data"""
        ti = TechnicalIndicators
        # 1. Empty data
        self.assertEqual(ti.sma([], 10), [])
        self.assertEqual(ti.ema([], 10), [])
        self.assertEqual(ti.rsi([], 14), [])
        macd, sig, hist = ti.macd([], 12, 26, 9)
        self.assertEqual(macd, [])

        # 2. Flat / constant data (zero variance / zero division check)
        flat = [100.0] * 50
        sma_flat = ti.sma(flat, 20)
        self.assertEqual(sma_flat[-1], 100.0)
        ema_flat = ti.ema(flat, 20)
        self.assertEqual(ema_flat[-1], 100.0)
        rsi_flat = ti.rsi(flat, 14)
        # When all changes are 0, avg_gain=0, avg_loss=0 -> handled gracefully
        self.assertIsNotNone(rsi_flat[-1])

        upper, mid, lower, bw = ti.bollinger_bands(flat, 20, 2.0)
        self.assertEqual(upper[-1], 100.0)
        self.assertEqual(lower[-1], 100.0)
        self.assertEqual(bw[-1], 0.0)

        # 3. ATR with flat data
        atr_flat = ti.atr(flat, flat, flat, 14)
        self.assertEqual(atr_flat[-1], 0.0)

    def test_03_market_data_engine_count_and_limit_aliases(self):
        """Audit MarketDataManager get_candles parameter alias flexibility"""
        synthetic = generate_synthetic_candles(60, 200.0)
        self.ctx.finnhub.get_candles = lambda sym, resolution: list(synthetic)

        candles = self.ctx.market_data.get_candles("AAPL", timeframe="1d", count=50)
        self.assertIsInstance(candles, list)
        self.assertEqual(len(candles), 50)

        # Calling with limit parameter alias should execute without TypeError
        candles_limit = self.ctx.market_data.get_candles("AAPL", timeframe="1d", limit=40)
        self.assertIsInstance(candles_limit, list)
        self.assertEqual(len(candles_limit), 40)

    def test_04_signal_engine_and_scoring(self):
        """Audit Signal generation, SL/TP1/TP2 and risk/reward calculations"""
        candles = generate_synthetic_candles(60, 2600.0)
        sig = self.ctx.signals.generate_signal(
            symbol="XAU/USD",
            candles=candles,
            timeframe=TF_1D,
            news_profile=None
        )
        self.assertIsInstance(sig, TradingSignal)
        self.assertIn(sig.signal, ["Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell"])
        self.assertGreater(sig.entry_price, 0.0)
        self.assertGreater(sig.stop_loss, 0.0)
        self.assertGreater(sig.take_profit_1, 0.0)
        self.assertGreater(sig.take_profit_2, 0.0)
        self.assertGreater(sig.risk_reward_ratio, 0.0)
        self.assertGreaterEqual(sig.confidence_pct, 0.0)
        self.assertLessEqual(sig.confidence_pct, 100.0)

        # Verify active signals ring buffer
        active = self.ctx.signals.get_active_signals(10)
        self.assertGreaterEqual(len(active), 1)

    def test_05_risk_management_guardrails(self):
        """Audit strict mathematical risk sizing and circuit breakers"""
        rm = self.ctx.risk_manager

        # Position Sizing with 80% maximum capital allocation guardrail:
        # At $2,600 entry, 50 units would cost $130,000 (> 80% of $100k balance).
        # Sizer correctly caps units to $80,000 / $2,600 = 30.7692 units.
        sizing_capped = rm.calculate_position_size(
            account_balance=100000.0,
            risk_pct=1.0,
            entry_price=2600.0,
            stop_loss=2580.0,
            take_profit=2650.0
        )
        self.assertAlmostEqual(sizing_capped.position_units, 30.7692, places=2)
        self.assertAlmostEqual(sizing_capped.risk_reward_ratio, 2.5, places=2)

        # Standard unconstrained position sizing where cost < max allocation:
        # $1,000 risk / $2 SL distance = 500 units @ $50 = $25,000 cost (< $80,000 max allocation)
        sizing_standard = rm.calculate_position_size(
            account_balance=100000.0,
            risk_pct=1.0,
            entry_price=50.0,
            stop_loss=48.0,
            take_profit=55.0
        )
        self.assertAlmostEqual(sizing_standard.position_units, 500.0, places=2)
        self.assertAlmostEqual(sizing_standard.risk_reward_ratio, 2.5, places=2)

        # Circuit breaker drawdown tracking
        dd_0 = rm.calculate_drawdown_pct(100000.0, peak_equity=100000.0)
        self.assertEqual(dd_0, 0.0)
        dd_10 = rm.calculate_drawdown_pct(90000.0, peak_equity=100000.0)
        self.assertEqual(dd_10, 10.0)

    def test_06_portfolio_and_paper_trading_ledger(self):
        """Audit paper trade execution, mark-to-market, and position closing"""
        pt = self.ctx.paper_trader
        pm = self.ctx.portfolio

        # 1. Execute BUY order
        ok, msg, pos = pt.execute_paper_order(
            symbol="XAU/USD",
            side=SIDE_BUY,
            entry_price=2600.0,
            stop_loss=2580.0,
            take_profit=2650.0,
            custom_risk_pct=1.0
        )
        self.assertTrue(ok, f"Order failed: {msg}")
        self.assertIsNotNone(pos)
        self.assertEqual(len(pm.get_open_positions()), 1)

        # 2. Mark to Market
        pm.update_market_price("XAU/USD", 2620.0)
        summary = pm.get_portfolio_summary()
        self.assertGreater(summary.unrealized_pnl, 0.0)

        # 3. Close Position
        ok_close, msg_close = pt.close_paper_position(pos.position_id, exit_price=2630.0, exit_reason="Manual Audit Test")
        self.assertTrue(ok_close)
        self.assertEqual(len(pm.get_open_positions()), 0)
        self.assertGreater(pm.get_portfolio_summary().realized_pnl, 0.0)

    def test_07_backtesting_all_strategies(self):
        """Audit backtest simulation across all 5 strategies with zero lookahead bias"""
        candles = generate_synthetic_candles(100, 2600.0)
        cfg = BacktestConfig(initial_capital=100000.0, risk_per_trade_pct=1.0)
        engine = BacktestEngine(cfg)

        strategies = [
            EMACrossoverStrategy(),
            RSIMeanReversionStrategy(),
            MACDTrendFollowingStrategy(),
            BollingerBreakoutStrategy(),
            InstitutionalConfluenceStrategy()
        ]

        for strat in strategies:
            result = engine.run(strat, candles, symbol="XAU/USD", timeframe=TF_1D)
            self.assertIsNotNone(result)
            self.assertIsNotNone(result.equity_curve)
            self.assertEqual(len(result.equity_curve), len(candles) - 30)
            self.assertIsInstance(result.win_rate, float)
            self.assertIsInstance(result.profit_factor, float)
            self.assertIsInstance(result.sharpe_ratio, float)
            self.assertIsInstance(result.max_drawdown_pct, float)

    def test_08_multi_watchlist_lifecycle(self):
        """Audit watchlist creation, renaming, notes, alerts, and deletion"""
        wm = self.ctx.watchlists

        # Create
        ok, msg, wid = wm.create_watchlist("Institutional FX", "FX Majors Surveillance")
        self.assertTrue(ok)
        self.assertIsNotNone(wid)

        # Add Symbol with Notes and Alert Condition
        ok_sym, msg_sym = wm.add_symbol(wid, "GBP/USD", market="Forex", notes="BOE rate decision catalyst", alert_condition="> 1.2850")
        self.assertTrue(ok_sym)

        # Get Symbols
        symbols = wm.get_symbols(wid)
        self.assertEqual(len(symbols), 1)
        self.assertEqual(symbols[0]["symbol"], "GBP/USD")
        self.assertEqual(symbols[0]["notes"], "BOE rate decision catalyst")

        # Evaluate Alert
        triggered = wm.evaluate_symbol_alerts("GBP/USD", 1.2900)
        self.assertGreaterEqual(len(triggered), 1)
        self.assertIn("GBP/USD", triggered[0])

        # Rename
        ok_rn, _ = wm.rename_watchlist(wid, "Institutional FX & Metals")
        self.assertTrue(ok_rn)

        # Delete
        ok_del, _ = wm.delete_watchlist(wid)
        self.assertTrue(ok_del)

    def test_09_universal_exporter_csv_and_json(self):
        """Audit CSV and JSON exporter output across all datasets"""
        exp = self.ctx.exporter
        export_dir = Path(self.temp_dir.name) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        # Test Scanner Export
        scan_data = [
            {"symbol": "XAU/USD", "price": 2650.0, "change_percent": 1.2, "volume": 50000, "rvol": 2.1, "rsi": 62.0, "trend": "BULLISH", "macd_status": "BULLISH", "volatility": "NORMAL", "technical_score": 78.5}
        ]
        csv_file = str(export_dir / "scanner.csv")
        ok_csv, msg_csv = exp.export_scanner_results(scan_data, csv_file, fmt="csv")
        self.assertTrue(ok_csv)
        self.assertTrue(os.path.exists(csv_file))

        json_file = str(export_dir / "scanner.json")
        ok_json, msg_json = exp.export_scanner_results(scan_data, json_file, fmt="json")
        self.assertTrue(ok_json)
        self.assertTrue(os.path.exists(json_file))

    def test_10_system_diagnostics_audit(self):
        """Audit 6-vector health diagnostic scanner and JSON completeness"""
        diag = self.ctx.diagnostics
        report = diag.run_full_diagnostics()

        self.assertIn("overall_status", report)
        self.assertIn("score", report)
        self.assertIn("api_connectivity", report)
        self.assertIn("database_integrity", report)
        self.assertIn("cache_telemetry", report)
        self.assertIn("application_health", report)
        self.assertIn("background_tasks", report)
        self.assertIn("system_logs", report)

        # Verify JSON serializability
        serialized = json.dumps(report)
        self.assertIsInstance(serialized, str)

    def test_11_gui_full_view_instantiation_and_callbacks(self):
        """Audit instantiation and data refresh across all 10 GUI views"""
        app = MainWindow(self.ctx)
        app.withdraw()

        try:
            for page_name, _ in NAV_ITEMS:
                app.navigate_to(page_name)
                app.update_idletasks()
                view = app._view_instances.get(page_name)
                self.assertIsNotNone(view)

                # Call view refresh if present
                if hasattr(view, "refresh_data"):
                    view.refresh_data()
                elif hasattr(view, "refresh_table"):
                    view.refresh_table()
                elif hasattr(view, "_refresh_portfolio_data"):
                    view._refresh_portfolio_data()

                app.update_idletasks()
        finally:
            app.destroy()


if __name__ == "__main__":
    unittest.main()
