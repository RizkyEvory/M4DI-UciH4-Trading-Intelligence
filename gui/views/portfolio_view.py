"""
M4DI~UciH4 Trading Intelligence System
Portfolio & Paper Trading Management GUI View — Enterprise Edition
Provides real-time mark-to-market equity telemetry, holdings surveillance,
risk exposure monitoring, order execution ledger, and paper trade entry dialog.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional

from config.theme import Theme
from config.constants import (
    SIDE_BUY,
    SIDE_SELL,
    POSITION_OPEN,
    TRADE_EXIT
)
from gui.components.cards import CardFrame, StatCard
from gui.components.tables import SortableTreeview
from portfolio.models import Position, TradeRecord, PortfolioSummary
from risk.position_sizer import PositionSizer
from utils.formatters import format_number


class PortfolioView(tk.Frame):
    """Institutional Portfolio Management & Paper Trading Execution Desk"""

    def __init__(self, parent, app_context, *args, **kwargs):
        super().__init__(parent, bg=Theme.BG_CONTENT, padx=20, pady=16, *args, **kwargs)
        self.ctx = app_context

        self._open_positions: List[Position] = []
        self._closed_trades: List[TradeRecord] = []
        self._summary: Optional[PortfolioSummary] = None

        self._build_ui()
        self.after(200, self._refresh_portfolio_data)

    def _build_ui(self):
        # 1. Header
        title_box = tk.Frame(self, bg=Theme.BG_CONTENT)
        title_box.pack(fill="x", pady=(0, 14))

        tk.Label(
            title_box,
            text="Portfolio & Paper Trading Management",
            font=Theme.font_title(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CONTENT
        ).pack(side="left")

        tk.Label(
            title_box,
            text="Real-time mark-to-market holdings, risk budgeting & simulated execution ledger",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CONTENT
        ).pack(side="left", padx=(12, 0), pady=(4, 0))

        tk.Label(
            title_box,
            text=" SIMULATION & RISK ENGINE ",
            font=(Theme.FONT_FAMILY, 8, "bold"),
            fg="#042F2E",
            bg=Theme.ACCENT_CYAN,
            padx=8,
            pady=3
        ).pack(side="right")

        # 2. Portfolio Telemetry Stat Cards
        stats_row = tk.Frame(self, bg=Theme.BG_CONTENT)
        stats_row.pack(fill="x", pady=(0, 14))
        stats_row.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="port_stats")

        self.card_equity = StatCard(stats_row, icon="💰", value="$100,000.00", label="Total Net Equity", status_text="Mark-to-Market", accent_color=Theme.ACCENT_CYAN)
        self.card_equity.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.card_cash = StatCard(stats_row, icon="💵", value="$100,000.00", label="Available Cash", status_text="Unallocated", accent_color=Theme.ACCENT_GOLD)
        self.card_cash.grid(row=0, column=1, sticky="nsew", padx=(0, 6))

        self.card_invested = StatCard(stats_row, icon="📊", value="$0.00", label="Invested Capital", status_text="Committed", accent_color=Theme.ACCENT_PURPLE)
        self.card_invested.grid(row=0, column=2, sticky="nsew", padx=(0, 6))

        self.card_unrealized = StatCard(stats_row, icon="📈", value="$0.00", label="Unrealized P/L", status_text="Open Risk", accent_color=Theme.SUCCESS)
        self.card_unrealized.grid(row=0, column=3, sticky="nsew", padx=(0, 6))

        self.card_realized = StatCard(stats_row, icon="🏆", value="$0.00", label="Realized P/L", status_text="Cumulative", accent_color=Theme.ACCENT_TURQUOISE)
        self.card_realized.grid(row=0, column=4, sticky="nsew", padx=(0, 6))

        self.card_return = StatCard(stats_row, icon="🚀", value="+0.00%", label="Total Return", status_text="Since Inception", accent_color=Theme.ACCENT_CYAN)
        self.card_return.grid(row=0, column=5, sticky="nsew")

        # 3. Action Toolbar & Risk Exposure
        act_card = CardFrame(self, title="Portfolio Actions & Institutional Risk Limits")
        act_card.pack(fill="x", pady=(0, 14))

        act_box = tk.Frame(act_card.body, bg=Theme.BG_CARD)
        act_box.pack(fill="x")

        # Buttons
        tk.Button(
            act_box,
            text="➕ New Paper Order",
            font=Theme.font_body_bold(),
            bg=Theme.ACCENT_CYAN,
            fg="#042F2E",
            activebackground=Theme.ACCENT_TURQUOISE,
            activeforeground="#042F2E",
            relief="flat",
            padx=12,
            pady=4,
            command=self._show_new_order_dialog
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            act_box,
            text="🔄 Refresh / MTM",
            font=Theme.font_body_bold(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.TEXT_PRIMARY,
            relief="flat",
            padx=10,
            pady=4,
            command=self._refresh_portfolio_data
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            act_box,
            text="❌ Close Selected Position",
            font=Theme.font_body_bold(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ERROR,
            relief="flat",
            padx=10,
            pady=4,
            command=self._close_selected_position
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            act_box,
            text="📥 Export Holdings",
            font=Theme.font_body_bold(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ACCENT_TURQUOISE,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._on_export_portfolio
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            act_box,
            text="📜 Export Trades",
            font=Theme.font_body_bold(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ACCENT_GOLD,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._on_export_trades
        ).pack(side="left", padx=(0, 8))

        # Exposure indicator pill
        self.lbl_exposure = tk.Label(
            act_box,
            text="EXPOSURE: 0.0% (Limit: 80.0%) | OPEN POSITIONS: 0 / 5",
            font=(Theme.FONT_FAMILY, 9, "bold"),
            fg=Theme.ACCENT_CYAN,
            bg=Theme.BG_CARD_ALT,
            padx=10,
            pady=4
        )
        self.lbl_exposure.pack(side="right")

        # 4. Notebook for Holdings, Trade History, and Risk Budget
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Tab A: Active Holdings Table
        tab_holdings = tk.Frame(self.notebook, bg=Theme.BG_CONTENT)
        self.notebook.add(tab_holdings, text="  Active Holdings & Positions  ")

        self.table_holdings = SortableTreeview(
            tab_holdings,
            columns=["id", "symbol", "side", "units", "entry", "curr", "cost", "value", "pnl", "ret", "sl", "tp", "opened"],
            headings=["ID", "Symbol", "Side", "Units", "Avg Entry", "Current", "Cost Basis", "Market Value", "Unrealized P/L", "Return %", "Stop Loss", "Take Profit", "Opened At"],
            widths=[65, 80, 55, 70, 75, 75, 85, 85, 95, 70, 75, 75, 110]
        )
        self.table_holdings.pack(fill="both", expand=True, pady=8)

        # Tag styles for table
        self.table_holdings.tree.tag_configure("buy", foreground=Theme.SUCCESS)
        self.table_holdings.tree.tag_configure("sell", foreground=Theme.ERROR)
        self.table_holdings.tree.tag_configure("gain", foreground=Theme.SUCCESS)
        self.table_holdings.tree.tag_configure("loss", foreground=Theme.ERROR)

        # Tab B: Trade Execution Ledger
        tab_trades = tk.Frame(self.notebook, bg=Theme.BG_CONTENT)
        self.notebook.add(tab_trades, text="  Executed Trades Ledger  ")

        self.table_trades = SortableTreeview(
            tab_trades,
            columns=["id", "symbol", "side", "units", "price", "fee", "pnl", "type", "timestamp"],
            headings=["Trade ID", "Symbol", "Side", "Units", "Fill Price", "Commission", "Realized P/L", "Action Type", "Timestamp"],
            widths=[80, 80, 60, 80, 80, 80, 95, 90, 130]
        )
        self.table_trades.pack(fill="both", expand=True, pady=8)

        # Tab C: Portfolio Allocation & Asset Breakdown
        tab_alloc = tk.Frame(self.notebook, bg=Theme.BG_CARD, padx=16, pady=16)
        self.notebook.add(tab_alloc, text="  Capital Allocation & Risk Exposure  ")

        tk.Label(
            tab_alloc,
            text="Institutional Capital Allocation Matrix",
            font=Theme.font_subtitle(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        ).pack(anchor="w", pady=(0, 10))

        self.lbl_alloc_summary = tk.Label(
            tab_alloc,
            text="• No open asset allocations.",
            font=Theme.font_body(),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD,
            justify="left",
            anchor="w"
        )
        self.lbl_alloc_summary.pack(anchor="w", pady=(0, 16))

        # Risk protocol guidelines card
        f_risk_info = tk.Frame(tab_alloc, bg=Theme.BG_CARD_ALT, padx=14, pady=12)
        f_risk_info.pack(fill="x")
        tk.Label(
            f_risk_info,
            text="Institutional Risk Management Mandate:\n"
                 "• Hard Stop Loss enforced on all positions prior to execution.\n"
                 "• Max Portfolio Capital Exposure bounded at 80% to maintain liquid cash cushion.\n"
                 "• Max Drawdown Circuit Breaker automatically halts new buying at 15% drawdown.\n"
                 "• Daily Loss Limit circuit breaker restricts intraday consecutive drawdowns to 3.0%.",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD_ALT,
            justify="left",
            anchor="w"
        ).pack(anchor="w")

    def _refresh_portfolio_data(self):
        """Fetch latest portfolio telemetry and populate views"""
        try:
            # 1. Update live quotes for open positions
            open_pos = self.ctx.portfolio.get_open_positions()
            if open_pos:
                price_map = {}
                for p in open_pos:
                    q = self.ctx.market_data.get_quote(p.symbol)
                    if q and q.last > 0:
                        price_map[p.symbol] = q.last
                if price_map:
                    self.ctx.portfolio.update_market_prices(price_map)

            # 2. Get summary
            summary = self.ctx.portfolio.get_portfolio_summary()
            self._summary = summary
            self._open_positions = self.ctx.portfolio.get_open_positions()
            self._closed_trades = self.ctx.portfolio.get_trade_history()

            # 3. Update Stat Cards
            self.card_equity.set_value(f"${summary.total_equity:,.2f}")
            self.card_cash.set_value(f"${summary.cash:,.2f}")
            self.card_invested.set_value(f"${summary.invested_capital:,.2f}")

            unreal_color = Theme.SUCCESS if summary.unrealized_pnl >= 0 else Theme.ERROR
            self.card_unrealized.set_value(f"${summary.unrealized_pnl:+,.2f}")
            self.card_unrealized.lbl_val.configure(fg=unreal_color)

            real_color = Theme.SUCCESS if summary.realized_pnl >= 0 else Theme.ERROR
            self.card_realized.set_value(f"${summary.realized_pnl:+,.2f}")
            self.card_realized.lbl_val.configure(fg=real_color)

            ret_sign = "+" if summary.total_return_pct >= 0 else ""
            ret_color = Theme.SUCCESS if summary.total_return_pct >= 0 else Theme.ERROR
            self.card_return.set_value(f"{ret_sign}{summary.total_return_pct:.2f}%")
            self.card_return.lbl_val.configure(fg=ret_color)

            # 4. Update Exposure Pill
            exp_text = f"EXPOSURE: {summary.exposure_pct:.1f}% (Limit: 80.0%) | OPEN POSITIONS: {summary.open_positions_count} / 5"
            self.lbl_exposure.configure(text=exp_text)

            # 5. Populate Holdings Table
            self.table_holdings.clear()
            for p in self._open_positions:
                side_tag = "buy" if p.side == SIDE_BUY else "sell"
                pnl_tag = "gain" if p.unrealized_pnl >= 0 else "loss"

                sl_str = f"{p.stop_loss:.4f}" if p.stop_loss else "-"
                tp_str = f"{p.take_profit:.4f}" if p.take_profit else "-"

                self.table_holdings.insert(
                    iid=p.id,
                    values=(
                        p.id,
                        p.symbol,
                        p.side,
                        f"{p.units:,.4f}",
                        f"${p.entry_price:,.4f}",
                        f"${p.current_price:,.4f}",
                        f"${p.cost_basis:,.2f}",
                        f"${p.market_value:,.2f}",
                        f"${p.unrealized_pnl:+,.2f}",
                        f"{p.unrealized_pnl_pct:+.2f}%",
                        sl_str,
                        tp_str,
                        p.opened_at.split()[0]
                    ),
                    tags=(side_tag, pnl_tag)
                )

            # 6. Populate Trades Ledger Table
            self.table_trades.clear()
            for t in self._closed_trades:
                pnl_str = f"${t.pnl:+,.2f}" if t.pnl != 0 else "$0.00"
                self.table_trades.insert(
                    iid=t.id,
                    values=(
                        t.id,
                        t.symbol,
                        t.side,
                        f"{t.units:,.4f}",
                        f"${t.price:,.4f}",
                        f"${t.fee:,.2f}",
                        pnl_str,
                        t.trade_type,
                        t.timestamp
                    )
                )

            # 7. Update Allocation Tab
            alloc_lines = []
            if summary.allocations:
                for sym, pct in summary.allocations.items():
                    alloc_lines.append(f"• {sym}: {pct:.1f}% of Total Equity")
            else:
                alloc_lines.append("• 100% Cash / No active market capital allocations.")
            self.lbl_alloc_summary.configure(text="\n".join(alloc_lines))

        except Exception as e:
            pass

    def _close_selected_position(self):
        """Close selected position in the holdings table"""
        selected = self.table_holdings.tree.selection()
        if not selected:
            messagebox.showinfo("Select Position", "Please select an open position from the holdings table to close.")
            return

        pos_id = selected[0]
        # Find position
        pos = next((p for p in self._open_positions if p.id == pos_id), None)
        if not pos:
            return

        if not messagebox.askyesno("Confirm Position Exit", f"Close {pos.side} position for {pos.units} {pos.symbol} at current market price ${pos.current_price:.4f}?"):
            return

        try:
            closed_pos, pnl = self.ctx.paper_trader.pm.close_position(
                position_id=pos_id,
                exit_price=pos.current_price,
                notes="Manual market close via Portfolio GUI"
            )
            messagebox.showinfo("Position Closed", f"Position [{pos_id}] closed.\nRealized P/L: ${pnl:+,.2f}")
            self._refresh_portfolio_data()
        except Exception as e:
            messagebox.showerror("Close Failed", f"Failed to close position: {e}")

    def _show_new_order_dialog(self):
        """Open Order Entry Modal Dialog with Live Position Sizing Calculator"""
        dlg = tk.Toplevel(self)
        dlg.title("New Paper Order & Institutional Position Sizer")
        dlg.geometry("520x620")
        dlg.configure(bg=Theme.BG_CONTENT)
        dlg.transient(self)
        dlg.grab_set()

        # Dialog Title
        tk.Label(
            dlg,
            text="New Paper Trade Execution",
            font=Theme.font_title(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CONTENT
        ).pack(anchor="w", padx=20, pady=(16, 4))

        tk.Label(
            dlg,
            text="Simulated paper order with mathematical risk sizing & capital governance",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CONTENT
        ).pack(anchor="w", padx=20, pady=(0, 14))

        form_f = tk.Frame(dlg, bg=Theme.BG_CARD, padx=16, pady=14)
        form_f.pack(fill="x", padx=20, pady=(0, 12))

        # Symbol
        tk.Label(form_f, text="Symbol:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=0, column=0, sticky="w", pady=4)
        var_symbol = tk.StringVar(value="XAU/USD")
        cb_sym = ttk.Combobox(form_f, textvariable=var_symbol, values=["XAU/USD", "EUR/USD", "GBP/USD", "USD/JPY", "AAPL", "NVDA", "TSLA", "BTC/USD"], width=12)
        cb_sym.grid(row=0, column=1, sticky="w", pady=4, padx=(10, 0))

        # Side (BUY / SELL)
        tk.Label(form_f, text="Order Side:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=1, column=0, sticky="w", pady=4)
        var_side = tk.StringVar(value=SIDE_BUY)
        cb_side = ttk.Combobox(form_f, textvariable=var_side, values=[SIDE_BUY, SIDE_SELL], state="readonly", width=12)
        cb_side.grid(row=1, column=1, sticky="w", pady=4, padx=(10, 0))

        # Entry Price
        tk.Label(form_f, text="Entry Price ($):", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=2, column=0, sticky="w", pady=4)
        var_entry = tk.StringVar(value="2650.00")
        entry_price_input = tk.Entry(form_f, textvariable=var_entry, font=Theme.font_body(), bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_CYAN, width=14)
        entry_price_input.grid(row=2, column=1, sticky="w", pady=4, padx=(10, 0))

        # Stop Loss
        tk.Label(form_f, text="Stop Loss ($):", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=3, column=0, sticky="w", pady=4)
        var_sl = tk.StringVar(value="2635.00")
        sl_input = tk.Entry(form_f, textvariable=var_sl, font=Theme.font_body(), bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_CYAN, width=14)
        sl_input.grid(row=3, column=1, sticky="w", pady=4, padx=(10, 0))

        # Take Profit
        tk.Label(form_f, text="Take Profit ($):", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=4, column=0, sticky="w", pady=4)
        var_tp = tk.StringVar(value="2680.00")
        tp_input = tk.Entry(form_f, textvariable=var_tp, font=Theme.font_body(), bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_CYAN, width=14)
        tp_input.grid(row=4, column=1, sticky="w", pady=4, padx=(10, 0))

        # Risk % per trade
        tk.Label(form_f, text="Risk % per Trade:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).grid(row=5, column=0, sticky="w", pady=4)
        var_risk_pct = tk.StringVar(value="1.0")
        risk_input = tk.Entry(form_f, textvariable=var_risk_pct, font=Theme.font_body(), bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_CYAN, width=14)
        risk_input.grid(row=5, column=1, sticky="w", pady=4, padx=(10, 0))

        # Live Calculation Preview Box
        calc_box = tk.LabelFrame(
            dlg,
            text=" Transparent Position Sizing Audit ",
            font=Theme.font_caption(),
            fg=Theme.ACCENT_CYAN,
            bg=Theme.BG_CARD_ALT,
            padx=12,
            pady=8
        )
        calc_box.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        lbl_calc_output = tk.Label(
            calc_box,
            text="Click 'Calculate Size' to compute mathematical position units.",
            font=Theme.font_caption(),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD_ALT,
            justify="left",
            wraplength=450,
            anchor="w"
        )
        lbl_calc_output.pack(fill="both", expand=True)

        current_sizing: List[Optional[PositionSizer]] = [None]

        def calculate_sizing_preview():
            try:
                e_p = float(var_entry.get())
                s_l = float(var_sl.get())
                t_p = float(var_tp.get()) if var_tp.get() else None
                r_pct = float(var_risk_pct.get())
                balance = self.ctx.portfolio.get_account_balance()

                sizing = PositionSizer.calculate_size(
                    account_balance=balance,
                    risk_pct=r_pct,
                    entry_price=e_p,
                    stop_loss=s_l,
                    take_profit=t_p
                )
                current_sizing[0] = sizing
                steps_txt = "\n".join(sizing.calculation_steps[:6])
                lbl_calc_output.configure(text=steps_txt)
            except Exception as ex:
                lbl_calc_output.configure(text=f"Calculation Error: {ex}")

        # Bind live recalculation
        for w in (entry_price_input, sl_input, tp_input, risk_input):
            w.bind("<KeyRelease>", lambda e: calculate_sizing_preview())

        # Calculate button
        tk.Button(
            form_f,
            text="📐 Recalculate Size",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ACCENT_CYAN,
            relief="flat",
            command=calculate_sizing_preview
        ).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        # Initial preview run
        calculate_sizing_preview()

        # Execute Order Button
        def execute_order():
            try:
                sym = var_symbol.get().strip().upper()
                side = var_side.get()
                e_p = float(var_entry.get())
                s_l = float(var_sl.get())
                t_p = float(var_tp.get()) if var_tp.get() else None
                r_pct = float(var_risk_pct.get())

                ok, msg, pos = self.ctx.paper_trader.execute_paper_order(
                    symbol=sym,
                    side=side,
                    entry_price=e_p,
                    stop_loss=s_l,
                    take_profit=t_p,
                    custom_risk_pct=r_pct,
                    notes="Manual order via Portfolio UI"
                )

                if ok:
                    messagebox.showinfo("Order Executed", msg)
                    dlg.destroy()
                    self._refresh_portfolio_data()
                else:
                    messagebox.showwarning("Risk Rejection", msg)

            except Exception as ex:
                messagebox.showerror("Execution Error", str(ex))

        tk.Button(
            dlg,
            text="🚀 Execute Paper Order",
            font=Theme.font_body_bold(),
            bg=Theme.ACCENT_CYAN,
            fg="#042F2E",
            relief="flat",
            pady=8,
            command=execute_order
        ).pack(fill="x", padx=20, pady=(0, 16))

    def _on_export_portfolio(self):
        """Export portfolio summary & holdings to JSON or CSV"""
        summary = self.ctx.portfolio.get_portfolio_summary()
        positions = self.ctx.portfolio.get_open_positions()
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Portfolio Holdings",
            defaultextension=".json",
            filetypes=[("JSON File", "*.json"), ("CSV Spreadsheet", "*.csv")]
        )
        if path:
            fmt = "csv" if path.endswith(".csv") else "json"
            ok, msg = self.ctx.exporter.export_portfolio(summary, positions, path, fmt=fmt)
            if ok:
                messagebox.showinfo("Export Successful", msg)
            else:
                messagebox.showerror("Export Failed", msg)

    def _on_export_trades(self):
        """Export executed paper trading transactions ledger to CSV or JSON"""
        trades = self.ctx.portfolio.get_trade_history(limit=500)
        if not trades:
            messagebox.showinfo("Export", "No executed trade history to export.")
            return

        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Trade Ledger",
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv"), ("JSON File", "*.json")]
        )
        if path:
            fmt = "json" if path.endswith(".json") else "csv"
            ok, msg = self.ctx.exporter.export_trade_history(trades, path, fmt=fmt)
            if ok:
                messagebox.showinfo("Export Successful", msg)
            else:
                messagebox.showerror("Export Failed", msg)
