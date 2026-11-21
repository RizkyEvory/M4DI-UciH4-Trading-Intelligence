"""
M4DI~UciH4 Trading Intelligence System
Quantitative Backtesting & Strategy Optimization GUI View — Enterprise Edition
Provides modular strategy selection, fee/slippage modeling, bar-by-bar anti-lookahead simulation,
interactive Canvas equity curves & drawdown charts, and full trade-by-trade audit logs.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional

from config.theme import Theme
from config.constants import (
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_RISK_PER_TRADE_PCT,
    DEFAULT_COMMISSION_PCT,
    DEFAULT_SLIPPAGE_PCT
)
from gui.components.cards import CardFrame, StatCard
from gui.components.tables import SortableTreeview
from backtesting.models import BacktestConfig, BacktestResult, BacktestTrade
from backtesting.backtest_engine import BacktestEngine
from backtesting.strategies import AVAILABLE_STRATEGIES


class BacktestingView(tk.Frame):
    """Institutional Strategy Backtest Laboratory & Performance Analytics Desk"""

    def __init__(self, parent, app_context, *args, **kwargs):
        super().__init__(parent, bg=Theme.BG_CONTENT, padx=20, pady=16, *args, **kwargs)
        self.ctx = app_context

        self._current_result: Optional[BacktestResult] = None

        self._build_ui()

    def _build_ui(self):
        # 1. Header
        title_box = tk.Frame(self, bg=Theme.BG_CONTENT)
        title_box.pack(fill="x", pady=(0, 14))

        tk.Label(
            title_box,
            text="Quantitative Strategy Backtesting Engine",
            font=Theme.font_title(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CONTENT
        ).pack(side="left")

        tk.Label(
            title_box,
            text="Anti-lookahead event simulation, slippage/fee friction & institutional risk metrics",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CONTENT
        ).pack(side="left", padx=(12, 0), pady=(4, 0))

        tk.Label(
            title_box,
            text=" STRATEGY OPTIMIZATION ENGINE ",
            font=(Theme.FONT_FAMILY, 8, "bold"),
            fg="#042F2E",
            bg=Theme.ACCENT_CYAN,
            padx=8,
            pady=3
        ).pack(side="right")

        # 2. Control Bar (Strategy & Parameters)
        ctrl_card = CardFrame(self, title="Backtest Configuration & Simulation Parameters")
        ctrl_card.pack(fill="x", pady=(0, 14))

        f_bar = tk.Frame(ctrl_card.body, bg=Theme.BG_CARD)
        f_bar.pack(fill="x")

        # Strategy selection
        tk.Label(f_bar, text="Strategy:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=4)
        self.var_strategy = tk.StringVar(value="Institutional Confluence")
        cb_strat = ttk.Combobox(f_bar, textvariable=self.var_strategy, values=list(AVAILABLE_STRATEGIES.keys()), state="readonly", width=22)
        cb_strat.grid(row=0, column=1, sticky="w", padx=(0, 14), pady=4)

        # Symbol selection
        tk.Label(f_bar, text="Symbol:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=0, column=2, sticky="w", padx=(0, 4), pady=4)
        self.var_symbol = tk.StringVar(value="XAU/USD")
        cb_sym = ttk.Combobox(f_bar, textvariable=self.var_symbol, values=["XAU/USD", "EUR/USD", "GBP/USD", "USD/JPY", "AAPL", "NVDA", "TSLA", "BTC/USD"], width=10)
        cb_sym.grid(row=0, column=3, sticky="w", padx=(0, 14), pady=4)

        # Timeframe
        tk.Label(f_bar, text="Timeframe:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=0, column=4, sticky="w", padx=(0, 4), pady=4)
        self.var_tf = tk.StringVar(value="1d")
        cb_tf = ttk.Combobox(f_bar, textvariable=self.var_tf, values=["15m", "1h", "4h", "1d", "1w"], state="readonly", width=6)
        cb_tf.grid(row=0, column=5, sticky="w", padx=(0, 14), pady=4)

        # Capital ($)
        tk.Label(f_bar, text="Capital ($):", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=0, column=6, sticky="w", padx=(0, 4), pady=4)
        self.var_capital = tk.StringVar(value="100000")
        tk.Entry(f_bar, textvariable=self.var_capital, font=Theme.font_body(), bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_CYAN, width=10).grid(row=0, column=7, sticky="w", padx=(0, 14), pady=4)

        # Second row: Risk, Fee, Slippage, Run button
        tk.Label(f_bar, text="Risk % / Trade:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=4)
        self.var_risk = tk.StringVar(value="1.0")
        tk.Entry(f_bar, textvariable=self.var_risk, font=Theme.font_body(), bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_CYAN, width=6).grid(row=1, column=1, sticky="w", padx=(0, 14), pady=4)

        tk.Label(f_bar, text="Commission %:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=1, column=2, sticky="w", padx=(0, 4), pady=4)
        self.var_fee = tk.StringVar(value="0.05")
        tk.Entry(f_bar, textvariable=self.var_fee, font=Theme.font_body(), bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_CYAN, width=6).grid(row=1, column=3, sticky="w", padx=(0, 14), pady=4)

        tk.Label(f_bar, text="Slippage %:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=1, column=4, sticky="w", padx=(0, 4), pady=4)
        self.var_slip = tk.StringVar(value="0.02")
        tk.Entry(f_bar, textvariable=self.var_slip, font=Theme.font_body(), bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_CYAN, width=6).grid(row=1, column=5, sticky="w", padx=(0, 14), pady=4)

        # Run Button
        self.btn_run = tk.Button(
            f_bar,
            text="⚡ Run Simulation",
            font=Theme.font_body_bold(),
            bg=Theme.ACCENT_CYAN,
            fg="#042F2E",
            activebackground=Theme.ACCENT_TURQUOISE,
            activeforeground="#042F2E",
            relief="flat",
            padx=14,
            pady=4,
            command=self._run_backtest_background
        )
        self.btn_run.grid(row=1, column=6, sticky="e", padx=(0, 6), pady=4)

        # Export Button
        self.btn_export = tk.Button(
            f_bar,
            text="📥 Export",
            font=Theme.font_body_bold(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ACCENT_TURQUOISE,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._on_export_backtest
        )
        self.btn_export.grid(row=1, column=7, sticky="e", pady=4)

        # 3. Performance StatCards (6 Metrics)
        stats_row = tk.Frame(self, bg=Theme.BG_CONTENT)
        stats_row.pack(fill="x", pady=(0, 14))
        stats_row.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="bt_stats")

        self.card_return = StatCard(stats_row, icon="📈", value="0.00%", label="Total Return", status_text="Net of Fees", accent_color=Theme.ACCENT_CYAN)
        self.card_return.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.card_winrate = StatCard(stats_row, icon="🎯", value="0.0%", label="Win Rate", status_text="0 Trades", accent_color=Theme.SUCCESS)
        self.card_winrate.grid(row=0, column=1, sticky="nsew", padx=(0, 6))

        self.card_pf = StatCard(stats_row, icon="⚖️", value="0.00", label="Profit Factor", status_text="Gross W/L", accent_color=Theme.ACCENT_GOLD)
        self.card_pf.grid(row=0, column=2, sticky="nsew", padx=(0, 6))

        self.card_maxdd = StatCard(stats_row, icon="🔻", value="0.00%", label="Max Drawdown", status_text="Peak-to-Trough", accent_color=Theme.ERROR)
        self.card_maxdd.grid(row=0, column=3, sticky="nsew", padx=(0, 6))

        self.card_sharpe = StatCard(stats_row, icon="🛡️", value="0.00", label="Sharpe Ratio", status_text="Annualized", accent_color=Theme.ACCENT_PURPLE)
        self.card_sharpe.grid(row=0, column=4, sticky="nsew", padx=(0, 6))

        self.card_expectancy = StatCard(stats_row, icon="💡", value="$0.00", label="Expectancy", status_text="Per Trade", accent_color=Theme.ACCENT_TURQUOISE)
        self.card_expectancy.grid(row=0, column=5, sticky="nsew")

        # 4. Notebook for Visualizer, Trade List, and Tear Sheet
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Equity Curve & Drawdown Chart (Canvas)
        tab_chart = tk.Frame(self.notebook, bg=Theme.BG_CARD, padx=8, pady=8)
        self.notebook.add(tab_chart, text="  Equity Curve & Underwater Drawdown  ")

        self.canvas = tk.Canvas(tab_chart, bg=Theme.BG_INPUT, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._draw_charts())

        # Tab 2: Detailed Trade Log Table
        tab_trades = tk.Frame(self.notebook, bg=Theme.BG_CONTENT)
        self.notebook.add(tab_trades, text="  Executed Trade Ledger  ")

        self.table_trades = SortableTreeview(
            tab_trades,
            columns=["id", "symbol", "side", "units", "entry_time", "entry_price", "exit_time", "exit_price", "net_pnl", "ret_pct", "r_mult", "reason"],
            headings=["#", "Symbol", "Side", "Units", "Entry Date", "Entry Price", "Exit Date", "Exit Price", "Net PnL ($)", "Return %", "R-Multiple", "Exit Reason"],
            widths=[45, 75, 55, 65, 110, 75, 110, 75, 85, 70, 70, 95]
        )
        self.table_trades.pack(fill="both", expand=True, pady=8)
        self.table_trades.tree.tag_configure("win", foreground=Theme.SUCCESS)
        self.table_trades.tree.tag_configure("loss", foreground=Theme.ERROR)

        # Tab 3: Institutional Tear Sheet
        tab_tearsheet = tk.Frame(self.notebook, bg=Theme.BG_CARD, padx=16, pady=16)
        self.notebook.add(tab_tearsheet, text="  Comprehensive Tear Sheet  ")

        self.lbl_tearsheet = tk.Label(
            tab_tearsheet,
            text="Run a simulation to generate the full institutional performance tear sheet.",
            font=Theme.font_body(),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD,
            justify="left",
            anchor="w"
        )
        self.lbl_tearsheet.pack(anchor="w")

    def _run_backtest_background(self):
        """Execute historical simulation in a thread-safe background task"""
        self.btn_run.configure(text="⏳ Simulating...", state="disabled")

        strat_name = self.var_strategy.get()
        sym = self.var_symbol.get().strip().upper()
        tf = self.var_tf.get()

        try:
            init_cap = float(self.var_capital.get())
            risk_pct = float(self.var_risk.get())
            comm_pct = float(self.var_fee.get())
            slip_pct = float(self.var_slip.get())
        except Exception:
            init_cap = DEFAULT_INITIAL_CAPITAL
            risk_pct = DEFAULT_RISK_PER_TRADE_PCT
            comm_pct = DEFAULT_COMMISSION_PCT
            slip_pct = DEFAULT_SLIPPAGE_PCT

        def task():
            # 1. Fetch historical candles
            candles = self.ctx.market_data.get_candles(sym, timeframe=tf, limit=120)
            if not candles or len(candles) < 35:
                raise ValueError(f"Insufficient historical data for {sym} ({len(candles) if candles else 0} bars). Need at least 35 bars.")

            # 2. Instantiate strategy
            strat_cls = AVAILABLE_STRATEGIES.get(strat_name)
            if not strat_cls:
                raise ValueError(f"Strategy '{strat_name}' not found.")
            strat = strat_cls()

            # 3. Configure and run engine
            cfg = BacktestConfig(
                initial_capital=init_cap,
                risk_per_trade_pct=risk_pct,
                commission_pct=comm_pct,
                slippage_pct=slip_pct
            )
            engine = BacktestEngine(config=cfg)
            result = engine.run(strat, candles, symbol=sym, timeframe=tf)
            return result

        def on_complete(result: BacktestResult):
            self.btn_run.configure(text="⚡ Run Simulation", state="normal")
            self._current_result = result
            self._update_display(result)

        def on_error(err):
            self.btn_run.configure(text="⚡ Run Simulation", state="normal")
            messagebox.showwarning("Backtest Error", str(err))

        self.ctx.tasks.submit_task(
            "StrategyBacktest",
            task,
            on_success=on_complete,
            on_error=on_error
        )

    def _update_display(self, res: BacktestResult):
        """Update metrics cards, tables, and render vector Canvas charts"""
        # 1. Update Metrics Cards
        ret_sign = "+" if res.total_return_pct >= 0 else ""
        self.card_return.set_value(f"{ret_sign}{res.total_return_pct:.2f}%")
        self.card_return.lbl_val.configure(fg=Theme.SUCCESS if res.total_return_pct >= 0 else Theme.ERROR)

        self.card_winrate.set_value(f"{res.win_rate:.1f}%")
        self.card_winrate.lbl_status.configure(text=f"{res.winning_trades}W / {res.losing_trades}L ({res.total_trades} Total)")

        self.card_pf.set_value(f"{res.profit_factor:.2f}")
        self.card_maxdd.set_value(f"{res.max_drawdown_pct:.2f}%")
        self.card_sharpe.set_value(f"{res.sharpe_ratio:.2f}")

        exp_color = Theme.SUCCESS if res.expectancy >= 0 else Theme.ERROR
        self.card_expectancy.set_value(f"${res.expectancy:+,.2f}")
        self.card_expectancy.lbl_val.configure(fg=exp_color)

        # 2. Populate Trade Table
        self.table_trades.clear()
        for t in res.trades:
            tag = "win" if t.net_pnl >= 0 else "loss"
            entry_t = t.entry_time.split()[0] if " " in t.entry_time else t.entry_time
            exit_t = t.exit_time.split()[0] if " " in t.exit_time else t.exit_time

            self.table_trades.insert(
                iid=str(t.trade_id),
                values=(
                    t.trade_id,
                    t.symbol,
                    t.side,
                    f"{t.units:.4f}",
                    entry_t,
                    f"${t.entry_price:,.2f}",
                    exit_t,
                    f"${t.exit_price:,.2f}",
                    f"${t.net_pnl:+,.2f}",
                    f"{t.return_pct:+.2f}%",
                    f"{t.r_multiple:+.2f}R",
                    t.exit_reason
                ),
                tags=(tag,)
            )

        # 3. Populate Tear Sheet Tab
        ts_text = (
            f"STRATEGY TEAR SHEET — {res.strategy_name.upper()} ({res.symbol} {res.timeframe})\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Initial Capital:        ${res.initial_capital:,.2f}\n"
            f"• Final Equity:           ${res.final_equity:,.2f}\n"
            f"• Total Net Return:       {ret_sign}{res.total_return_pct:.2f}%\n"
            f"• CAGR (Annualized):      {res.cagr:.2f}%\n"
            f"• Total Trades:           {res.total_trades} (Win: {res.winning_trades}, Loss: {res.losing_trades})\n"
            f"• Win Rate:               {res.win_rate:.2f}%\n"
            f"• Profit Factor:          {res.profit_factor:.2f}\n"
            f"• Sharpe Ratio:           {res.sharpe_ratio:.2f}\n"
            f"• Sortino Ratio:          {res.sortino_ratio:.2f}\n"
            f"• Maximum Drawdown:       {res.max_drawdown_pct:.2f}% (Underwater: {res.max_drawdown_duration} bars)\n"
            f"• Average Trade P/L:      ${res.avg_trade_pnl:+,.2f}\n"
            f"• Average Winning Trade:  ${res.avg_win:,.2f}\n"
            f"• Average Losing Trade:   ${res.avg_loss:,.2f}\n"
            f"• Expectancy per Trade:   ${res.expectancy:+,.2f}\n"
        )
        self.lbl_tearsheet.configure(text=ts_text, font=Theme.font_mono())

        # 4. Render Canvas Charts
        self._draw_charts()

    def _draw_charts(self):
        """Draw Equity Curve & Underwater Drawdown onto Tkinter Canvas"""
        if not self._current_result or not self._current_result.equity_curve:
            return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            return

        self.canvas.delete("all")

        eq_curve = self._current_result.equity_curve
        dd_curve = self._current_result.drawdown_curve or [0.0] * len(eq_curve)
        n = len(eq_curve)
        if n < 2:
            return

        # Split canvas: Top 65% for Equity, Bottom 35% for Drawdown
        eq_h = int(h * 0.62)
        dd_top = eq_h + 15
        dd_h = h - dd_top - 10

        pad_left = 60
        pad_right = 20
        plot_w = w - pad_left - pad_right

        # --- 1. Draw Equity Curve ---
        min_eq = min(eq_curve)
        max_eq = max(eq_curve)
        eq_range = max(1.0, max_eq - min_eq)

        # Baseline grid lines
        self.canvas.create_line(pad_left, 15, w - pad_right, 15, fill="#1E2B3E", dash=(2, 4))
        self.canvas.create_line(pad_left, eq_h, w - pad_right, eq_h, fill="#1E2B3E")
        self.canvas.create_text(pad_left - 8, 15, text=f"${max_eq:,.0f}", fill=Theme.TEXT_MUTED, font=Theme.font_caption(), anchor="e")
        self.canvas.create_text(pad_left - 8, eq_h, text=f"${min_eq:,.0f}", fill=Theme.TEXT_MUTED, font=Theme.font_caption(), anchor="e")
        self.canvas.create_text(pad_left, 5, text="CUMULATIVE STRATEGY EQUITY ($)", fill=Theme.ACCENT_CYAN, font=(Theme.FONT_FAMILY, 8, "bold"), anchor="w")

        # Plot equity path
        eq_coords = []
        for i, val in enumerate(eq_curve):
            x = pad_left + (i / (n - 1)) * plot_w
            y = eq_h - ((val - min_eq) / eq_range) * (eq_h - 25)
            eq_coords.extend([x, y])

        if len(eq_coords) >= 4:
            self.canvas.create_line(*eq_coords, fill=Theme.ACCENT_CYAN, width=2, smooth=True)

        # --- 2. Draw Underwater Drawdown Chart ---
        max_dd = max(dd_curve) if dd_curve else 0.0
        dd_range = max(1.0, max_dd)

        self.canvas.create_line(pad_left, dd_top, w - pad_right, dd_top, fill="#1E2B3E")
        self.canvas.create_line(pad_left, dd_top + dd_h, w - pad_right, dd_top + dd_h, fill="#1E2B3E", dash=(2, 4))
        self.canvas.create_text(pad_left - 8, dd_top, text="0.0%", fill=Theme.TEXT_MUTED, font=Theme.font_caption(), anchor="e")
        self.canvas.create_text(pad_left - 8, dd_top + dd_h, text=f"-{max_dd:.1f}%", fill=Theme.ERROR, font=Theme.font_caption(), anchor="e")
        self.canvas.create_text(pad_left, dd_top - 10, text="UNDERWATER DRAWDOWN (%)", fill=Theme.ERROR, font=(Theme.FONT_FAMILY, 8, "bold"), anchor="w")

        # Plot drawdown bars/fill
        for i, dd_val in enumerate(dd_curve):
            x = pad_left + (i / (n - 1)) * plot_w
            bar_len = (dd_val / dd_range) * dd_h
            if bar_len > 0:
                self.canvas.create_line(x, dd_top, x, dd_top + bar_len, fill="#F43F5E", width=max(1, int(plot_w / n)))

    def _on_export_backtest(self):
        """Export backtest results & tear sheet to JSON or CSV"""
        if not self._last_result:
            messagebox.showinfo("Export", "No backtesting results available. Run simulation first.")
            return

        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Backtest Results & Tear Sheet",
            defaultextension=".json",
            filetypes=[("JSON File", "*.json"), ("CSV Trades", "*.csv")]
        )
        if path:
            fmt = "csv" if path.endswith(".csv") else "json"
            ok, msg = self.ctx.exporter.export_backtest_results(self._last_result, path, fmt=fmt)
            if ok:
                messagebox.showinfo("Export Successful", msg)
            else:
                messagebox.showerror("Export Failed", msg)
