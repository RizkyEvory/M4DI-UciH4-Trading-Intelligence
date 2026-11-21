"""
M4DI~UciH4 Trading Intelligence System
Main Application Shell Window with Header, Sidebar, and View Switcher
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Type

from config.constants import (
    APP_NAME, APP_VERSION,
    PAGE_DASHBOARD, PAGE_SCANNER, PAGE_CHARTS, PAGE_SIGNALS,
    PAGE_NEWS, PAGE_PORTFOLIO, PAGE_BACKTESTING, PAGE_API,
    PAGE_SETTINGS, PAGE_LOGS
)
from config.theme import Theme
from core.logger import get_app_logger
from gui.components.header import Header
from gui.components.sidebar import Sidebar
from gui.views.dashboard_view import DashboardView
from gui.views.api_management_view import ApiManagementView
from gui.views.settings_view import SettingsView
from gui.views.logs_view import LogsView
from gui.views.market_scanner_view import MarketScannerView
from gui.views.charts_view import ChartsView
from gui.views.signals_view import SignalsView
from gui.views.news_view import NewsView
from gui.views.portfolio_view import PortfolioView
from gui.views.backtesting_view import BacktestingView

logger = get_app_logger("MainWindow")


class MainWindow(tk.Tk):
    """
    Main Application Window Shell.
    Coordinates Header, Left Navigation Sidebar, and Content View Switcher.
    Thread-safe background queue polling runs continuously via Tkinter 'after()'.
    """
    def __init__(self, app_context):
        super().__init__()
        self.ctx = app_context

        # Window Branding & Initial Geometry
        self.title(f"{APP_NAME} {APP_VERSION}")
        saved_geom = self.ctx.settings.get("window_geometry", "1280x820")
        self.geometry(saved_geom)
        self.minsize(1100, 680)
        self.configure(bg=Theme.BG_ROOT)

        # Apply Modern TTK Dark Styling
        Theme.apply_ttk_styles(self)

        # Active View Map
        self._view_classes: Dict[str, Type[tk.Frame]] = {
            PAGE_DASHBOARD: DashboardView,
            PAGE_SCANNER: MarketScannerView,
            PAGE_CHARTS: ChartsView,
            PAGE_SIGNALS: SignalsView,
            PAGE_NEWS: NewsView,
            PAGE_PORTFOLIO: PortfolioView,
            PAGE_BACKTESTING: BacktestingView,
            PAGE_API: ApiManagementView,
            PAGE_SETTINGS: SettingsView,
            PAGE_LOGS: LogsView
        }
        self._view_instances: Dict[str, tk.Frame] = {}
        self._current_view_name = ""

        self._build_layout()

        # Start Thread-Safe Background Task Queue Polling
        self.ctx.tasks.start_polling(self, interval_ms=50)

        # Navigate to Initial Startup Page
        startup_page = self.ctx.settings.get("startup_page", PAGE_DASHBOARD)
        if startup_page not in self._view_classes:
            startup_page = PAGE_DASHBOARD
        self.navigate_to(startup_page)

        # Handle Graceful Shutdown
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        logger.info(f"Main GUI shell initialized successfully. Navigated to '{startup_page}'.")

    def _build_layout(self):
        """Construct the top-level grid containing Header, Sidebar, and Content Container"""
        self.grid_rowconfigure(0, weight=0)  # Header fixed height
        self.grid_rowconfigure(1, weight=1)  # Body area expands
        self.grid_columnconfigure(0, weight=0)  # Sidebar fixed width
        self.grid_columnconfigure(1, weight=1)  # Content area expands

        # 1. Top Header Bar
        self.header = Header(self, self.ctx)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")

        # 2. Left Sidebar Navigation
        self.sidebar = Sidebar(self, on_navigate=self.navigate_to)
        self.sidebar.grid(row=1, column=0, sticky="nsew")

        # 3. Main Content Container
        self.content_container = tk.Frame(self, bg=Theme.BG_CONTENT)
        self.content_container.grid(row=1, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

    def navigate_to(self, page_name: str):
        """
        Switch active view in the content area without destroying or reopening the app window.
        Caches view instances for fast, seamless navigation.
        """
        if page_name not in self._view_classes:
            logger.warning(f"Attempted to navigate to unknown page '{page_name}'")
            return

        if self._current_view_name == page_name:
            return

        # Lazy instantiate view if not already cached
        if page_name not in self._view_instances:
            view_cls = self._view_classes[page_name]
            view_inst = view_cls(self.content_container, self.ctx)
            view_inst.grid(row=0, column=0, sticky="nsew")
            self._view_instances[page_name] = view_inst

        # Bring requested view to top
        target_view = self._view_instances[page_name]
        target_view.tkraise()

        # Call refresh hook if supported
        if hasattr(target_view, "refresh_data"):
            target_view.refresh_data()
        elif hasattr(target_view, "refresh_table"):
            target_view.refresh_table()
        elif hasattr(target_view, "refresh_logs"):
            target_view.refresh_logs()

        self._current_view_name = page_name
        self.sidebar.set_active(page_name)

        if self.ctx.events:
            self.ctx.events.emit("PAGE_CHANGED", {"page": page_name})

    def on_closing(self):
        """Clean application shutdown handler"""
        try:
            logger.info("Application shutdown initiated by user.")
            
            # Save current window geometry
            current_geom = self.geometry()
            self.ctx.settings.set("window_geometry", current_geom)

            # Shutdown background services cleanly
            self.ctx.shutdown()
        except Exception as e:
            print(f"Error during shutdown: {e}")
        finally:
            self.destroy()
