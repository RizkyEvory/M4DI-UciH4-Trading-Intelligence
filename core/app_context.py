"""
M4DI~UciH4 Trading Intelligence System
Application Context (Dependency Container)
"""
from typing import Optional

from database.db_manager import DatabaseManager
from config.settings import SettingsManager
from core.event_bus import EventBus
from core.task_manager import TaskManager


class AppContext:
    """Central Dependency Container for Clean Lifecycle Management"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppContext, cls).__new__(cls)
            cls._instance._db_manager: Optional[DatabaseManager] = None
            cls._instance._settings_manager: Optional[SettingsManager] = None
            cls._instance._task_manager: Optional[TaskManager] = None
            cls._instance._event_bus: Optional[EventBus] = None
            cls._instance._api_key_manager = None
            cls._instance._cache = None
            cls._instance._rate_limiter = None
            cls._instance._key_rotation = None
            cls._instance._health_monitor = None
            cls._instance._finnhub = None
            cls._instance._twelve_data = None
            cls._instance._newsapi = None
            cls._instance._market_data = None
            cls._instance._scanner = None
            cls._instance._news_engine = None
            cls._instance._signals = None
            cls._instance._alerts = None
            cls._instance._risk_manager = None
            cls._instance._portfolio_manager = None
            cls._instance._paper_trader = None
            cls._instance._backtest_engine = None
            cls._instance._watchlist_manager = None
            cls._instance._telegram_notifier = None
            cls._instance._diagnostics = None
        return cls._instance

    @property
    def db(self) -> DatabaseManager:
        if self._db_manager is None:
            self._db_manager = DatabaseManager()
        return self._db_manager

    @property
    def settings(self) -> SettingsManager:
        if self._settings_manager is None:
            self._settings_manager = SettingsManager(self.db)
        return self._settings_manager

    @property
    def tasks(self) -> TaskManager:
        if self._task_manager is None:
            self._task_manager = TaskManager()
        return self._task_manager

    @property
    def events(self) -> EventBus:
        if self._event_bus is None:
            self._event_bus = EventBus()
        return self._event_bus

    @property
    def api_keys(self):
        if self._api_key_manager is None:
            from api.key_manager import ApiKeyManager
            self._api_key_manager = ApiKeyManager(self.db, self.events)
        return self._api_key_manager

    @property
    def cache(self):
        if self._cache is None:
            from api.cache import ResponseCache
            self._cache = ResponseCache()
        return self._cache

    @property
    def rate_limiter(self):
        if self._rate_limiter is None:
            from api.rate_limiter import RateLimitManager
            self._rate_limiter = RateLimitManager()
        return self._rate_limiter

    @property
    def key_rotation(self):
        if self._key_rotation is None:
            from api.key_rotation import KeyRotationManager
            self._key_rotation = KeyRotationManager(self.db, self.events)
        return self._key_rotation

    @property
    def health_monitor(self):
        if self._health_monitor is None:
            from api.health_monitor import ProviderHealthMonitor
            self._health_monitor = ProviderHealthMonitor(self.events, db=self.db)
        return self._health_monitor

    @property
    def security(self):
        from security.encryption import SecurityManager
        return SecurityManager

    @property
    def finnhub(self):
        if self._finnhub is None:
            from api.finnhub_client import FinnhubClient
            self._finnhub = FinnhubClient(
                rate_limiter=self.rate_limiter,
                key_rotation=self.key_rotation,
                health_monitor=self.health_monitor,
                cache=self.cache
            )
        return self._finnhub

    @property
    def twelve_data(self):
        if self._twelve_data is None:
            from api.twelve_data_client import TwelveDataClient
            self._twelve_data = TwelveDataClient(
                rate_limiter=self.rate_limiter,
                key_rotation=self.key_rotation,
                health_monitor=self.health_monitor,
                cache=self.cache
            )
        return self._twelve_data

    @property
    def newsapi(self):
        if self._newsapi is None:
            from api.newsapi_client import NewsApiClient
            self._newsapi = NewsApiClient(
                rate_limiter=self.rate_limiter,
                key_rotation=self.key_rotation,
                health_monitor=self.health_monitor,
                cache=self.cache
            )
        return self._newsapi

    @property
    def market_data(self):
        if self._market_data is None:
            from engine.market_data_engine import MarketDataManager
            self._market_data = MarketDataManager(self)
        return self._market_data

    @property
    def scanner(self):
        if self._scanner is None:
            from engine.scanner_engine import MarketScannerEngine
            self._scanner = MarketScannerEngine(self.market_data)
        return self._scanner

    @property
    def news_engine(self):
        if self._news_engine is None:
            from news.news_engine import NewsEngine
            self._news_engine = NewsEngine(
                finnhub_client=self.finnhub,
                newsapi_client=self.newsapi,
                cache=self.cache
            )
        return self._news_engine

    @property
    def signals(self):
        if self._signals is None:
            from signals.signal_generator import SignalGenerator
            self._signals = SignalGenerator()
        return self._signals

    @property
    def alerts(self):
        if self._alerts is None:
            from signals.alerts_engine import AlertsEngine
            self._alerts = AlertsEngine(event_bus=self.events)
        return self._alerts

    @property
    def risk_manager(self):
        if self._risk_manager is None:
            from risk.risk_manager import RiskManager
            self._risk_manager = RiskManager()
        return self._risk_manager

    @property
    def portfolio(self):
        if self._portfolio_manager is None:
            from portfolio.portfolio_manager import PortfolioManager
            self._portfolio_manager = PortfolioManager(self.db)
        return self._portfolio_manager

    @property
    def paper_trader(self):
        if self._paper_trader is None:
            from portfolio.paper_trader import PaperTrader
            self._paper_trader = PaperTrader(
                portfolio_manager=self.portfolio,
                risk_manager=self.risk_manager
            )
        return self._paper_trader

    @property
    def backtester(self):
        if self._backtest_engine is None:
            from backtesting.backtest_engine import BacktestEngine
            self._backtest_engine = BacktestEngine()
        return self._backtest_engine

    @property
    def watchlists(self):
        if self._watchlist_manager is None:
            from watchlist.watchlist_manager import WatchlistManager
            self._watchlist_manager = WatchlistManager(self.db)
        return self._watchlist_manager

    @property
    def telegram(self):
        if self._telegram_notifier is None:
            from notifications.telegram_notifier import TelegramNotifier
            self._telegram_notifier = TelegramNotifier(self.settings)
        return self._telegram_notifier

    @property
    def diagnostics(self):
        if self._diagnostics is None:
            from diagnostics.system_diagnostics import SystemDiagnostics
            self._diagnostics = SystemDiagnostics(self)
        return self._diagnostics

    @property
    def exporter(self):
        from utils.exporter import UniversalExporter
        return UniversalExporter

    def shutdown(self):
        """Clean shutdown of background services"""
        if self._task_manager:
            self._task_manager.shutdown(wait=False)
        if self._db_manager:
            self._db_manager.close()
