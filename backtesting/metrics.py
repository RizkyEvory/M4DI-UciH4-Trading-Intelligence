"""
M4DI~UciH4 Trading Intelligence System
Quantitative Backtesting Performance Metrics Engine (Phase 5)
Calculates Total Return, CAGR, Win Rate, Profit Factor, Sharpe Ratio, Sortino Ratio,
Maximum Drawdown, Average Trade, and Mathematical Expectancy.
"""
import math
from typing import List, Tuple, Dict, Any
from backtesting.models import BacktestTrade


class PerformanceMetrics:
    """Institutional Strategy Performance Analytics"""

    @classmethod
    def calculate_all(
        cls,
        trades: List[BacktestTrade],
        equity_curve: List[float],
        initial_capital: float,
        annual_trading_days: int = 252,
        risk_free_rate_pct: float = 2.0
    ) -> Dict[str, Any]:
        """
        Computes all standard institutional hedge fund performance metrics.
        """
        total_trades = len(trades)
        final_equity = equity_curve[-1] if equity_curve else initial_capital

        if total_trades == 0:
            return {
                "total_trades": 0, "winning_trades": 0, "losing_trades": 0,
                "win_rate": 0.0, "profit_factor": 0.0, "total_return_pct": 0.0,
                "cagr": 0.0, "max_drawdown_pct": 0.0, "max_drawdown_duration": 0,
                "sharpe_ratio": 0.0, "sortino_ratio": 0.0, "avg_trade_pnl": 0.0,
                "avg_win": 0.0, "avg_loss": 0.0, "expectancy": 0.0
            }

        wins = [t for t in trades if t.net_pnl > 0]
        losses = [t for t in trades if t.net_pnl < 0]

        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = round((winning_trades / total_trades) * 100.0, 2)

        gross_profit = sum(t.net_pnl for t in wins)
        gross_loss = abs(sum(t.net_pnl for t in losses))

        # Profit Factor
        if gross_loss > 0:
            profit_factor = round(gross_profit / gross_loss, 2)
        else:
            profit_factor = round(gross_profit, 2) if gross_profit > 0 else 0.0

        # Total Return %
        total_return_pct = round(((final_equity - initial_capital) / initial_capital) * 100.0, 2)

        # CAGR estimation based on equity bars
        n_bars = len(equity_curve)
        years = max(n_bars / annual_trading_days, 0.05)  # min 0.05 years
        if final_equity > 0:
            cagr = round(((final_equity / initial_capital) ** (1.0 / years) - 1.0) * 100.0, 2)
        else:
            cagr = -100.0

        # Drawdown Analysis
        max_dd_pct, max_dd_duration, dd_curve = cls.calculate_drawdown(equity_curve)

        # Averages
        avg_trade_pnl = round(sum(t.net_pnl for t in trades) / total_trades, 2)
        avg_win = round(gross_profit / winning_trades, 2) if winning_trades > 0 else 0.0
        avg_loss = round(gross_loss / losing_trades, 2) if losing_trades > 0 else 0.0

        # Expectancy: (Win Rate * Avg Win) - (Loss Rate * Avg Loss)
        win_prob = winning_trades / total_trades
        loss_prob = losing_trades / total_trades
        expectancy = round((win_prob * avg_win) - (loss_prob * avg_loss), 2)

        # Periodic Returns for Sharpe & Sortino
        returns = []
        for i in range(1, len(equity_curve)):
            prev = equity_curve[i - 1]
            curr = equity_curve[i]
            if prev > 0:
                returns.append((curr - prev) / prev)

        sharpe_ratio, sortino_ratio = cls.calculate_ratios(
            returns, annual_trading_days, risk_free_rate_pct
        )

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_return_pct": total_return_pct,
            "cagr": cagr,
            "max_drawdown_pct": max_dd_pct,
            "max_drawdown_duration": max_dd_duration,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "avg_trade_pnl": avg_trade_pnl,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "expectancy": expectancy,
            "drawdown_curve": dd_curve
        }

    @staticmethod
    def calculate_drawdown(equity_curve: List[float]) -> Tuple[float, int, List[float]]:
        """
        Calculates Maximum Peak-to-Trough Drawdown %, Duration, and Drawdown Curve.
        """
        if not equity_curve:
            return 0.0, 0, []

        peak = equity_curve[0]
        max_dd = 0.0
        current_dd_duration = 0
        max_dd_duration = 0
        dd_curve = []

        for eq in equity_curve:
            if eq > peak:
                peak = eq
                current_dd_duration = 0
            else:
                current_dd_duration += 1
                if current_dd_duration > max_dd_duration:
                    max_dd_duration = current_dd_duration

            dd = ((peak - eq) / peak) * 100.0 if peak > 0 else 0.0
            dd_curve.append(round(dd, 2))
            if dd > max_dd:
                max_dd = dd

        return round(max_dd, 2), max_dd_duration, dd_curve

    @staticmethod
    def calculate_ratios(
        returns: List[float],
        annual_trading_days: int = 252,
        risk_free_rate_pct: float = 2.0
    ) -> Tuple[float, float]:
        """Calculates annualized Sharpe Ratio and Sortino Ratio"""
        if len(returns) < 2:
            return 0.0, 0.0

        rf_daily = (risk_free_rate_pct / 100.0) / annual_trading_days
        mean_ret = sum(returns) / len(returns)
        excess_mean = mean_ret - rf_daily

        # Variance & Std Dev
        variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = math.sqrt(variance)

        if std_dev > 0:
            sharpe = (excess_mean / std_dev) * math.sqrt(annual_trading_days)
            sharpe = round(sharpe, 2)
        else:
            sharpe = 0.0

        # Downside Deviation for Sortino
        negative_returns = [min(0.0, r - rf_daily) for r in returns]
        downside_variance = sum(nr ** 2 for nr in negative_returns) / (len(returns) - 1)
        downside_dev = math.sqrt(downside_variance)

        if downside_dev > 0:
            sortino = (excess_mean / downside_dev) * math.sqrt(annual_trading_days)
            sortino = round(sortino, 2)
        else:
            sortino = 0.0

        return sharpe, sortino
