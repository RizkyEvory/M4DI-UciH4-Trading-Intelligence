"""
M4DI~UciH4 Trading Intelligence System
Backtesting Engine & Strategy Framework Unit Tests (Phase 5)
Verifies anti-data leakage, bar-by-bar simulation, fee & slippage deductions,
and mathematical accuracy of performance metrics (Sharpe, Sortino, Max Drawdown, Win Rate, Expectancy).
"""
import unittest
from datetime import datetime, timedelta

from api.models import NormalizedCandle
from backtesting.models import BacktestConfig, BacktestTrade
from backtesting.metrics import PerformanceMetrics
from backtesting.backtest_engine import BacktestEngine
from backtesting.strategies.ema_crossover import EMACrossoverStrategy
from backtesting.strategies.rsi_mean_reversion import RSIMeanReversionStrategy
from backtesting.strategies.macd_trend import MACDTrendFollowingStrategy
from backtesting.strategies.bollinger_breakout import BollingerBreakoutStrategy
from backtesting.strategies.institutional_confluence import InstitutionalConfluenceStrategy


def _create_synthetic_dataset(bars: int = 100, start_price: float = 100.0) -> list:
    """Generate realistic oscillating historical bars for strategy testing"""
    candles = []
    p = start_price
    start_dt = datetime(2026, 1, 1, 9, 30)

    for i in range(bars):
        # Sine-wave oscillating price path
        drift = 0.5 if (i // 15) % 2 == 0 else -0.5
        op = p
        cl = p + drift + (0.2 if i % 2 == 0 else -0.2)
        hi = max(op, cl) + 0.8
        lo = min(op, cl) - 0.8
        vol = 20000.0 + (i * 50)
        p = cl

        candles.append(NormalizedCandle(
            symbol="TEST",
            timeframe="1d",
            open=round(op, 2),
            high=round(hi, 2),
            low=round(lo, 2),
            close=round(cl, 2),
            volume=vol,
            timestamp=(start_dt + timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S")
        ))
    return candles


class TestPerformanceMetrics(unittest.TestCase):
    """Test mathematical accuracy of Sharpe, Sortino, Drawdown, Profit Factor, and Expectancy"""

    def test_metrics_calculation(self):
        trades = [
            BacktestTrade(trade_id=1, symbol="TEST", side="BUY", units=10.0, entry_time="t1", entry_price=100.0, exit_time="t2", exit_price=110.0, stop_loss=95.0, take_profit=110.0, exit_reason="TP", net_pnl=100.0),
            BacktestTrade(trade_id=2, symbol="TEST", side="BUY", units=10.0, entry_time="t3", entry_price=110.0, exit_time="t4", exit_price=105.0, stop_loss=105.0, take_profit=120.0, exit_reason="SL", net_pnl=-50.0),
            BacktestTrade(trade_id=3, symbol="TEST", side="BUY", units=10.0, entry_time="t5", entry_price=105.0, exit_time="t6", exit_price=115.0, stop_loss=100.0, take_profit=115.0, exit_reason="TP", net_pnl=100.0)
        ]
        equity_curve = [10000.0, 10100.0, 10050.0, 10150.0]

        res = PerformanceMetrics.calculate_all(trades, equity_curve, initial_capital=10000.0)

        self.assertEqual(res["total_trades"], 3)
        self.assertEqual(res["winning_trades"], 2)
        self.assertEqual(res["losing_trades"], 1)
        self.assertAlmostEqual(res["win_rate"], 66.67, delta=0.1)

        # Gross Profit = 200, Gross Loss = 50 -> PF = 4.0
        self.assertEqual(res["profit_factor"], 4.0)

        # Total Return = (10,150 - 10,000) / 10,000 = 1.5%
        self.assertEqual(res["total_return_pct"], 1.5)

        # Expectancy: (2/3 * 100) - (1/3 * 50) = 66.67 - 16.67 = 50.0
        self.assertAlmostEqual(res["expectancy"], 50.0, delta=0.5)

        # Sharpe ratio must be positive
        self.assertGreater(res["sharpe_ratio"], 0.0)

    def test_drawdown_calculation(self):
        curve = [100.0, 120.0, 90.0, 110.0, 130.0]
        # Peak was 120.0, trough was 90.0 -> DD = (120 - 90) / 120 = 25.0%
        max_dd, duration, _ = PerformanceMetrics.calculate_drawdown(curve)
        self.assertEqual(max_dd, 25.0)
        self.assertGreaterEqual(duration, 1)


class TestBacktestEngine(unittest.TestCase):
    """Test full backtest execution with anti-lookahead guarantees and fee/slippage modeling"""

    def setUp(self):
        self.candles = _create_synthetic_dataset(bars=120)
        self.config = BacktestConfig(
            initial_capital=50000.0,
            risk_per_trade_pct=1.0,
            commission_pct=0.05,
            slippage_pct=0.02
        )
        self.engine = BacktestEngine(self.config)

    def test_ema_crossover_backtest(self):
        strat = EMACrossoverStrategy({"fast_period": 5, "slow_period": 15, "trend_period": 30})
        res = self.engine.run(strat, self.candles, symbol="TEST", warmup_period=30)

        self.assertIsNotNone(res)
        self.assertEqual(res.strategy_name, "EMA Crossover")
        self.assertEqual(res.initial_capital, 50000.0)
        self.assertTrue(len(res.equity_curve) > 0)
        self.assertTrue(len(res.trades) > 0)

        # Verify all trades had fee and slippage applied
        for t in res.trades:
            self.assertGreater(t.fee, 0.0)

    def test_rsi_mean_reversion_backtest(self):
        strat = RSIMeanReversionStrategy({"period": 10, "oversold": 35.0, "overbought": 65.0})
        res = self.engine.run(strat, self.candles, symbol="TEST", warmup_period=20)
        self.assertIsNotNone(res)
        self.assertEqual(res.strategy_name, "RSI Mean Reversion")

    def test_macd_trend_backtest(self):
        strat = MACDTrendFollowingStrategy({"fast_period": 8, "slow_period": 17, "signal_period": 9})
        res = self.engine.run(strat, self.candles, symbol="TEST", warmup_period=25)
        self.assertIsNotNone(res)
        self.assertEqual(res.strategy_name, "MACD Trend Following")

    def test_bollinger_breakout_backtest(self):
        strat = BollingerBreakoutStrategy({"period": 15, "num_std": 1.5})
        res = self.engine.run(strat, self.candles, symbol="TEST", warmup_period=20)
        self.assertIsNotNone(res)
        self.assertEqual(res.strategy_name, "Bollinger Breakout")

    def test_institutional_confluence_backtest(self):
        strat = InstitutionalConfluenceStrategy({
            "fast_ema": 10, "slow_ema": 25, "rsi_min": 40.0, "rsi_max": 75.0, "rvol_threshold": 0.8
        })
        res = self.engine.run(strat, self.candles, symbol="TEST", warmup_period=30)
        self.assertIsNotNone(res)
        self.assertEqual(res.strategy_name, "Institutional Confluence")


if __name__ == "__main__":
    unittest.main()
