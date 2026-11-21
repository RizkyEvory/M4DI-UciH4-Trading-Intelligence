"""
M4DI~UciH4 Trading Intelligence System
Trading Signals & Execution Engine GUI View — Enterprise Edition
Synthesizes Technical Indicators, Multi-Timeframe Confluence, and News Sentiment
into actionable institutional signals with Stop Loss, Take Profit 1 & 2, Risk/Reward,
transparent reasoning breakdowns, and real-time event alerts.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional

from config.theme import Theme
from config.constants import (
    SIGNAL_STRONG_BUY,
    SIGNAL_BUY,
    SIGNAL_NEUTRAL,
    SIGNAL_SELL,
    SIGNAL_STRONG_SELL,
    SIGNAL_TYPES,
    TIMEFRAMES,
    ALERT_TYPES,
    PAGE_CHARTS
)
from gui.components.cards import CardFrame, StatCard
from gui.components.tables import SortableTreeview
from signals.models import TradingSignal, SignalAlert


class SignalsView(tk.Frame):
    """Institutional Algorithmic Trading Signal Hub & Real-time Alert Monitor"""

    DEFAULT_WATCHLIST = ["XAU/USD", "EUR/USD", "GBP/USD", "USD/JPY", "AAPL", "NVDA", "MSFT", "TSLA"]

    def __init__(self, parent, app_context, *args, **kwargs):
        super().__init__(parent, bg=Theme.BG_CONTENT, padx=20, pady=16, *args, **kwargs)
        self.ctx = app_context

        self._signals_cache: Dict[str, TradingSignal] = {}
        self._filtered_signals: List[TradingSignal] = []
        self._selected_signal: Optional[TradingSignal] = None

        self._build_ui()
        # Register for real-time alert notifications
        if hasattr(self.ctx, "alerts") and self.ctx.alerts:
            self.ctx.alerts.register_listener(self._on_realtime_alert)

        # Initial signal scan
        self.after(300, self._scan_signals_background)

    def _build_ui(self):
        # 1. Header
        title_box = tk.Frame(self, bg=Theme.BG_CONTENT)
        title_box.pack(fill="x", pady=(0, 14))

        tk.Label(
            title_box,
            text="Institutional Trading Signal Engine",
            font=Theme.font_title(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CONTENT
        ).pack(side="left")

        tk.Label(
            title_box,
            text="Quantitative multi-model synthesis: Technicals, Confluence & News Intelligence",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CONTENT
        ).pack(side="left", padx=(12, 0), pady=(4, 0))

        tk.Label(
            title_box,
            text=" QUANTITATIVE SIGNAL MATRIX ",
            font=(Theme.FONT_FAMILY, 8, "bold"),
            fg="#042F2E",
            bg=Theme.ACCENT_CYAN,
            padx=8,
            pady=3
        ).pack(side="right")

        # 2. Metric Stat Cards
        stats_row = tk.Frame(self, bg=Theme.BG_CONTENT)
        stats_row.pack(fill="x", pady=(0, 14))
        stats_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="sig_stats")

        self.card_active = StatCard(stats_row, icon="🎯", value="0", label="Active Setups", status_text="Directional", accent_color=Theme.ACCENT_CYAN)
        self.card_active.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.card_strong_buy = StatCard(stats_row, icon="🚀", value="0", label="Strong Buy Setups", status_text="High Edge", accent_color=Theme.SUCCESS)
        self.card_strong_buy.grid(row=0, column=1, sticky="nsew", padx=(0, 8))

        self.card_strong_sell = StatCard(stats_row, icon="🔻", value="0", label="Strong Sell Setups", status_text="Distribution", accent_color=Theme.ERROR)
        self.card_strong_sell.grid(row=0, column=2, sticky="nsew", padx=(0, 8))

        self.card_avg_conf = StatCard(stats_row, icon="🛡️", value="0%", label="Avg Model Confidence", status_text="Multi-Model", accent_color=Theme.ACCENT_GOLD)
        self.card_avg_conf.grid(row=0, column=3, sticky="nsew")

        # 3. Scanner Controls & Filters
        ctrl_card = CardFrame(self, title="Signal Generation & Strategy Parameters")
        ctrl_card.pack(fill="x", pady=(0, 14))

        c_bar = tk.Frame(ctrl_card.body, bg=Theme.BG_CARD)
        c_bar.pack(fill="x")

        # Timeframe selector
        tk.Label(c_bar, text="Timeframe:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.var_tf = tk.StringVar(value="1d")
        cb_tf = ttk.Combobox(c_bar, textvariable=self.var_tf, values=["15m", "1h", "4h", "1d", "1w"], state="readonly", width=6)
        cb_tf.pack(side="left", padx=(0, 16))

        # Signal Type filter
        tk.Label(c_bar, text="Filter Signal:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.var_sig_filter = tk.StringVar(value="ALL")
        cb_filter = ttk.Combobox(c_bar, textvariable=self.var_sig_filter, values=["ALL"] + SIGNAL_TYPES, state="readonly", width=12)
        cb_filter.pack(side="left", padx=(0, 16))
        cb_filter.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        # Min Confidence threshold
        tk.Label(c_bar, text="Min Confidence:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.var_min_conf = tk.StringVar(value="40%")
        cb_conf = ttk.Combobox(c_bar, textvariable=self.var_min_conf, values=["0%", "40%", "50%", "60%", "70%", "80%"], state="readonly", width=6)
        cb_conf.pack(side="left", padx=(0, 16))
        cb_conf.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        # Alerts config button
        tk.Button(
            c_bar,
            text="🔔 Alert Rules",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.TEXT_PRIMARY,
            relief="flat",
            padx=8,
            pady=3,
            command=self._show_alerts_config_dialog
        ).pack(side="left", padx=(0, 8))

        # Export button
        tk.Button(
            c_bar,
            text="📥 Export",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ACCENT_TURQUOISE,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self._on_export_signals
        ).pack(side="left")

        # Scan Button
        self.btn_scan = tk.Button(
            c_bar,
            text="⚡ Run Quantitative Scan",
            font=Theme.font_body_bold(),
            bg=Theme.ACCENT_CYAN,
            fg="#042F2E",
            activebackground=Theme.ACCENT_TURQUOISE,
            activeforeground="#042F2E",
            relief="flat",
            padx=14,
            pady=4,
            command=self._scan_signals_background
        )
        self.btn_scan.pack(side="right")

        # 4. Main Split: Signals Table & Setup Inspector
        split = tk.PanedWindow(self, orient="horizontal", bg=Theme.BG_CONTENT, sashwidth=4, bd=0)
        split.pack(fill="both", expand=True)

        # Left: Signals Table
        left_card = CardFrame(split, title="Active Signal Matrix", subtitle="Click row to inspect thesis & SL/TP levels")
        split.add(left_card, minsize=520, stretch="always")

        self.table = SortableTreeview(
            left_card.body,
            columns=["symbol", "signal", "confidence", "score", "entry", "sl", "tp1", "tp2", "rr", "tf", "time"],
            headings=["Symbol", "Signal", "Conf", "Score", "Entry", "SL", "TP1", "TP2", "R:R", "TF", "Generated"],
            widths=[80, 95, 60, 55, 75, 75, 75, 75, 50, 45, 95]
        )
        self.table.pack(fill="both", expand=True)
        self.table.tree.bind("<<TreeviewSelect>>", self._on_table_select)

        # Tag configurations for colors
        self.table.tree.tag_configure("strong_buy", foreground="#00E5FF", font=(Theme.FONT_FAMILY, 9, "bold"))
        self.table.tree.tag_configure("buy", foreground=Theme.SUCCESS)
        self.table.tree.tag_configure("sell", foreground=Theme.ACCENT_GOLD)
        self.table.tree.tag_configure("strong_sell", foreground=Theme.ERROR, font=(Theme.FONT_FAMILY, 9, "bold"))
        self.table.tree.tag_configure("neutral", foreground=Theme.TEXT_MUTED)

        # Right: Institutional Setup Inspector Tabs
        right_card = CardFrame(split, title="Institutional Setup Inspector", subtitle="Auditable Score & Risk Breakdown")
        split.add(right_card, minsize=400, stretch="never")

        self.notebook = ttk.Notebook(right_card.body)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Reasons & Algorithmic Thesis
        tab_thesis = tk.Frame(self.notebook, bg=Theme.BG_CARD, padx=10, pady=10)
        self.notebook.add(tab_thesis, text="  Thesis & Drivers  ")

        self.lbl_thesis_title = tk.Label(
            tab_thesis,
            text="Select a signal to inspect its quantitative thesis",
            font=Theme.font_subtitle(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD,
            wraplength=360,
            justify="left",
            anchor="w"
        )
        self.lbl_thesis_title.pack(fill="x", pady=(0, 6))

        # Score & Conf pills row
        pill_row = tk.Frame(tab_thesis, bg=Theme.BG_CARD)
        pill_row.pack(fill="x", pady=(0, 8))

        self.lbl_pill_score = tk.Label(pill_row, text="SCORE: 0.0", font=(Theme.FONT_FAMILY, 8, "bold"), fg=Theme.TEXT_PRIMARY, bg=Theme.BG_CARD_ALT, padx=6, pady=2)
        self.lbl_pill_score.pack(side="left", padx=(0, 6))

        self.lbl_pill_conf = tk.Label(pill_row, text="CONFIDENCE: 0%", font=(Theme.FONT_FAMILY, 8, "bold"), fg=Theme.TEXT_PRIMARY, bg=Theme.BG_CARD_ALT, padx=6, pady=2)
        self.lbl_pill_conf.pack(side="left")

        # Scrollable Reasons Text
        self.txt_reasons = tk.Text(
            tab_thesis,
            font=Theme.font_caption(),
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            relief="flat",
            wrap="word",
            height=10
        )
        self.txt_reasons.pack(fill="both", expand=True, pady=(0, 8))
        self.txt_reasons.insert("1.0", "• Select a signal row from the table above.")
        self.txt_reasons.configure(state="disabled")

        # Action: Open in Charts
        self.btn_open_chart = tk.Button(
            tab_thesis,
            text="📈 Open Symbol in Interactive Chart",
            font=Theme.font_body_bold(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ACCENT_CYAN,
            activebackground=Theme.BG_SIDEBAR,
            activeforeground=Theme.ACCENT_TURQUOISE,
            relief="flat",
            pady=4,
            command=self._navigate_to_chart,
            state="disabled"
        )
        self.btn_open_chart.pack(fill="x")

        # Tab 2: Execution & Risk Management
        tab_risk = tk.Frame(self.notebook, bg=Theme.BG_CARD, padx=12, pady=12)
        self.notebook.add(tab_risk, text="  Risk & Execution  ")

        self.lbl_risk_summary = tk.Label(
            tab_risk,
            text="Entry & Stop Loss Protection Framework",
            font=Theme.font_subtitle(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD,
            anchor="w"
        )
        self.lbl_risk_summary.pack(fill="x", pady=(0, 10))

        # Risk parameters table/grid
        grid_f = tk.Frame(tab_risk, bg=Theme.BG_CARD_ALT, padx=10, pady=8)
        grid_f.pack(fill="x", pady=(0, 12))

        labels = [
            ("Entry Price:", "lbl_entry_val"),
            ("Stop Loss (SL):", "lbl_sl_val"),
            ("Take Profit 1 (1.5R):", "lbl_tp1_val"),
            ("Take Profit 2 (2.5R):", "lbl_tp2_val"),
            ("Risk / Reward Ratio:", "lbl_rr_val"),
        ]

        self.risk_val_labels = {}
        for r_idx, (text_label, var_name) in enumerate(labels):
            tk.Label(grid_f, text=text_label, font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD_ALT).grid(row=r_idx, column=0, sticky="w", pady=3)
            val_lbl = tk.Label(grid_f, text="-", font=Theme.font_body(), fg=Theme.TEXT_PRIMARY, bg=Theme.BG_CARD_ALT)
            val_lbl.grid(row=r_idx, column=1, sticky="e", padx=(20, 0), pady=3)
            self.risk_val_labels[var_name] = val_lbl

        # Capital risk advice
        tk.Label(
            tab_risk,
            text="Institutional Sizing Protocol:\n• Never risk > 1.0% account capital per setup.\n• Set SL hard on exchange/broker — avoid mental stops.\n• Partial out 50% at TP1 (1.5R) and trail stop to breakeven.",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD,
            justify="left",
            wraplength=350,
            anchor="w"
        ).pack(fill="x")

        # Tab 3: Real-Time Alerts Log
        tab_alerts = tk.Frame(self.notebook, bg=Theme.BG_CARD, padx=8, pady=8)
        self.notebook.add(tab_alerts, text="  Active Alerts (0)  ")

        self.txt_alerts = tk.Text(
            tab_alerts,
            font=Theme.font_caption(),
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            relief="flat",
            wrap="word",
            height=12
        )
        self.txt_alerts.pack(fill="both", expand=True, pady=(0, 6))
        self.txt_alerts.insert("1.0", "No alerts triggered yet.\nListening for RSI extremes, breakouts, and catalysts...")
        self.txt_alerts.configure(state="disabled")

        btn_clear_alerts = tk.Button(
            tab_alerts,
            text="Clear Alert History",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.TEXT_MUTED,
            relief="flat",
            command=self._clear_alerts_log
        )
        btn_clear_alerts.pack(side="right")

    def _scan_signals_background(self):
        """Batch evaluate watchlist symbols across MarketData & NewsEngine"""
        self.btn_scan.configure(text="⏳ Scanning Watchlist...", state="disabled")
        timeframe = self.var_tf.get()
        symbols = self.DEFAULT_WATCHLIST

        def task():
            results: Dict[str, TradingSignal] = {}
            for sym in symbols:
                try:
                    # 1. Fetch candles
                    candles = self.ctx.market_data.get_candles(sym, timeframe=timeframe, limit=80)
                    if not candles or len(candles) < 14:
                        continue

                    # 2. Fetch symbol news sentiment
                    news_profile = None
                    if hasattr(self.ctx, "news_engine") and self.ctx.news_engine:
                        news_profile = self.ctx.news_engine.get_symbol_sentiment(sym)

                    # 3. Generate Signal
                    sig = self.ctx.signals.generate_signal(
                        symbol=sym,
                        candles=candles,
                        timeframe=timeframe,
                        news_profile=news_profile
                    )
                    results[sym] = sig

                    # 4. Check real-time alerts
                    if hasattr(self.ctx, "alerts") and self.ctx.alerts:
                        self.ctx.alerts.check_signal_alerts(sig)
                        self.ctx.alerts.check_technical_alerts(sym, candles)

                except Exception as e:
                    logger.warning(f"Error evaluating signal for {sym}: {e}")
            return results

        def on_complete(results_dict):
            self.btn_scan.configure(text="⚡ Run Quantitative Scan", state="normal")
            if results_dict:
                self._signals_cache = results_dict
                self._apply_filters()

        def on_error(err):
            self.btn_scan.configure(text="⚡ Run Quantitative Scan", state="normal")
            messagebox.showwarning("Signal Scan Warning", f"Error scanning signals: {err}")

        self.ctx.tasks.submit_task(
            "BatchSignalScan",
            task,
            on_success=on_complete,
            on_error=on_error
        )

    def _apply_filters(self):
        """Filter cached signals by Type and Min Confidence"""
        filter_type = self.var_sig_filter.get()
        conf_str = self.var_min_conf.get().replace("%", "")
        min_conf = float(conf_str) if conf_str.isdigit() else 0.0

        filtered = []
        for sym, sig in self._signals_cache.items():
            if filter_type != "ALL" and sig.signal != filter_type:
                continue
            if sig.confidence < min_conf:
                continue
            filtered.append(sig)

        # Sort by absolute score descending (highest conviction setups first)
        filtered.sort(key=lambda s: abs(s.score), reverse=True)
        self._filtered_signals = filtered

        # Update stats
        total_sigs = len(self._signals_cache)
        active_count = sum(1 for s in self._signals_cache.values() if s.signal != SIGNAL_NEUTRAL)
        strong_buys = sum(1 for s in self._signals_cache.values() if s.signal == SIGNAL_STRONG_BUY)
        strong_sells = sum(1 for s in self._signals_cache.values() if s.signal == SIGNAL_STRONG_SELL)
        avg_c = round(sum(s.confidence for s in self._signals_cache.values()) / max(1, total_sigs))

        self.card_active.set_value(str(active_count))
        self.card_strong_buy.set_value(str(strong_buys))
        self.card_strong_sell.set_value(str(strong_sells))
        self.card_avg_conf.set_value(f"{avg_c}%")

        # Repopulate table
        self.table.clear()
        for idx, s in enumerate(filtered):
            tag = "neutral"
            if s.signal == SIGNAL_STRONG_BUY:
                tag = "strong_buy"
            elif s.signal == SIGNAL_BUY:
                tag = "buy"
            elif s.signal == SIGNAL_SELL:
                tag = "sell"
            elif s.signal == SIGNAL_STRONG_SELL:
                tag = "strong_sell"

            time_str = s.timestamp.split()[1][:5] if " " in s.timestamp else s.timestamp[:10]

            self.table.insert(
                iid=str(idx),
                values=(
                    s.symbol,
                    s.signal,
                    f"{s.confidence:.0f}%",
                    f"{s.score:+.1f}",
                    f"{s.entry_price:.2f}",
                    f"{s.stop_loss:.2f}",
                    f"{s.take_profit_1:.2f}",
                    f"{s.take_profit_2:.2f}",
                    f"1:{s.risk_reward:.1f}",
                    s.timeframe,
                    time_str
                ),
                tags=(tag,)
            )

        if filtered:
            self.table.tree.selection_set("0")
            self._on_table_select(None)
        else:
            self._clear_inspector()

    def _on_table_select(self, event):
        """User selected a signal row in treeview"""
        sel = self.table.tree.selection()
        if not sel:
            return

        try:
            idx = int(sel[0])
            if 0 <= idx < len(self._filtered_signals):
                sig = self._filtered_signals[idx]
                self._display_signal_detail(sig)
        except Exception:
            pass

    def _display_signal_detail(self, sig: TradingSignal):
        """Display setup thesis and risk numbers"""
        self._selected_signal = sig

        # Thesis tab
        self.lbl_thesis_title.configure(text=f"{sig.symbol} — {sig.signal} ({sig.timeframe.upper()})")

        score_color = Theme.SUCCESS if sig.score > 20 else (Theme.ERROR if sig.score < -20 else Theme.TEXT_MUTED)
        self.lbl_pill_score.configure(text=f"SCORE: {sig.score:+.1f}", fg=score_color)
        self.lbl_pill_conf.configure(text=f"CONFIDENCE: {sig.confidence:.1f}%")

        self.txt_reasons.configure(state="normal")
        self.txt_reasons.delete("1.0", "end")
        reasons_fmt = "\n".join([f"• {r}" for r in sig.reasons])
        self.txt_reasons.insert("1.0", reasons_fmt)
        self.txt_reasons.configure(state="disabled")

        self.btn_open_chart.configure(state="normal")

        # Risk tab
        self.risk_val_labels["lbl_entry_val"].configure(text=f"{sig.entry_price:.4f}")
        self.risk_val_labels["lbl_sl_val"].configure(text=f"{sig.stop_loss:.4f}", fg=Theme.ERROR)
        self.risk_val_labels["lbl_tp1_val"].configure(text=f"{sig.take_profit_1:.4f}", fg=Theme.SUCCESS)
        self.risk_val_labels["lbl_tp2_val"].configure(text=f"{sig.take_profit_2:.4f}", fg=Theme.ACCENT_CYAN)
        self.risk_val_labels["lbl_rr_val"].configure(text=f"1 : {sig.risk_reward:.2f}")

    def _clear_inspector(self):
        """Reset inspector widgets to empty state"""
        self._selected_signal = None
        self.lbl_thesis_title.configure(text="No signals match the current filter")
        self.lbl_pill_score.configure(text="SCORE: 0.0", fg=Theme.TEXT_MUTED)
        self.lbl_pill_conf.configure(text="CONFIDENCE: 0%")

        self.txt_reasons.configure(state="normal")
        self.txt_reasons.delete("1.0", "end")
        self.txt_reasons.insert("1.0", "• No signals available.")
        self.txt_reasons.configure(state="disabled")
        self.btn_open_chart.configure(state="disabled")

        for lbl in self.risk_val_labels.values():
            lbl.configure(text="-")

    def _on_realtime_alert(self, alert: SignalAlert):
        """Dispatched on real-time event alerts"""
        # Append to alerts tab
        self.txt_alerts.configure(state="normal")
        time_part = alert.timestamp.split()[1] if " " in alert.timestamp else alert.timestamp
        alert_line = f"[{time_part}] [{alert.severity}] {alert.symbol} ({alert.alert_type}): {alert.message}\n\n"
        self.txt_alerts.insert("1.0", alert_line)
        self.txt_alerts.configure(state="disabled")

        # Update notebook tab text
        alerts_count = len(self.ctx.alerts.get_recent_alerts())
        self.notebook.tab(2, text=f"  Active Alerts ({alerts_count})  ")

    def _clear_alerts_log(self):
        """Clear alerts text box and engine history"""
        if hasattr(self.ctx, "alerts") and self.ctx.alerts:
            self.ctx.alerts.clear_alerts()
        self.txt_alerts.configure(state="normal")
        self.txt_alerts.delete("1.0", "end")
        self.txt_alerts.insert("1.0", "Alert history cleared.\n")
        self.txt_alerts.configure(state="disabled")
        self.notebook.tab(2, text="  Active Alerts (0)  ")

    def _navigate_to_chart(self):
        """Navigate main window to ChartsView with selected symbol"""
        if not self._selected_signal:
            return
        sym = self._selected_signal.symbol
        # Navigate via Main window if available in widget hierarchy
        main_win = self.winfo_toplevel()
        if hasattr(main_win, "navigate_to"):
            main_win.navigate_to(PAGE_CHARTS)
            # Find charts view and set symbol
            if hasattr(main_win, "views") and PAGE_CHARTS in main_win.views:
                chart_view = main_win.views[PAGE_CHARTS]
                if hasattr(chart_view, "load_symbol"):
                    chart_view.load_symbol(sym)

    def _show_alerts_config_dialog(self):
        """Open modal dialog to configure alert rules"""
        dlg = tk.Toplevel(self)
        dlg.title("Configure Signal Alert Rules")
        dlg.geometry("400x380")
        dlg.configure(bg=Theme.BG_CONTENT)
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(
            dlg,
            text="Real-Time Event Alert Preferences",
            font=Theme.font_subtitle(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CONTENT
        ).pack(anchor="w", padx=20, pady=(16, 8))

        tk.Label(
            dlg,
            text="Toggle specific triggers to receive live notifications:",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CONTENT
        ).pack(anchor="w", padx=20, pady=(0, 12))

        f_rules = tk.Frame(dlg, bg=Theme.BG_CARD, padx=16, pady=12)
        f_rules.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        check_vars = {}
        for alert_type in ALERT_TYPES:
            curr_val = self.ctx.alerts.alert_configs.get(alert_type, True)
            var = tk.BooleanVar(value=curr_val)
            check_vars[alert_type] = var

            cb = tk.Checkbutton(
                f_rules,
                text=alert_type,
                variable=var,
                font=Theme.font_body(),
                fg=Theme.TEXT_PRIMARY,
                bg=Theme.BG_CARD,
                selectcolor=Theme.BG_SIDEBAR,
                activebackground=Theme.BG_CARD,
                activeforeground=Theme.ACCENT_CYAN
            )
            cb.pack(anchor="w", pady=3)

        def save_and_close():
            for at, var in check_vars.items():
                self.ctx.alerts.configure_alert(at, var.get())
            dlg.destroy()

        tk.Button(
            dlg,
            text="Save Preferences",
            font=Theme.font_body_bold(),
            bg=Theme.ACCENT_CYAN,
            fg="#042F2E",
            relief="flat",
            pady=6,
            command=save_and_close
        ).pack(fill="x", padx=20, pady=(0, 16))

    def _on_export_signals(self):
        """Export trading signals to CSV or JSON"""
        if not self._all_signals:
            messagebox.showinfo("Export", "No signals available to export. Run signal scan first.")
            return

        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Trading Signals",
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv"), ("JSON Data", "*.json")]
        )
        if path:
            fmt = "json" if path.endswith(".json") else "csv"
            ok, msg = self.ctx.exporter.export_trading_signals(self._all_signals, path, fmt=fmt)
            if ok:
                messagebox.showinfo("Export Successful", msg)
            else:
                messagebox.showerror("Export Failed", msg)
