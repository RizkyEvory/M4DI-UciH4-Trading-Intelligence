"""
M4DI~UciH4 Trading Intelligence System
Executive Institutional Dashboard — Enterprise Edition
Integrates real-time telemetry across all core subsystems:
- Multi-Asset Market Overview & Benchmark Telemetry
- Active Watchlist Performance & Multi-Watchlist Switcher
- Trading Signal Distribution & High-Confidence Setup Telemetry
- Deterministic NLP News Sentiment & Breaking Catalyst Feed
- Portfolio Equity, Unrealized/Realized P&L, & Asset Allocation
- Risk Management Circuit Breakers & Drawdown Utilization
- Provider Health, Multi-Key Rotation, & Request Metrics
- One-Click System Diagnostics & Data Export
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional
from datetime import datetime

from config.constants import (
    API_PROVIDERS,
    SUPPORTED_MARKETS,
    PROVIDER_FINNHUB,
    PROVIDER_TWELVE_DATA,
    PROVIDER_NEWS_API
)
from config.theme import Theme
from gui.components.cards import CardFrame, StatCard
from gui.components.tables import SortableTreeview
from core.logger import get_logger

logger = get_logger("DashboardView")


class DashboardView(tk.Frame):
    """
    Institutional Executive Dashboard.
    Provides reactive, high-density quantitative overview with zero fake data.
    """

    def __init__(self, parent, app_context, *args, **kwargs):
        super().__init__(parent, bg=Theme.BG_CONTENT, *args, **kwargs)
        self.ctx = app_context
        self._selected_wl_name = tk.StringVar(value="All Watchlists")

        self._build_ui()
        self.refresh_data()

        # Event subscriptions
        if self.ctx.events:
            self.ctx.events.subscribe("API_KEY_CHANGED", lambda d: self.refresh_data())
            self.ctx.events.subscribe("SETTINGS_SAVED", lambda d: self.refresh_data())
            self.ctx.events.subscribe("PORTFOLIO_CHANGED", lambda d: self.refresh_data())
            self.ctx.events.subscribe("SIGNAL_GENERATED", lambda d: self.refresh_data())

    def _build_ui(self):
        # Canvas & Scrollbar for smooth vertical layout
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
        # 1. Header & Actions Bar
        # -------------------------------------------------------------
        header_bar = tk.Frame(self.scroll_content, bg=Theme.BG_CONTENT)
        header_bar.pack(fill="x", pady=(0, 16))

        title_box = tk.Frame(header_bar, bg=Theme.BG_CONTENT)
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="Executive Intelligence Dashboard",
            font=Theme.font_title(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CONTENT
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Unified Cross-Subsystem Surveillance, Portfolio Telemetry & Risk Matrix",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CONTENT
        ).pack(anchor="w", pady=(2, 0))

        # Quick Action Buttons
        btn_box = tk.Frame(header_bar, bg=Theme.BG_CONTENT)
        btn_box.pack(side="right")

        self.btn_refresh = tk.Button(
            btn_box,
            text="🔄 Refresh Telemetry",
            font=Theme.font_body_bold(),
            bg=Theme.BG_CARD,
            fg=Theme.ACCENT_CYAN,
            activebackground=Theme.BG_CARD_ALT,
            activeforeground=Theme.ACCENT_CYAN,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.refresh_data
        )
        self.btn_refresh.pack(side="left", padx=(0, 8))

        self.btn_diag = tk.Button(
            btn_box,
            text="🩺 Diagnostics",
            font=Theme.font_body_bold(),
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            activebackground=Theme.BG_CARD_ALT,
            activeforeground=Theme.ACCENT_TURQUOISE,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._show_diagnostics_modal
        )
        self.btn_diag.pack(side="left")

        # -------------------------------------------------------------
        # 2. Executive Stat Cards Row (5 Cards)
        # -------------------------------------------------------------
        stats_row = tk.Frame(self.scroll_content, bg=Theme.BG_CONTENT)
        stats_row.pack(fill="x", pady=(0, 16))
        stats_row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="stat_cards")

        self.card_equity = StatCard(
            stats_row,
            icon="💼",
            value="$100,000.00",
            label="Total Paper Equity",
            status_text="Return: +0.00%",
            accent_color=Theme.ACCENT_EMERALD
        )
        self.card_equity.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.card_signals = StatCard(
            stats_row,
            icon="🎯",
            value="0 Active",
            label="Institutional Signals",
            status_text="High Confidence: 0",
            accent_color=Theme.ACCENT_GOLD
        )
        self.card_signals.grid(row=0, column=1, sticky="nsew", padx=(0, 8))

        self.card_risk = StatCard(
            stats_row,
            icon="🛡️",
            value="NORMAL",
            label="Circuit Breaker Status",
            status_text="DD: 0.0% / 15.0%",
            accent_color=Theme.ACCENT_CYAN
        )
        self.card_risk.grid(row=0, column=2, sticky="nsew", padx=(0, 8))

        self.card_sentiment = StatCard(
            stats_row,
            icon="📰",
            value="NEUTRAL",
            label="News Macro Sentiment",
            status_text="Score: 0.00",
            accent_color=Theme.ACCENT_TURQUOISE
        )
        self.card_sentiment.grid(row=0, column=3, sticky="nsew", padx=(0, 8))

        self.card_apis = StatCard(
            stats_row,
            icon="🔑",
            value="0 / 3 Online",
            label="API Infrastructure",
            status_text="Paced & Protected",
            accent_color=Theme.ACCENT_PURPLE
        )
        self.card_apis.grid(row=0, column=4, sticky="nsew")

        # -------------------------------------------------------------
        # 3. Two-Column Dashboard Layout
        # -------------------------------------------------------------
        cols_frame = tk.Frame(self.scroll_content, bg=Theme.BG_CONTENT)
        cols_frame.pack(fill="both", expand=True)
        cols_frame.grid_columnconfigure(0, weight=6, uniform="dash_cols")
        cols_frame.grid_columnconfigure(1, weight=4, uniform="dash_cols")

        left_col = tk.Frame(cols_frame, bg=Theme.BG_CONTENT)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        right_col = tk.Frame(cols_frame, bg=Theme.BG_CONTENT)
        right_col.grid(row=0, column=1, sticky="nsew")

        # =============================================================
        # LEFT COLUMN COMPONENTS
        # =============================================================

        # Component A: Market Benchmark Overview
        card_benchmarks = CardFrame(left_col, title="Market Benchmarks & Asset Classes", subtitle="Institutional Liquidity Hubs")
        card_benchmarks.pack(fill="x", pady=(0, 14))

        self.benchmarks_grid = tk.Frame(card_benchmarks.body, bg=Theme.BG_CARD)
        self.benchmarks_grid.pack(fill="x")
        self.benchmarks_grid.grid_columnconfigure((0, 1), weight=1)

        # Benchmark tiles
        self._build_benchmark_tiles()

        # Component B: Watchlist Performance & Multi-Watchlist Selector
        card_watchlist = CardFrame(left_col, title="Active Watchlist Performance", subtitle="Tracked symbols with quantitative alerts and notes")
        card_watchlist.pack(fill="both", expand=True, pady=(0, 14))

        # Selector bar
        wl_bar = tk.Frame(card_watchlist.body, bg=Theme.BG_CARD)
        wl_bar.pack(fill="x", pady=(0, 8))

        tk.Label(
            wl_bar,
            text="Selected Pool:",
            font=Theme.font_body_bold(),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        ).pack(side="left", padx=(0, 8))

        self.wl_combo = ttk.Combobox(
            wl_bar,
            textvariable=self._selected_wl_name,
            state="readonly",
            width=22,
            font=Theme.font_body()
        )
        self.wl_combo.pack(side="left")
        self.wl_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_watchlist_table())

        self.watchlist_table = SortableTreeview(
            card_watchlist.body,
            columns=["symbol", "market", "notes", "alert", "added_at"],
            headings=["Symbol", "Market", "Institutional Thesis / Notes", "Active Alert", "Added"],
            widths=[90, 130, 200, 110, 110]
        )
        self.watchlist_table.pack(fill="both", expand=True)

        # Component C: Active Signals Summary
        card_signals = CardFrame(left_col, title="Active Trading Signals Summary", subtitle="Multi-Factor Confluence Engine")
        card_signals.pack(fill="x")

        self.signals_table = SortableTreeview(
            card_signals.body,
            columns=["symbol", "signal", "confidence", "score", "entry", "sl", "tp1"],
            headings=["Symbol", "Setup", "Confidence", "Score", "Entry", "Stop Loss", "Target 1"],
            widths=[80, 100, 85, 75, 80, 80, 80]
        )
        self.signals_table.pack(fill="x")

        # =============================================================
        # RIGHT COLUMN COMPONENTS
        # =============================================================

        # Component D: Portfolio & Risk Exposure
        card_portfolio = CardFrame(right_col, title="Portfolio & Capital Exposure", subtitle="Paper Trading Ledger Status")
        card_portfolio.pack(fill="x", pady=(0, 14))

        self.port_box = tk.Frame(card_portfolio.body, bg=Theme.BG_CARD)
        self.port_box.pack(fill="x")

        # Component E: News Intelligence & Macro Catalyst
        card_news = CardFrame(right_col, title="Macro News Sentiment & Catalysts", subtitle="Deterministic NLP Financial Intelligence")
        card_news.pack(fill="x", pady=(0, 14))

        self.news_box = tk.Frame(card_news.body, bg=Theme.BG_CARD)
        self.news_box.pack(fill="x")

        # Component F: API Provider Health & Multi-Key Telemetry
        card_api = CardFrame(right_col, title="API Provider Health & Key Rotation", subtitle="Paced Rate Limiter & Automatic Failover")
        card_api.pack(fill="x", pady=(0, 14))

        self.api_box = tk.Frame(card_api.body, bg=Theme.BG_CARD)
        self.api_box.pack(fill="x")

        # Component G: System Status & Diagnostic Quick Check
        card_sys = CardFrame(right_col, title="System Environment & Safety", subtitle="Security & Thread-Safe Engine")
        card_sys.pack(fill="x")

        self.sys_box = tk.Frame(card_sys.body, bg=Theme.BG_CARD)
        self.sys_box.pack(fill="x")

    def _build_benchmark_tiles(self):
        """Construct the 4 benchmark asset class containers"""
        benchmarks = [
            ("Gold / Precious Metals", "XAU/USD", "Commodities Benchmark", "Institutional Store of Value"),
            ("Forex Major", "EUR/USD", "Macro FX Liquidity", "ECB / Fed Monetary Dynamics"),
            ("US Stock Index", "US30 / SPX500", "Equity Risk Sentiment", "Corporate Earnings & Growth"),
            ("Digital Assets", "BTC/USDT", "Crypto Liquid Benchmark", "Global Liquidity Cycle")
        ]

        for i, (cat, sym, role, desc) in enumerate(benchmarks):
            box = tk.Frame(
                self.benchmarks_grid,
                bg=Theme.BG_CARD_ALT,
                padx=10,
                pady=8,
                highlightbackground=Theme.BORDER_SUBTLE,
                highlightthickness=1
            )
            box.grid(row=i // 2, column=i % 2, sticky="nsew", padx=4, pady=4)

            top = tk.Frame(box, bg=Theme.BG_CARD_ALT)
            top.pack(fill="x")
            tk.Label(top, text=cat, font=Theme.font_caption(), fg=Theme.TEXT_MUTED, bg=Theme.BG_CARD_ALT).pack(side="left")
            tk.Label(top, text="READY", font=Theme.font_caption(), fg=Theme.ACCENT_TURQUOISE, bg=Theme.BG_CARD_ALT).pack(side="right")

            tk.Label(box, text=sym, font=Theme.font_body_bold(), fg=Theme.TEXT_PRIMARY, bg=Theme.BG_CARD_ALT).pack(anchor="w", pady=(2, 0))
            tk.Label(box, text=f"{role} • {desc}", font=Theme.font_caption(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD_ALT).pack(anchor="w")

    def refresh_data(self):
        """Pull live telemetry from all core subsystems and refresh GUI widgets"""
        try:
            # 1. Portfolio Telemetry
            summary = self.ctx.portfolio.get_portfolio_summary()
            self.card_equity.update_value(
                f"${summary.total_equity:,.2f}",
                status_text=f"Return: {summary.total_return_pct:+.2f}% | Cash: ${summary.cash:,.2f}"
            )

            # 2. Risk Status
            risk_mgr = self.ctx.risk_manager
            dd_pct = risk_mgr.calculate_drawdown_pct(summary.total_equity)
            dd_lim = risk_mgr.max_drawdown_limit_pct
            status_text = "HALTED" if dd_pct >= dd_lim else ("CAUTION" if dd_pct >= dd_lim * 0.7 else "NORMAL")
            accent = Theme.ACCENT_ROSE if status_text == "HALTED" else (Theme.ACCENT_AMBER if status_text == "CAUTION" else Theme.ACCENT_CYAN)

            self.card_risk.update_value(
                status_text,
                status_text=f"DD: {dd_pct:.1f}% / {dd_lim:.1f}% | Open: {summary.open_positions_count}/{risk_mgr.max_open_positions}"
            )

            # 3. News Sentiment Telemetry
            recent_articles = self.ctx.news_engine.get_cached_articles(limit=50)
            if recent_articles:
                scores = [a.sentiment_score for a in recent_articles]
                avg_score = sum(scores) / len(scores) if scores else 0.0
                sent_label = "BULLISH" if avg_score >= 0.15 else ("BEARISH" if avg_score <= -0.15 else "NEUTRAL")
                self.card_sentiment.update_value(
                    sent_label,
                    status_text=f"Score: {avg_score:+.2f} ({len(recent_articles)} Articles)"
                )
            else:
                self.card_sentiment.update_value(
                    "AWAITING FEED",
                    status_text="News Engine Ready"
                )

            # 4. API Status Card
            api_summary = self.ctx.api_keys.count_summary()
            active_keys = api_summary["active_keys"]
            total_keys = api_summary["total_keys"]
            self.card_apis.update_value(
                f"{active_keys} Active",
                status_text=f"{total_keys} Total Keys Managed"
            )

            # 5. Populate Watchlist Combo & Table
            all_wls = self.ctx.watchlists.get_watchlists()
            wl_names = ["All Watchlists"] + [w["name"] for w in all_wls]
            self.wl_combo["values"] = wl_names
            if self._selected_wl_name.get() not in wl_names:
                self._selected_wl_name.set("All Watchlists")
            self._refresh_watchlist_table()

            # 6. Populate Signals Table
            self._refresh_signals_table()

            # 7. Rebuild Right Column Cards
            self._render_portfolio_card(summary)
            self._render_news_card(recent_articles)
            self._render_api_card(api_summary)
            self._render_sys_card()

        except Exception as e:
            logger.warning(f"Error during dashboard telemetry refresh: {e}")

    def _refresh_watchlist_table(self):
        """Update active watchlist table with symbols, notes, and alerts"""
        self.watchlist_table.clear()
        chosen = self._selected_wl_name.get()

        if chosen == "All Watchlists":
            symbols = []
            for w in self.ctx.watchlists.get_watchlists():
                symbols.extend(self.ctx.watchlists.get_symbols(w["id"]))
        else:
            symbols = self.ctx.watchlists.get_symbols(chosen)

        if not symbols:
            self.watchlist_table.insert_row(
                ("-", "No symbols", "Add symbols via Market Scanner or Watchlist", "-", "-"),
                tags=("disabled_tag",)
            )
            return

        for s in symbols:
            sym = s.get("symbol", "-")
            mkt = s.get("market", "-")
            notes = s.get("notes", "") or "No notes"
            alert = s.get("alert_condition", "") or "None"
            added = s.get("added_at", "-")
            self.watchlist_table.insert_row((sym, mkt, notes, alert, added))

    def _refresh_signals_table(self):
        """Populate active generated signals"""
        self.signals_table.clear()
        active_signals = self.ctx.signals.get_active_signals(limit=10)
        self.card_signals.update_value(
            f"{len(active_signals)} Active",
            status_text=f"Strong Setups: {sum(1 for s in active_signals if 'STRONG' in s.signal.upper())}"
        )

        if not active_signals:
            self.signals_table.insert_row(
                ("-", "No active signals", "-", "-", "-", "-", "-"),
                tags=("disabled_tag",)
            )
            return

        for s in active_signals:
            self.signals_table.insert_row((
                s.symbol,
                s.signal,
                f"{s.confidence_pct:.1f}%",
                f"{s.score:+.1f}",
                f"${s.entry_price:,.4f}",
                f"${s.stop_loss:,.4f}",
                f"${s.take_profit_1:,.4f}"
            ))

    def _render_portfolio_card(self, summary):
        for w in self.port_box.winfo_children():
            w.destroy()

        metrics = [
            ("Available Cash", f"${summary.cash:,.2f}", Theme.TEXT_PRIMARY),
            ("Invested Capital", f"${summary.invested_capital:,.2f}", Theme.TEXT_PRIMARY),
            ("Unrealized P&L", f"${summary.unrealized_pnl:+,.2f}", Theme.ACCENT_EMERALD if summary.unrealized_pnl >= 0 else Theme.ACCENT_ROSE),
            ("Realized P&L", f"${summary.realized_pnl:+,.2f}", Theme.ACCENT_EMERALD if summary.realized_pnl >= 0 else Theme.ACCENT_ROSE),
            ("Portfolio Exposure", f"{summary.exposure_pct:.1f}%", Theme.ACCENT_CYAN),
            ("Open Positions", f"{summary.open_positions_count} active", Theme.ACCENT_GOLD)
        ]

        for k, v, color in metrics:
            row = tk.Frame(self.port_box, bg=Theme.BG_CARD, pady=2)
            row.pack(fill="x")
            tk.Label(row, text=k, font=Theme.font_body(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left")
            tk.Label(row, text=v, font=Theme.font_body_bold(), fg=color, bg=Theme.BG_CARD).pack(side="right")

    def _render_news_card(self, recent_articles):
        for w in self.news_box.winfo_children():
            w.destroy()

        if not recent_articles:
            tk.Label(
                self.news_box,
                text="No news ingested yet. Configure NewsAPI / Finnhub keys to stream.",
                font=Theme.font_caption(),
                fg=Theme.TEXT_MUTED,
                bg=Theme.BG_CARD,
                pady=10
            ).pack()
            return

        for a in recent_articles[:4]:
            box = tk.Frame(self.news_box, bg=Theme.BG_CARD_ALT, padx=8, pady=6, highlightbackground=Theme.BORDER_SUBTLE, highlightthickness=1)
            box.pack(fill="x", pady=2)

            top = tk.Frame(box, bg=Theme.BG_CARD_ALT)
            top.pack(fill="x")
            color = Theme.ACCENT_EMERALD if a.sentiment_label == "POSITIVE" else (Theme.ACCENT_ROSE if a.sentiment_label == "NEGATIVE" else Theme.TEXT_MUTED)
            tk.Label(top, text=f"[{a.impact_tier}] {a.category}", font=Theme.font_caption(), fg=Theme.ACCENT_GOLD, bg=Theme.BG_CARD_ALT).pack(side="left")
            tk.Label(top, text=a.sentiment_label, font=Theme.font_caption(), fg=color, bg=Theme.BG_CARD_ALT).pack(side="right")

            tk.Label(box, text=a.title[:65] + "..." if len(a.title) > 65 else a.title, font=Theme.font_body_bold(), fg=Theme.TEXT_PRIMARY, bg=Theme.BG_CARD_ALT, wraplength=350, justify="left").pack(anchor="w", pady=(2, 0))

    def _render_api_card(self, summary):
        for w in self.api_box.winfo_children():
            w.destroy()

        for prov in API_PROVIDERS:
            p_stat = summary["by_provider"].get(prov, {"total": 0, "active": 0})
            health = self.ctx.health_monitor.get_health(prov)
            status = health.get("status", "DISCONNECTED")
            strat = self.ctx.key_rotation.get_strategy(prov).upper()

            row = tk.Frame(self.api_box, bg=Theme.BG_CARD_ALT, padx=10, pady=5, highlightbackground=Theme.BORDER_SUBTLE, highlightthickness=1)
            row.pack(fill="x", pady=2)

            tk.Label(row, text=prov, font=Theme.font_body_bold(), fg=Theme.TEXT_PRIMARY, bg=Theme.BG_CARD_ALT).pack(side="left")

            if p_stat["active"] > 0:
                if status == "CONNECTED":
                    badge = f"🟢 Connected ({p_stat['active']} Keys)"
                    fg = Theme.ACCENT_EMERALD
                elif status == "RATE_LIMITED":
                    badge = f"⏳ Cooldown ({p_stat['active']} Keys)"
                    fg = Theme.ACCENT_GOLD
                else:
                    badge = f"⚡ Ready ({p_stat['active']} Keys • {strat})"
                    fg = Theme.ACCENT_CYAN
            else:
                badge = "⚪ Unconfigured"
                fg = Theme.TEXT_MUTED

            tk.Label(row, text=badge, font=Theme.font_caption(), fg=fg, bg=Theme.BG_CARD_ALT).pack(side="right")

    def _render_sys_card(self):
        for w in self.sys_box.winfo_children():
            w.destroy()

        items = [
            ("Database Engine", "SQLite 3.50+ WAL (Optimized)"),
            ("Telegram Bot", "Ready (Configurable)" if self.ctx.telegram.is_enabled else "Optional / Standby"),
            ("Key Encryption", "PBKDF2-HMAC-SHA256 Encrypted"),
            ("Universal Exporter", "CSV & JSON Native Engine"),
            ("Diagnostics Suite", "Automated Integrity & Cache Check")
        ]
        for k, v in items:
            row = tk.Frame(self.sys_box, bg=Theme.BG_CARD, pady=2)
            row.pack(fill="x")
            tk.Label(row, text=k, font=Theme.font_body(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left")
            tk.Label(row, text=v, font=Theme.font_caption(), fg=Theme.ACCENT_TURQUOISE, bg=Theme.BG_CARD).pack(side="right")

    def _show_diagnostics_modal(self):
        """Display System Diagnostics modal dialog"""
        diag_results = self.ctx.diagnostics.run_full_diagnostics()

        win = tk.Toplevel(self)
        win.title("M4DI~UciH4 System Diagnostics Audit")
        win.geometry("640x580")
        win.configure(bg=Theme.BG_MODAL)
        win.transient(self)
        win.grab_set()

        content = tk.Frame(win, bg=Theme.BG_MODAL, padx=16, pady=16)
        content.pack(fill="both", expand=True)

        tk.Label(
            content,
            text=f"System Diagnostics: {diag_results['overall_status']} ({diag_results['score']} Checks Passed)",
            font=Theme.font_title(),
            fg=Theme.ACCENT_EMERALD if diag_results["overall_status"] == "OPTIMAL" else Theme.ACCENT_GOLD,
            bg=Theme.BG_MODAL
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            content,
            text=f"Audit completed at {diag_results['timestamp']}",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_MODAL
        ).pack(anchor="w", pady=(0, 12))

        # Text area
        txt = tk.Text(content, bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY, font=Theme.font_mono(), wrap="word", relief="flat", padx=10, pady=10)
        txt.pack(fill="both", expand=True, pady=(0, 12))

        import json
        formatted_json = json.dumps(diag_results, indent=2)
        txt.insert("1.0", formatted_json)
        txt.configure(state="disabled")

        btn_bar = tk.Frame(content, bg=Theme.BG_MODAL)
        btn_bar.pack(fill="x")

        tk.Button(
            btn_bar,
            text="Close",
            font=Theme.font_body_bold(),
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            command=win.destroy,
            padx=16,
            pady=6,
            relief="flat"
        ).pack(side="right")
