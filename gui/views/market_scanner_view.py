"""
M4DI~UciH4 Trading Intelligence System
Market Scanner View — Multi-Asset Surveillance & Quantitative Screener
Features: Sortable Technical Matrix, Filters (Trend, RSI, Volatility), Search, Watchlists, and Chart Deep-Linking.
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import Optional, List, Dict, Any

from config.constants import (
    TF_15M, TF_1H, TF_4H, TF_1D,
    PAGE_CHARTS
)
from config.theme import Theme
from gui.components.cards import CardFrame, StatCard
from gui.components.tables import SortableTreeview
from utils.formatters import format_number
from core.logger import get_app_logger

logger = get_app_logger("MarketScannerView")


class MarketScannerView(tk.Frame):
    """
    Quantitative Multi-Asset Market Scanner — Enterprise Edition.
    Evaluates real-time feeds, computes complete indicator suites, and ranks instruments by Technical Score.
    """

    def __init__(self, parent, app_context, *args, **kwargs):
        super().__init__(parent, bg=Theme.BG_CONTENT, padx=20, pady=16, *args, **kwargs)
        self.ctx = app_context
        self._is_scanning = False
        self._scan_results: List[Dict[str, Any]] = []

        self._build_ui()
        self.load_watchlists()
        # Automatically run initial scan
        self.after(500, self._on_start_scan)

    def _build_ui(self):
        # 1. Header Row
        title_box = tk.Frame(self, bg=Theme.BG_CONTENT)
        title_box.pack(fill="x", pady=(0, 14))

        tk.Label(
            title_box,
            text="Market Scanner & Technical Matrix",
            font=Theme.font_title(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CONTENT
        ).pack(side="left")

        tk.Label(
            title_box,
            text="Multi-factor institutional screener (Trend, Momentum, Volatility & Technical Score)",
            font=Theme.font_caption(),
            fg=Theme.ACCENT_TURQUOISE,
            bg=Theme.BG_CONTENT
        ).pack(side="left", padx=(12, 0), pady=(4, 0))

        # Status Badge
        tk.Label(
            title_box,
            text=" REAL-TIME SCANNER ENGINE ",
            font=(Theme.FONT_FAMILY, 8, "bold"),
            fg="#042F2E",
            bg=Theme.ACCENT_TURQUOISE,
            padx=8,
            pady=3
        ).pack(side="right")

        # 2. Scanner Metrics Summary Cards (3 Cards)
        summary_row = tk.Frame(self, bg=Theme.BG_CONTENT)
        summary_row.pack(fill="x", pady=(0, 14))
        summary_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="sc_cards")

        self.card_bulls = StatCard(
            summary_row,
            icon="🟢",
            value="0 Bulls",
            label="Bullish Opportunities",
            status_text="Score >= 65",
            accent_color=Theme.ACCENT_EMERALD
        )
        self.card_bulls.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.card_bears = StatCard(
            summary_row,
            icon="🔴",
            value="0 Bears",
            label="Bearish Opportunities",
            status_text="Score <= 35",
            accent_color=Theme.ACCENT_ROSE
        )
        self.card_bears.grid(row=0, column=1, sticky="nsew", padx=(0, 10))

        self.card_vol = StatCard(
            summary_row,
            icon="⚡",
            value="0 Surges",
            label="High Volatility / RVOL",
            status_text="Regime: High / Extreme",
            accent_color=Theme.ACCENT_GOLD
        )
        self.card_vol.grid(row=0, column=2, sticky="nsew")

        # 3. Filter & Controls Toolbar Card
        filter_card = CardFrame(self, title="Surveillance Parameters & Quantitative Filters", subtitle="Select target watchlist pool, timeframe, and technical conditions")
        filter_card.pack(fill="x", pady=(0, 12))

        filter_body = filter_card.body

        # Row 1: Target Watchlist & Timeframe
        r1 = tk.Frame(filter_body, bg=Theme.BG_CARD)
        r1.pack(fill="x", pady=(0, 8))

        tk.Label(r1, text="Watchlist Pool:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.wl_var = tk.StringVar(value="All Watchlists")
        self.wl_combo = ttk.Combobox(r1, textvariable=self.wl_var, state="readonly", width=18, style="TCombobox")
        self.wl_combo.pack(side="left", padx=(0, 8))

        tk.Button(
            r1,
            text="⚙️ Watchlists",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ACCENT_CYAN,
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
            command=self._on_open_watchlist_manager
        ).pack(side="left", padx=(0, 16))

        tk.Label(r1, text="Scan Timeframe:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.tf_var = tk.StringVar(value=TF_1D)
        self.tf_combo = ttk.Combobox(r1, textvariable=self.tf_var, values=[TF_15M, TF_1H, TF_4H, TF_1D], state="readonly", width=8, style="TCombobox")
        self.tf_combo.pack(side="left", padx=(0, 16))

        tk.Label(r1, text="Search Symbol:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(r1, textvariable=self.search_var, width=12, style="TEntry")
        self.search_entry.pack(side="left", padx=(0, 16))
        self.search_entry.bind("<KeyRelease>", lambda e: self._apply_filters())

        # Row 2: Trend, RSI, Volatility Filters
        r2 = tk.Frame(filter_body, bg=Theme.BG_CARD)
        r2.pack(fill="x")

        tk.Label(r2, text="Trend Filter:", font=Theme.font_caption(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.trend_filter_var = tk.StringVar(value="ALL")
        self.trend_combo = ttk.Combobox(r2, textvariable=self.trend_filter_var, values=["ALL", "BULLISH", "BEARISH", "NEUTRAL"], state="readonly", width=10, style="TCombobox")
        self.trend_combo.pack(side="left", padx=(0, 14))
        self.trend_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        tk.Label(r2, text="RSI Regime:", font=Theme.font_caption(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.rsi_filter_var = tk.StringVar(value="ALL")
        self.rsi_combo = ttk.Combobox(r2, textvariable=self.rsi_filter_var, values=["ALL", "Oversold (<35)", "Overbought (>65)", "Neutral (35-65)"], state="readonly", width=16, style="TCombobox")
        self.rsi_combo.pack(side="left", padx=(0, 14))
        self.rsi_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        tk.Label(r2, text="Volatility:", font=Theme.font_caption(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.vol_filter_var = tk.StringVar(value="ALL")
        self.vol_combo = ttk.Combobox(r2, textvariable=self.vol_filter_var, values=["ALL", "LOW", "NORMAL", "HIGH", "EXTREME"], state="readonly", width=10, style="TCombobox")
        self.vol_combo.pack(side="left", padx=(0, 16))
        self.vol_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        # Action Buttons
        self.btn_scan = ttk.Button(r2, text="▶ Run Scanner", style="Primary.TButton", command=self._on_start_scan)
        self.btn_scan.pack(side="left", padx=(0, 8))

        btn_chart = ttk.Button(r2, text="📈 Open in Chart", style="Secondary.TButton", command=self._on_open_selected_chart)
        btn_chart.pack(side="left", padx=(0, 8))

        tk.Button(
            r2,
            text="📥 Export",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ACCENT_TURQUOISE,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self._on_export_results
        ).pack(side="left", padx=(0, 8))

        self.lbl_scan_status = tk.Label(r2, text="", font=Theme.font_caption(), fg=Theme.ACCENT_CYAN, bg=Theme.BG_CARD)
        self.lbl_scan_status.pack(side="left", padx=(8, 0))

        # 4. Results Matrix Table
        main_card = CardFrame(self, title="Market Surveillance Results", subtitle="Double click any instrument row to instantly open in interactive candlestick chart")
        main_card.pack(fill="both", expand=True, pady=(0, 10))

        self.table = SortableTreeview(
            main_card.body,
            columns=["symbol", "price", "change", "volume", "rvol", "rsi", "trend", "macd", "volatility", "score"],
            headings=["Symbol", "Last Price", "24h Change", "Volume", "RVOL", "RSI (14)", "Trend Bias", "MACD", "Volatility", "Tech Score"],
            widths=[85, 90, 85, 80, 60, 65, 120, 80, 85, 85]
        )
        self.table.pack(fill="both", expand=True)
        self.table.tree.bind("<Double-1>", lambda e: self._on_open_selected_chart())

    def load_watchlists(self):
        """Populate Watchlist dropdown from database"""
        try:
            rows = self.ctx.db.fetchall("SELECT name FROM watchlists ORDER BY id ASC")
            wl_names = ["All Watchlists"] + [r[0] for r in rows]
            self.wl_combo.config(values=wl_names)
        except Exception:
            pass

    def _on_start_scan(self):
        if self._is_scanning:
            return

        self._is_scanning = True
        self.btn_scan.config(state="disabled")
        self.lbl_scan_status.config(text="Scanning instruments...", fg=Theme.ACCENT_CYAN)

        chosen_wl = self.wl_var.get()
        tf = self.tf_var.get()

        def scan_task():
            # Get symbols from database
            if chosen_wl == "All Watchlists":
                symbols_info = self.ctx.market_data.get_watchlist_symbols()
            else:
                symbols_info = self.ctx.market_data.get_watchlist_symbols(watchlist_name=chosen_wl)

            symbols = [item["symbol"] for item in symbols_info]
            if not symbols:
                symbols = ["XAU/USD", "EUR/USD", "GBP/USD", "BTC/USD", "AAPL", "NVDA", "US30", "NAS100"]

            # Run batch scan
            results = self.ctx.scanner.scan_symbols(symbols, timeframe=tf)
            return results

        def on_done(results):
            self._is_scanning = False
            self.btn_scan.config(state="normal")
            self._scan_results = results
            self._apply_filters()
            self.lbl_scan_status.config(text=f"✓ Scanned {len(results)} instruments", fg=Theme.ACCENT_EMERALD)

        def on_err(err):
            self._is_scanning = False
            self.btn_scan.config(state="normal")
            self.lbl_scan_status.config(text=f"Scan failed: {err}", fg=Theme.ACCENT_ROSE)
            messagebox.showerror("Scanner Error", str(err))

        self.ctx.tasks.submit_task(
            "Market Scanner Run",
            scan_task,
            on_complete=on_done,
            on_error=on_err
        )

    def _apply_filters(self):
        """Filter memory results and populate treeview"""
        self.table.clear()
        if not self._scan_results:
            return

        search_q = self.search_var.get().strip().upper()
        trend_q = self.trend_filter_var.get()
        rsi_q = self.rsi_filter_var.get()
        vol_q = self.vol_filter_var.get()

        filtered = []
        bull_count = 0
        bear_count = 0
        vol_surge_count = 0

        for r in self._scan_results:
            sym = r["symbol"].upper()
            if search_q and search_q not in sym:
                continue

            # Trend Filter
            if trend_q != "ALL" and trend_q not in r["trend"]:
                continue

            # RSI Filter
            rsi_val = r["rsi"]
            if "Oversold" in rsi_q and rsi_val >= 35.0:
                continue
            if "Overbought" in rsi_q and rsi_val <= 65.0:
                continue
            if "Neutral" in rsi_q and (rsi_val < 35.0 or rsi_val > 65.0):
                continue

            # Volatility Filter
            if vol_q != "ALL" and r["volatility"] != vol_q:
                continue

            filtered.append(r)

            if r["technical_score"] >= 65.0:
                bull_count += 1
            elif r["technical_score"] <= 35.0:
                bear_count += 1

            if r["volatility"] in ("HIGH", "EXTREME") or r["rvol"] >= 1.8:
                vol_surge_count += 1

        # Update StatCards
        self.card_bulls.update_value(f"{bull_count} Bulls", status_text=f"{len(filtered)} Matched")
        self.card_bears.update_value(f"{bear_count} Bears", status_text=f"{len(filtered)} Matched")
        self.card_vol.update_value(f"{vol_surge_count} Surges", status_text="High Vol / Breakout")

        # Populate Table
        for r in filtered:
            chg = r["change_percent"]
            chg_sign = "+" if chg >= 0 else ""
            row_tag = "active_tag" if chg >= 0 else "danger_tag"

            self.table.insert_row(
                (
                    r["symbol"],
                    f"{r['price']:.2f}",
                    f"{chg_sign}{chg:.2f}%",
                    format_number(r["volume"]),
                    f"{r['rvol']:.1f}x",
                    f"{r['rsi']:.1f}",
                    r["trend"],
                    r["macd_status"],
                    r["volatility"],
                    f"{r['technical_score']:.1f}"
                ),
                tags=(row_tag,)
            )

    def _on_open_selected_chart(self):
        """Open the currently selected instrument inside the interactive ChartsView"""
        selected = self.table.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a row in the scanner table first.")
            return

        item = self.table.tree.item(selected[0])
        symbol = item["values"][0]

        # Navigate to Charts page
        main_win = self.winfo_toplevel()
        if hasattr(main_win, "navigate_to"):
            main_win.navigate_to(PAGE_CHARTS)
            chart_view = main_win._view_instances.get(PAGE_CHARTS)
            if chart_view:
                chart_view.sym_var.set(symbol)
                chart_view.current_symbol = symbol
                chart_view.load_symbol_candles(symbol, chart_view.current_timeframe)

    def _on_open_watchlist_manager(self):
        """Open the interactive Watchlist management dialog"""
        from gui.dialogs.watchlist_dialog import WatchlistDialog
        WatchlistDialog(self, self.ctx, on_watchlist_changed=self.load_watchlists)

    def _on_export_results(self):
        """Export scanner results to CSV or JSON"""
        if not self._scan_results:
            messagebox.showinfo("Export", "No scanner results to export. Run scanner first.")
            return

        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Market Scanner Data",
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv"), ("JSON Data", "*.json")]
        )
        if path:
            fmt = "json" if path.endswith(".json") else "csv"
            ok, msg = self.ctx.exporter.export_scanner_results(self._scan_results, path, fmt=fmt)
            if ok:
                messagebox.showinfo("Export Successful", msg)
            else:
                messagebox.showerror("Export Failed", msg)
