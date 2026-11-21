"""
M4DI~UciH4 Trading Intelligence System
Settings View — Application Configuration & User Preferences — Enterprise Edition
Configures:
- Theme & Visual Appearance Customization
- Market, Symbol & Timeframe Defaults
- Risk Management Circuit Breakers & Position Sizing Defaults
- Trading & Simulation Defaults (Commission, Slippage)
- Chart Display Preferences
- Optional Telegram Notification Dispatcher & Live Test Ping
- Refresh Intervals & Background Worker Pacing
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from config.constants import (
    THEMES,
    TIMEFRAMES,
    SUPPORTED_MARKETS,
    LOG_LEVELS,
    SETTING_TELEGRAM_ENABLED,
    SETTING_TELEGRAM_BOT_TOKEN,
    SETTING_TELEGRAM_CHAT_ID,
    SETTING_TELEGRAM_NOTIFY_SIGNALS,
    SETTING_TELEGRAM_NOTIFY_NEWS,
    SETTING_TELEGRAM_NOTIFY_RISK,
    SETTING_TELEGRAM_NOTIFY_PORTFOLIO,
    DEFAULT_SETTINGS
)
from config.theme import Theme
from gui.components.cards import CardFrame
from gui.dialogs.confirm_dialog import ConfirmDialog
from core.logger import get_logger

logger = get_logger("SettingsView")


class SettingsView(tk.Frame):
    """
    Comprehensive Configuration Interface for institutional desktop parameters.
    All settings persist in SQLite and are broadcast across subsystems.
    """

    def __init__(self, parent, app_context, *args, **kwargs):
        super().__init__(parent, bg=Theme.BG_CONTENT, *args, **kwargs)
        self.ctx = app_context

        self._build_ui()
        self.load_settings()

    def _build_ui(self):
        # Scrollable container for responsive layout
        self.canvas = tk.Canvas(self, bg=Theme.BG_CONTENT, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar")
        self.scroll_content = tk.Frame(self.canvas, bg=Theme.BG_CONTENT, padx=20, pady=16)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.scroll_content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        # -------------------------------------------------------------
        # 1. Header Title & Save Bar
        # -------------------------------------------------------------
        header_bar = tk.Frame(self.scroll_content, bg=Theme.BG_CONTENT)
        header_bar.pack(fill="x", pady=(0, 16))

        title_box = tk.Frame(header_bar, bg=Theme.BG_CONTENT)
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="Application Configuration & Preferences",
            font=Theme.font_title(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CONTENT
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Manage visual themes, risk circuit breakers, paper trading, and Telegram alerts",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CONTENT
        ).pack(anchor="w", pady=(2, 0))

        # Actions on right
        btn_box = tk.Frame(header_bar, bg=Theme.BG_CONTENT)
        btn_box.pack(side="right")

        self.btn_reset = tk.Button(
            btn_box,
            text="Reset Defaults",
            font=Theme.font_body_bold(),
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_SECONDARY,
            activebackground=Theme.BG_CARD_ALT,
            activeforeground=Theme.TEXT_PRIMARY,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._on_reset_defaults
        )
        self.btn_reset.pack(side="left", padx=(0, 8))

        self.btn_save = tk.Button(
            btn_box,
            text="💾 Save All Settings",
            font=Theme.font_body_bold(),
            bg=Theme.ACCENT_CYAN,
            fg="#080C13",
            activebackground=Theme.ACCENT_CYAN_HOVER,
            activeforeground="#080C13",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._on_save_settings
        )
        self.btn_save.pack(side="left")

        # -------------------------------------------------------------
        # 2. Status Notification Banner
        # -------------------------------------------------------------
        self.status_banner = tk.Label(
            self.scroll_content,
            text="",
            font=Theme.font_caption(),
            fg=Theme.ACCENT_TURQUOISE,
            bg=Theme.BG_CONTENT
        )
        self.status_banner.pack(fill="x", pady=(0, 8))

        # -------------------------------------------------------------
        # 3. Two-Column Card Layout
        # -------------------------------------------------------------
        grid_frame = tk.Frame(self.scroll_content, bg=Theme.BG_CONTENT)
        grid_frame.pack(fill="both", expand=True)
        grid_frame.grid_columnconfigure((0, 1), weight=1, uniform="settings_cols")

        col_left = tk.Frame(grid_frame, bg=Theme.BG_CONTENT)
        col_left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        col_right = tk.Frame(grid_frame, bg=Theme.BG_CONTENT)
        col_right.grid(row=0, column=1, sticky="nsew")

        # =============================================================
        # CARD 1: Theme & Appearance (Left)
        # =============================================================
        card_theme = CardFrame(col_left, title="Theme & Visual Appearance", subtitle="Desktop UI Customization")
        card_theme.pack(fill="x", pady=(0, 14))

        tk.Label(card_theme.body, text="Active Color Palette", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(anchor="w", pady=(0, 4))
        self.theme_var = tk.StringVar()
        self.theme_combo = ttk.Combobox(card_theme.body, textvariable=self.theme_var, values=THEMES, state="readonly")
        self.theme_combo.pack(fill="x", pady=(0, 14))

        tk.Label(card_theme.body, text="Application Display Title", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(anchor="w", pady=(0, 4))
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(card_theme.body, textvariable=self.title_var)
        self.title_entry.pack(fill="x", pady=(0, 4))

        # =============================================================
        # CARD 2: Market & Chart Defaults (Left)
        # =============================================================
        card_market = CardFrame(col_left, title="Market & Chart Preferences", subtitle="Default Analysis Symbols & Views")
        card_market.pack(fill="x", pady=(0, 14))

        tk.Label(card_market.body, text="Default Analysis Symbol", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(anchor="w", pady=(0, 4))
        self.symbol_var = tk.StringVar()
        self.symbol_entry = ttk.Entry(card_market.body, textvariable=self.symbol_var)
        self.symbol_entry.pack(fill="x", pady=(0, 12))

        tk.Label(card_market.body, text="Default Trading Timeframe", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(anchor="w", pady=(0, 4))
        self.tf_var = tk.StringVar()
        self.tf_combo = ttk.Combobox(card_market.body, textvariable=self.tf_var, values=TIMEFRAMES, state="readonly")
        self.tf_combo.pack(fill="x", pady=(0, 12))

        tk.Label(card_market.body, text="Default Market / Asset Class", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(anchor="w", pady=(0, 4))
        self.market_var = tk.StringVar()
        self.market_combo = ttk.Combobox(card_market.body, textvariable=self.market_var, values=SUPPORTED_MARKETS, state="readonly")
        self.market_combo.pack(fill="x", pady=(0, 12))

        # Chart display toggles
        self.show_vol_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            card_market.body,
            text="Display Volume Sub-Panel on Candlestick Charts",
            variable=self.show_vol_var,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            selectcolor=Theme.BG_INPUT,
            font=Theme.font_body()
        ).pack(anchor="w", pady=(0, 4))

        self.show_grid_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            card_market.body,
            text="Display Canvas Background Price Gridlines",
            variable=self.show_grid_var,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            selectcolor=Theme.BG_INPUT,
            font=Theme.font_body()
        ).pack(anchor="w")

        # =============================================================
        # CARD 3: Risk Management & Circuit Breakers (Left)
        # =============================================================
        card_risk = CardFrame(col_left, title="Risk Management & Circuit Breakers", subtitle="Account Protection Guardrails")
        card_risk.pack(fill="x")

        r_grid = tk.Frame(card_risk.body, bg=Theme.BG_CARD)
        r_grid.pack(fill="x")
        r_grid.grid_columnconfigure((0, 1), weight=1)

        tk.Label(r_grid, text="Risk per Trade (%):", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.risk_pct_var = tk.StringVar(value="1.0")
        ttk.Entry(r_grid, textvariable=self.risk_pct_var, width=12).grid(row=0, column=1, sticky="e", pady=(0, 4))

        tk.Label(r_grid, text="Max Drawdown Limit (%):", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=1, column=0, sticky="w", pady=(0, 4))
        self.max_dd_var = tk.StringVar(value="15.0")
        ttk.Entry(r_grid, textvariable=self.max_dd_var, width=12).grid(row=1, column=1, sticky="e", pady=(0, 4))

        tk.Label(r_grid, text="Daily Loss Limit (%):", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.daily_loss_var = tk.StringVar(value="3.0")
        ttk.Entry(r_grid, textvariable=self.daily_loss_var, width=12).grid(row=2, column=1, sticky="e", pady=(0, 4))

        tk.Label(r_grid, text="Max Open Positions:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=3, column=0, sticky="w", pady=(0, 4))
        self.max_pos_var = tk.StringVar(value="5")
        ttk.Entry(r_grid, textvariable=self.max_pos_var, width=12).grid(row=3, column=1, sticky="e", pady=(0, 4))

        # =============================================================
        # CARD 4: Optional Telegram Notifications (Right)
        # =============================================================
        card_tg = CardFrame(col_right, title="Telegram Notifications (Optional)", subtitle="Real-time Mobile Alerts Dispatcher")
        card_tg.pack(fill="x", pady=(0, 14))

        self.tg_enable_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            card_tg.body,
            text="Enable Telegram Notification Transmissions",
            variable=self.tg_enable_var,
            bg=Theme.BG_CARD,
            fg=Theme.ACCENT_CYAN,
            selectcolor=Theme.BG_INPUT,
            font=Theme.font_body_bold()
        ).pack(anchor="w", pady=(0, 10))

        tk.Label(card_tg.body, text="Telegram Bot Token:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(anchor="w", pady=(0, 2))
        self.tg_token_var = tk.StringVar()
        self.tg_token_entry = ttk.Entry(card_tg.body, textvariable=self.tg_token_var, show="*")
        self.tg_token_entry.pack(fill="x", pady=(0, 8))

        tk.Label(card_tg.body, text="Telegram Target Chat ID:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(anchor="w", pady=(0, 2))
        self.tg_chat_var = tk.StringVar()
        self.tg_chat_entry = ttk.Entry(card_tg.body, textvariable=self.tg_chat_var)
        self.tg_chat_entry.pack(fill="x", pady=(0, 10))

        # Specific alert toggles
        tg_toggles = tk.Frame(card_tg.body, bg=Theme.BG_CARD)
        tg_toggles.pack(fill="x", pady=(0, 10))

        self.tg_signals_var = tk.BooleanVar(value=True)
        tk.Checkbutton(tg_toggles, text="Trading Signals", variable=self.tg_signals_var, bg=Theme.BG_CARD, fg=Theme.TEXT_PRIMARY, selectcolor=Theme.BG_INPUT, font=Theme.font_caption()).pack(anchor="w")

        self.tg_news_var = tk.BooleanVar(value=True)
        tk.Checkbutton(tg_toggles, text="High-Impact Breaking News", variable=self.tg_news_var, bg=Theme.BG_CARD, fg=Theme.TEXT_PRIMARY, selectcolor=Theme.BG_INPUT, font=Theme.font_caption()).pack(anchor="w")

        self.tg_risk_var = tk.BooleanVar(value=True)
        tk.Checkbutton(tg_toggles, text="Risk & Circuit Breaker Warnings", variable=self.tg_risk_var, bg=Theme.BG_CARD, fg=Theme.TEXT_PRIMARY, selectcolor=Theme.BG_INPUT, font=Theme.font_caption()).pack(anchor="w")

        self.tg_port_var = tk.BooleanVar(value=True)
        tk.Checkbutton(tg_toggles, text="Paper Trading Orders & Ledger", variable=self.tg_port_var, bg=Theme.BG_CARD, fg=Theme.TEXT_PRIMARY, selectcolor=Theme.BG_INPUT, font=Theme.font_caption()).pack(anchor="w")

        self.btn_test_tg = tk.Button(
            card_tg.body,
            text="📡 Send Test Telegram Ping",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ACCENT_TURQUOISE,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._on_test_telegram
        )
        self.btn_test_tg.pack(anchor="w")

        # =============================================================
        # CARD 5: Simulation & Execution Settings (Right)
        # =============================================================
        card_sim = CardFrame(col_right, title="Paper Trading & Execution Model", subtitle="Slippage & Commission Parameters")
        card_sim.pack(fill="x", pady=(0, 14))

        sim_grid = tk.Frame(card_sim.body, bg=Theme.BG_CARD)
        sim_grid.pack(fill="x")
        sim_grid.grid_columnconfigure((0, 1), weight=1)

        tk.Label(sim_grid, text="Default Commission (%):", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.comm_var = tk.StringVar(value="0.05")
        ttk.Entry(sim_grid, textvariable=self.comm_var, width=12).grid(row=0, column=1, sticky="e", pady=(0, 4))

        tk.Label(sim_grid, text="Default Slippage (%):", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=1, column=0, sticky="w", pady=(0, 4))
        self.slip_var = tk.StringVar(value="0.02")
        ttk.Entry(sim_grid, textvariable=self.slip_var, width=12).grid(row=1, column=1, sticky="e", pady=(0, 4))

        # =============================================================
        # CARD 6: System Refresh & Workers (Right)
        # =============================================================
        card_refresh = CardFrame(col_right, title="System Refresh & Workers", subtitle="Async Task Queue & Logging")
        card_refresh.pack(fill="x")

        tk.Label(card_refresh.body, text="Dashboard Auto-Refresh Interval (sec):", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(anchor="w", pady=(0, 4))
        self.refresh_var = tk.StringVar(value="30")
        self.refresh_combo = ttk.Combobox(card_refresh.body, textvariable=self.refresh_var, values=["10", "15", "30", "60", "120"], state="readonly")
        self.refresh_combo.pack(fill="x", pady=(0, 10))

        tk.Label(card_refresh.body, text="System Logging Level:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(anchor="w", pady=(0, 4))
        self.log_level_var = tk.StringVar(value="INFO")
        self.log_level_combo = ttk.Combobox(card_refresh.body, textvariable=self.log_level_var, values=LOG_LEVELS, state="readonly")
        self.log_level_combo.pack(fill="x")

    def load_settings(self):
        """Populate inputs with values from SQLite SettingsManager"""
        s = self.ctx.settings
        self.theme_var.set(s.get("theme", DEFAULT_SETTINGS["theme"]))
        self.title_var.set(s.get("app_title", "M4DI~UciH4 Trading Intelligence"))
        self.symbol_var.set(s.get("default_symbol", DEFAULT_SETTINGS["default_symbol"]))
        self.tf_var.set(s.get("default_timeframe", DEFAULT_SETTINGS["default_timeframe"]))
        self.market_var.set(s.get("default_market", DEFAULT_SETTINGS["default_market"]))
        self.show_vol_var.set(s.get_bool("chart_show_volume", True))
        self.show_grid_var.set(s.get_bool("chart_show_grid", True))

        self.risk_pct_var.set(s.get("risk_per_trade_pct", DEFAULT_SETTINGS["risk_per_trade_pct"]))
        self.max_dd_var.set(s.get("max_drawdown_limit_pct", DEFAULT_SETTINGS["max_drawdown_limit_pct"]))
        self.daily_loss_var.set(s.get("daily_loss_limit_pct", DEFAULT_SETTINGS["daily_loss_limit_pct"]))
        self.max_pos_var.set(s.get("max_open_positions", DEFAULT_SETTINGS["max_open_positions"]))

        self.comm_var.set(s.get("default_commission_pct", DEFAULT_SETTINGS["default_commission_pct"]))
        self.slip_var.set(s.get("default_slippage_pct", DEFAULT_SETTINGS["default_slippage_pct"]))
        self.refresh_var.set(s.get("refresh_interval_sec", DEFAULT_SETTINGS["refresh_interval_sec"]))
        self.log_level_var.set(s.get("log_level", "INFO"))

        # Telegram
        self.tg_enable_var.set(s.get_bool(SETTING_TELEGRAM_ENABLED, False))
        self.tg_token_var.set(s.get(SETTING_TELEGRAM_BOT_TOKEN, ""))
        self.tg_chat_var.set(s.get(SETTING_TELEGRAM_CHAT_ID, ""))
        self.tg_signals_var.set(s.get_bool(SETTING_TELEGRAM_NOTIFY_SIGNALS, True))
        self.tg_news_var.set(s.get_bool(SETTING_TELEGRAM_NOTIFY_NEWS, True))
        self.tg_risk_var.set(s.get_bool(SETTING_TELEGRAM_NOTIFY_RISK, True))
        self.tg_port_var.set(s.get_bool(SETTING_TELEGRAM_NOTIFY_PORTFOLIO, True))

    def _on_save_settings(self):
        """Persist settings to SQLite and update active subsystems"""
        try:
            payload = {
                "theme": self.theme_var.get(),
                "app_title": self.title_var.get().strip(),
                "default_symbol": self.symbol_var.get().strip(),
                "default_timeframe": self.tf_var.get(),
                "default_market": self.market_var.get(),
                "chart_show_volume": str(self.show_vol_var.get()),
                "chart_show_grid": str(self.show_grid_var.get()),

                "risk_per_trade_pct": str(float(self.risk_pct_var.get())),
                "max_drawdown_limit_pct": str(float(self.max_dd_var.get())),
                "daily_loss_limit_pct": str(float(self.daily_loss_var.get())),
                "max_open_positions": str(int(self.max_pos_var.get())),

                "default_commission_pct": str(float(self.comm_var.get())),
                "default_slippage_pct": str(float(self.slip_var.get())),
                "refresh_interval_sec": self.refresh_var.get(),
                "log_level": self.log_level_var.get(),

                SETTING_TELEGRAM_ENABLED: str(self.tg_enable_var.get()),
                SETTING_TELEGRAM_BOT_TOKEN: self.tg_token_var.get().strip(),
                SETTING_TELEGRAM_CHAT_ID: self.tg_chat_var.get().strip(),
                SETTING_TELEGRAM_NOTIFY_SIGNALS: str(self.tg_signals_var.get()),
                SETTING_TELEGRAM_NOTIFY_NEWS: str(self.tg_news_var.get()),
                SETTING_TELEGRAM_NOTIFY_RISK: str(self.tg_risk_var.get()),
                SETTING_TELEGRAM_NOTIFY_PORTFOLIO: str(self.tg_port_var.get()),
            }
            self.ctx.settings.save_bulk(payload)

            # Apply Risk Manager dynamic updates
            self.ctx.risk_manager.risk_per_trade_pct = float(self.risk_pct_var.get())
            self.ctx.risk_manager.max_drawdown_limit_pct = float(self.max_dd_var.get())
            self.ctx.risk_manager.daily_loss_limit_pct = float(self.daily_loss_var.get())
            self.ctx.risk_manager.max_open_positions = int(self.max_pos_var.get())

            # Apply Palette
            Theme.set_palette(self.theme_var.get())

            logger.info("Application settings saved successfully to SQLite.")

            if self.ctx.events:
                self.ctx.events.emit("SETTINGS_SAVED", payload)

            self.status_banner.config(
                text="✅ All application settings saved & applied successfully!",
                fg=Theme.ACCENT_TURQUOISE
            )
            self.after(3000, lambda: self.status_banner.config(text=""))
        except ValueError as ve:
            messagebox.showerror("Validation Error", f"Invalid numerical value: {ve}")
        except Exception as e:
            messagebox.showerror("Error Saving Settings", str(e))

    def _on_test_telegram(self):
        """Perform instant connectivity test to configured Telegram bot and chat"""
        # Save temporary entered values
        self.ctx.settings.set(SETTING_TELEGRAM_BOT_TOKEN, self.tg_token_var.get().strip())
        self.ctx.settings.set(SETTING_TELEGRAM_CHAT_ID, self.tg_chat_var.get().strip())

        ok, msg = self.ctx.telegram.test_connection()
        if ok:
            messagebox.showinfo("Telegram Connected", msg)
        else:
            messagebox.showwarning("Telegram Error", msg)

    def _on_reset_defaults(self):
        """Confirm and restore factory settings"""
        confirm = ConfirmDialog(
            self,
            title="Reset Settings",
            message="Are you sure you want to restore all settings to default values?",
            confirm_label="Reset All",
            is_danger=True
        )
        self.wait_window(confirm)

        if confirm.confirmed:
            self.ctx.settings.save_bulk(DEFAULT_SETTINGS)
            self.load_settings()
            logger.warning("Application settings reset to factory defaults.")
            self.status_banner.config(
                text="⚠️ Settings reset to default values.",
                fg=Theme.ACCENT_AMBER
            )
            self.after(3000, lambda: self.status_banner.config(text=""))
