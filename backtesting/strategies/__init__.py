"""
M4DI~UciH4 Trading Intelligence System - Strategies Framework
"""
from backtesting.strategies.base_strategy import BaseStrategy
from backtesting.strategies.ema_crossover import EMACrossoverStrategy
from backtesting.strategies.rsi_mean_reversion import RSIMeanReversionStrategy
from backtesting.strategies.macd_trend import MACDTrendFollowingStrategy
from backtesting.strategies.bollinger_breakout import BollingerBreakoutStrategy
from backtesting.strategies.institutional_confluence import InstitutionalConfluenceStrategy

AVAILABLE_STRATEGIES = {
    "EMA Crossover": EMACrossoverStrategy,
    "RSI Mean Reversion": RSIMeanReversionStrategy,
    "MACD Trend Following": MACDTrendFollowingStrategy,
    "Bollinger Breakout": BollingerBreakoutStrategy,
    "Institutional Confluence": InstitutionalConfluenceStrategy,
}

__all__ = [
    "BaseStrategy",
    "EMACrossoverStrategy",
    "RSIMeanReversionStrategy",
    "MACDTrendFollowingStrategy",
    "BollingerBreakoutStrategy",
    "InstitutionalConfluenceStrategy",
    "AVAILABLE_STRATEGIES",
]
