"""
M4DI~UciH4 Trading Intelligence System
Application Constants & Global Definitions
"""
import os
from pathlib import Path

# Application Branding
APP_NAME = "M4DI~UciH4 Trading Intelligence"
APP_SUBTITLE = "Institutional Trading Intelligence System"
APP_VERSION = "v6.0.0 Enterprise"
APP_AUTHOR = "M4DI~UciH4 Institutional Algos"
APP_COPYRIGHT = "© 2026 M4DI~UciH4. All Rights Reserved."

# File Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "m4di_ucih4_trading.db"
LOG_FILE_PATH = LOGS_DIR / "m4di_trading.log"

# Supported API Providers
PROVIDER_FINNHUB = "Finnhub"
PROVIDER_TWELVE_DATA = "Twelve Data"
PROVIDER_NEWS_API = "NewsAPI.org"

API_PROVIDERS = [
    PROVIDER_FINNHUB,
    PROVIDER_TWELVE_DATA,
    PROVIDER_NEWS_API,
]

PROVIDER_INFO = {
    PROVIDER_FINNHUB: {
        "name": "Finnhub Stock & Forex API",
        "description": "Real-time institutional stock, forex, and market fundamental data.",
        "website": "https://finnhub.io",
        "status": "Operational (Active)"
    },
    PROVIDER_TWELVE_DATA: {
        "name": "Twelve Data Financial API",
        "description": "High-speed multi-asset market data for Gold, Indices, FX, and Crypto.",
        "website": "https://twelvedata.com",
        "status": "Operational (Active)"
    },
    PROVIDER_NEWS_API: {
        "name": "NewsAPI Intelligence Feed",
        "description": "Global economic, financial breaking news, and central bank releases.",
        "website": "https://newsapi.org",
        "status": "Operational (Active)"
    }
}

# API Key Rotation Strategies
ROTATION_STRATEGY_PRIORITY = "priority"
ROTATION_STRATEGY_ROUND_ROBIN = "round_robin"
ROTATION_STRATEGY_LEAST_USED = "least_used"
ROTATION_STRATEGY_FAILOVER = "failover"

ROTATION_STRATEGIES = [
    ROTATION_STRATEGY_PRIORITY,
    ROTATION_STRATEGY_ROUND_ROBIN,
    ROTATION_STRATEGY_LEAST_USED,
    ROTATION_STRATEGY_FAILOVER,
]

ROTATION_STRATEGY_LABELS = {
    ROTATION_STRATEGY_PRIORITY: "Priority-Based (Highest Priority First)",
    ROTATION_STRATEGY_ROUND_ROBIN: "Round-Robin (Sequential Cycling)",
    ROTATION_STRATEGY_LEAST_USED: "Least-Used (Lowest Request Count)",
    ROTATION_STRATEGY_FAILOVER: "Failover (Backup upon Failure)",
}

# Provider Rate Limits (Free Tier Defaults)
DEFAULT_PROVIDER_LIMITS = {
    PROVIDER_FINNHUB: {
        "rpm": 60,                # 60 calls per minute
        "min_interval_sec": 1.0,  # Min interval between consecutive calls
        "daily_limit": None,
        "base_url": "https://finnhub.io/api/v1"
    },
    PROVIDER_TWELVE_DATA: {
        "rpm": 8,                 # 8 calls per minute on standard free plan
        "min_interval_sec": 7.5,  # 8 req/min throttle
        "daily_limit": 800,
        "base_url": "https://api.twelvedata.com"
    },
    PROVIDER_NEWS_API: {
        "rpm": 10,                # Safe pacing
        "min_interval_sec": 2.0,
        "daily_limit": 100,       # 100 requests / 24 hours on developer tier
        "base_url": "https://newsapi.org/v2"
    }
}

# Cache TTL Configuration (in seconds)
CACHE_TTL_QUOTE = 30        # Live quotes cache for 30s
CACHE_TTL_CANDLE = 300      # Historical candles cache for 5 min
CACHE_TTL_COMPANY = 3600    # Company profiles cache for 1 hour
CACHE_TTL_NEWS = 600        # News headlines cache for 10 min
CACHE_TTL_SEARCH = 1800     # Symbol search cache for 30 min

# Provider Health Status Enum
HEALTH_CONNECTED = "CONNECTED"
HEALTH_DISCONNECTED = "DISCONNECTED"
HEALTH_RATE_LIMITED = "RATE_LIMITED"
HEALTH_INVALID_KEY = "INVALID_KEY"
HEALTH_ERROR = "ERROR"

# Markets & Asset Classes
MARKET_FOREX = "Forex (Major & Crosses)"
MARKET_GOLD = "Commodities (XAUUSD / Gold & Metals)"
MARKET_INDICES = "Indices (US30 / NAS100 / SPX500)"
MARKET_CRYPTO = "Crypto (BTC / ETH / SOL)"
MARKET_STOCKS = "US Equities & Tech"

SUPPORTED_MARKETS = [
    MARKET_GOLD,
    MARKET_FOREX,
    MARKET_INDICES,
    MARKET_CRYPTO,
    MARKET_STOCKS
]

# Timeframes
TF_1M = "1m"
TF_5M = "5m"
TF_15M = "15m"
TF_30M = "30m"
TF_1H = "1h"
TF_4H = "4h"
TF_1D = "1d"
TF_1W = "1w"
TF_1MO = "1M"

TIMEFRAMES = [TF_1M, TF_5M, TF_15M, TF_30M, TF_1H, TF_4H, TF_1D, TF_1W, TF_1MO]

# Timeframe in seconds for mathematical resampling
TIMEFRAME_SECONDS = {
    TF_1M: 60,
    TF_5M: 300,
    TF_15M: 900,
    TF_30M: 1800,
    TF_1H: 3600,
    TF_4H: 14400,
    TF_1D: 86400,
    TF_1W: 604800,
    TF_1MO: 2592000,
}

# Trend Classifications
TREND_STRONG_BULLISH = "STRONG_BULLISH"
TREND_BULLISH = "BULLISH"
TREND_NEUTRAL = "NEUTRAL"
TREND_BEARISH = "BEARISH"
TREND_STRONG_BEARISH = "STRONG_BEARISH"

# Volatility Classifications
VOLATILITY_LOW = "LOW"
VOLATILITY_NORMAL = "NORMAL"
VOLATILITY_HIGH = "HIGH"
VOLATILITY_EXTREME = "EXTREME"

# News Categories (11 Required Categories)
NEWS_CAT_EARNINGS = "Earnings"
NEWS_CAT_ECONOMIC = "Economic data"
NEWS_CAT_INTEREST_RATES = "Interest rates"
NEWS_CAT_INFLATION = "Inflation"
NEWS_CAT_COMPANY_ANNOUNCEMENTS = "Company announcements"
NEWS_CAT_MA = "Mergers and acquisitions"
NEWS_CAT_REGULATION = "Regulation"
NEWS_CAT_GEOPOLITICAL = "Geopolitical events"
NEWS_CAT_ANALYST_RATINGS = "Analyst upgrades/downgrades"
NEWS_CAT_PRODUCT_LAUNCHES = "Product launches"
NEWS_CAT_MARKET_SENTIMENT = "Market sentiment"

NEWS_CATEGORIES = [
    NEWS_CAT_EARNINGS,
    NEWS_CAT_ECONOMIC,
    NEWS_CAT_INTEREST_RATES,
    NEWS_CAT_INFLATION,
    NEWS_CAT_COMPANY_ANNOUNCEMENTS,
    NEWS_CAT_MA,
    NEWS_CAT_REGULATION,
    NEWS_CAT_GEOPOLITICAL,
    NEWS_CAT_ANALYST_RATINGS,
    NEWS_CAT_PRODUCT_LAUNCHES,
    NEWS_CAT_MARKET_SENTIMENT,
]

# Sentiment Classifications
SENTIMENT_POSITIVE = "POSITIVE"
SENTIMENT_NEGATIVE = "NEGATIVE"
SENTIMENT_NEUTRAL = "NEUTRAL"

SENTIMENTS = [SENTIMENT_POSITIVE, SENTIMENT_NEUTRAL, SENTIMENT_NEGATIVE]

# News Impact Classifications
IMPACT_LOW = "LOW"
IMPACT_MEDIUM = "MEDIUM"
IMPACT_HIGH = "HIGH"
IMPACT_CRITICAL = "CRITICAL"

IMPACT_LEVELS = [IMPACT_LOW, IMPACT_MEDIUM, IMPACT_HIGH, IMPACT_CRITICAL]

# Trading Signal Classifications
SIGNAL_STRONG_BUY = "Strong Buy"
SIGNAL_BUY = "Buy"
SIGNAL_NEUTRAL = "Neutral"
SIGNAL_SELL = "Sell"
SIGNAL_STRONG_SELL = "Strong Sell"

SIGNAL_TYPES = [
    SIGNAL_STRONG_BUY,
    SIGNAL_BUY,
    SIGNAL_NEUTRAL,
    SIGNAL_SELL,
    SIGNAL_STRONG_SELL,
]

# Signal Alert Types
ALERT_STRONG_BUY = "Strong Buy"
ALERT_STRONG_SELL = "Strong Sell"
ALERT_TREND_BREAKOUT = "Trend Breakout"
ALERT_RSI_EXTREME = "RSI Extreme"
ALERT_MACD_CROSSOVER = "MACD Crossover"
ALERT_VOLUME_BREAKOUT = "Volume Breakout"
ALERT_HIGH_IMPACT_NEWS = "High Impact News"

ALERT_TYPES = [
    ALERT_STRONG_BUY,
    ALERT_STRONG_SELL,
    ALERT_TREND_BREAKOUT,
    ALERT_RSI_EXTREME,
    ALERT_MACD_CROSSOVER,
    ALERT_VOLUME_BREAKOUT,
    ALERT_HIGH_IMPACT_NEWS,
]

# Order Sides & Types
SIDE_BUY = "BUY"
SIDE_SELL = "SELL"
ORDER_SIDES = [SIDE_BUY, SIDE_SELL]

POSITION_OPEN = "OPEN"
POSITION_CLOSED = "CLOSED"

TRADE_ENTRY = "ENTRY"
TRADE_EXIT = "EXIT"
TRADE_SL_HIT = "SL_HIT"
TRADE_TP_HIT = "TP_HIT"

# Default Risk Management Thresholds
DEFAULT_INITIAL_CAPITAL = 100000.0
DEFAULT_RISK_PER_TRADE_PCT = 1.0           # 1.0% equity risk per trade
DEFAULT_MAX_PORTFOLIO_EXPOSURE_PCT = 80.0  # Max 80% total capital allocated
DEFAULT_MAX_DRAWDOWN_LIMIT_PCT = 15.0      # 15% Max DD circuit breaker
DEFAULT_DAILY_LOSS_LIMIT_PCT = 3.0         # 3% Daily loss limit
DEFAULT_MAX_OPEN_POSITIONS = 5             # Max 5 simultaneous open positions

# Default Backtesting Assumptions
DEFAULT_COMMISSION_PCT = 0.05              # 0.05% fee / commission per trade
DEFAULT_SLIPPAGE_PCT = 0.02                # 0.02% simulated slippage

# UI Themes
THEMES = [
    "Dark Charcoal (Default)",
    "Obsidian Gold",
    "Emerald Obsidian",
    "Cyberpunk Cyan"
]

# Logging Levels
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Navigation Pages
PAGE_DASHBOARD = "Dashboard"
PAGE_SCANNER = "Market Scanner"
PAGE_CHARTS = "Charts"
PAGE_SIGNALS = "Trading Signals"
PAGE_NEWS = "News Intelligence"
PAGE_PORTFOLIO = "Portfolio"
PAGE_BACKTESTING = "Backtesting"
PAGE_API = "API Management"
PAGE_SETTINGS = "Settings"
PAGE_LOGS = "Logs"

NAV_ITEMS = [
    (PAGE_DASHBOARD, "📊"),
    (PAGE_SCANNER, "🔍"),
    (PAGE_CHARTS, "📈"),
    (PAGE_SIGNALS, "🎯"),
    (PAGE_NEWS, "📰"),
    (PAGE_PORTFOLIO, "💼"),
    (PAGE_BACKTESTING, "🧪"),
    (PAGE_API, "🔑"),
    (PAGE_SETTINGS, "⚙️"),
    (PAGE_LOGS, "📝"),
]

# Phase 6: Telegram Notifications Settings Keys
SETTING_TELEGRAM_ENABLED = "telegram_enabled"
SETTING_TELEGRAM_BOT_TOKEN = "telegram_bot_token"
SETTING_TELEGRAM_CHAT_ID = "telegram_chat_id"
SETTING_TELEGRAM_NOTIFY_SIGNALS = "telegram_notify_signals"
SETTING_TELEGRAM_NOTIFY_NEWS = "telegram_notify_news"
SETTING_TELEGRAM_NOTIFY_RISK = "telegram_notify_risk"
SETTING_TELEGRAM_NOTIFY_PORTFOLIO = "telegram_notify_portfolio"

# Phase 6: Export Formats
EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_JSON = "json"

# Phase 6: Default Settings
DEFAULT_SETTINGS = {
    "theme": "Dark Charcoal (Default)",
    "refresh_interval_sec": "30",
    "default_watchlist": "Gold & Metals",
    "default_market": "Commodities (Gold/Silver)",
    "default_symbol": "XAU/USD",
    "default_timeframe": "1h",
    "chart_show_volume": "true",
    "chart_show_grid": "true",
    "risk_per_trade_pct": "1.0",
    "max_drawdown_limit_pct": "15.0",
    "daily_loss_limit_pct": "3.0",
    "max_open_positions": "5",
    "default_commission_pct": "0.05",
    "default_slippage_pct": "0.02",
    "telegram_enabled": "false",
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "telegram_notify_signals": "true",
    "telegram_notify_news": "true",
    "telegram_notify_risk": "true",
    "telegram_notify_portfolio": "true"
}
