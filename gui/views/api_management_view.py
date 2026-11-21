"""
M4DI~UciH4 Trading Intelligence System
API Management View — Multi-Provider Key Director, Rotation Strategies, Telemetry & Health
"""
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import Optional, Dict, Any

from config.constants import (
    API_PROVIDERS,
    PROVIDER_FINNHUB,
    PROVIDER_TWELVE_DATA,
    PROVIDER_NEWS_API,
    ROTATION_STRATEGIES,
    ROTATION_STRATEGY_LABELS,
    HEALTH_CONNECTED,
    HEALTH_DISCONNECTED,
    HEALTH_RATE_LIMITED,
    HEALTH_INVALID_KEY,
    HEALTH_ERROR
)
from config.theme import Theme
from gui.components.cards import CardFrame, StatCard
from gui.components.tables import SortableTreeview
from gui.dialogs.api_key_dialog import ApiKeyDialog
from gui.dialogs.confirm_dialog import ConfirmDialog
from utils.formatters import format_timestamp
from core.logger import get_app_logger

logger = get_app_logger("ApiManagementView")


class ApiManagementView(tk.Frame):
    """
    Advanced Multi-Key API Management Interface — Enterprise Edition.
    Features:
    - Real-time connection testing per key and per provider (background thread)
    - Dynamic key rotation strategy selection (Priority, Round-Robin, Least-Used, Failover)
    - Key Priority ordering (1-10)
    - Rate limit cooldown monitors & health telemetry counters
    - Encrypted local persistence with masked views
    """
    def __init__(self, parent, app_context, *args, **kwargs):
        super().__init__(parent, bg=Theme.BG_CONTENT, padx=20, pady=16, *args, **kwargs)
        self.ctx = app_context
        self._test_in_progress = False

        self._build_ui()
        self.refresh_table()

        # Listen for health and key events
        if hasattr(self.ctx, "events"):
            self.ctx.events.subscribe("PROVIDER_HEALTH_CHANGED", self._on_health_event)
            self.ctx.events.subscribe("API_KEY_STATUS_CHANGED", self._on_key_status_event)

    def _on_health_event(self, data):
        self.after(50, self.refresh_table)

    def _on_key_status_event(self, data):
        self.after(50, self.refresh_table)

    def _build_ui(self):
        # 1. Header Row
        title_box = tk.Frame(self, bg=Theme.BG_CONTENT)
        title_box.pack(fill="x", pady=(0, 14))

        tk.Label(
            title_box,
            text="API Key Director & Multi-Key Manager",
            font=Theme.font_title(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CONTENT
        ).pack(side="left")

        tk.Label(
            title_box,
            text="Intelligent Key Rotation, Rate-Limiting & Health Telemetry",
            font=Theme.font_caption(),
            fg=Theme.ACCENT_TURQUOISE,
            bg=Theme.BG_CONTENT
        ).pack(side="left", padx=(12, 0), pady=(4, 0))

        # 2. Provider Telemetry & Health Cards (3 Cards)
        summary_row = tk.Frame(self, bg=Theme.BG_CONTENT)
        summary_row.pack(fill="x", pady=(0, 14))
        summary_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="prov_cards")

        self.card_fh = StatCard(
            summary_row,
            icon="📊",
            value="0 Keys",
            label="Finnhub Stock & FX",
            status_text="Untested",
            accent_color=Theme.ACCENT_CYAN
        )
        self.card_fh.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.card_td = StatCard(
            summary_row,
            icon="📈",
            value="0 Keys",
            label="Twelve Data Multi-Asset",
            status_text="Untested",
            accent_color=Theme.ACCENT_TURQUOISE
        )
        self.card_td.grid(row=0, column=1, sticky="nsew", padx=(0, 10))

        self.card_na = StatCard(
            summary_row,
            icon="📰",
            value="0 Keys",
            label="NewsAPI Intelligence",
            status_text="Untested",
            accent_color=Theme.ACCENT_GOLD
        )
        self.card_na.grid(row=0, column=2, sticky="nsew")

        # 3. Rotation Strategy Selector Strip
        strat_card = CardFrame(self, title="API Key Rotation & Provider Director", subtitle="Configure failover and rotation policy per provider")
        strat_card.pack(fill="x", pady=(0, 12))

        strat_strip = tk.Frame(strat_card.body, bg=Theme.BG_CARD)
        strat_strip.pack(fill="x")

        # Provider Selector for Strategy
        tk.Label(strat_strip, text="Target Provider:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 8))
        self.strat_prov_var = tk.StringVar(value=API_PROVIDERS[0])
        self.strat_prov_combo = ttk.Combobox(
            strat_strip,
            textvariable=self.strat_prov_var,
            values=API_PROVIDERS,
            state="readonly",
            width=14,
            style="TCombobox"
        )
        self.strat_prov_combo.pack(side="left", padx=(0, 16))
        self.strat_prov_combo.bind("<<ComboboxSelected>>", self._on_strat_prov_changed)

        # Strategy Selector
        tk.Label(strat_strip, text="Active Strategy:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 8))
        self.strat_choice_var = tk.StringVar()
        self.strat_combo = ttk.Combobox(
            strat_strip,
            textvariable=self.strat_choice_var,
            values=[ROTATION_STRATEGY_LABELS[s] for s in ROTATION_STRATEGIES],
            state="readonly",
            width=36,
            style="TCombobox"
        )
        self.strat_combo.pack(side="left", padx=(0, 12))

        btn_apply_strat = ttk.Button(
            strat_strip,
            text="💾 Save Strategy",
            style="Primary.TButton",
            command=self._on_save_strategy
        )
        btn_apply_strat.pack(side="left")

        self.lbl_strat_status = tk.Label(strat_strip, text="", font=Theme.font_caption(), fg=Theme.ACCENT_EMERALD, bg=Theme.BG_CARD)
        self.lbl_strat_status.pack(side="left", padx=(12, 0))

        # 4. Main Keys Table & Action Toolbar
        main_card = CardFrame(self, title="Registered API Credentials & Live Health Matrix", subtitle="Priority-directed multi-key pool with automatic rate limit cooldowns")
        main_card.pack(fill="both", expand=True, pady=(0, 10))

        # Action Toolbar
        toolbar = tk.Frame(main_card.body, bg=Theme.BG_CARD)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(toolbar, text="➕ Add Key", style="Primary.TButton", command=self._on_add_key).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="✏️ Edit", style="Secondary.TButton", command=self._on_edit_key).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="🔄 Toggle State", style="Secondary.TButton", command=self._on_toggle_key).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="🗑️ Delete", style="Danger.TButton", command=self._on_delete_key).pack(side="left", padx=(0, 12))

        # Testing Buttons
        self.btn_test_key = ttk.Button(toolbar, text="🧪 Test Key", style="Secondary.TButton", command=self._on_test_key)
        self.btn_test_key.pack(side="left", padx=(0, 6))

        self.btn_test_prov = ttk.Button(toolbar, text="⚡ Test Provider", style="Secondary.TButton", command=self._on_test_provider)
        self.btn_test_prov.pack(side="left", padx=(0, 6))

        ttk.Button(toolbar, text="📜 Failover & Telemetry Logs", style="Secondary.TButton", command=self._show_failover_logs_dialog).pack(side="left", padx=(0, 6))

        self.lbl_test_spinner = tk.Label(toolbar, text="", font=Theme.font_caption(), fg=Theme.ACCENT_CYAN, bg=Theme.BG_CARD)
        self.lbl_test_spinner.pack(side="left", padx=(8, 0))

        ttk.Button(toolbar, text="↻ Refresh", style="Secondary.TButton", command=self.refresh_table).pack(side="right")

        # Sortable Keys Table
        self.table = SortableTreeview(
            main_card.body,
            columns=["id", "provider", "name", "priority", "masked_key", "status", "health", "cooldown", "last_used", "errors"],
            headings=["ID", "Provider", "Key Name", "Priority", "Masked Secret", "State", "Health", "Cooldown", "Last Used", "Req / Err"],
            widths=[40, 100, 130, 65, 170, 75, 95, 80, 125, 85]
        )
        self.table.pack(fill="both", expand=True)
        self.table.tree.bind("<Double-1>", lambda e: self._on_edit_key())

        # 5. Telemetry & Rotation Callout Banner
        callout = tk.Frame(self, bg=Theme.BG_CARD_ALT, padx=12, pady=8, highlightbackground=Theme.BORDER_SUBTLE, highlightthickness=1)
        callout.pack(fill="x")

        tk.Label(
            callout,
            text="⚡ Intelligent Engine Protocol:",
            font=Theme.font_body_bold(),
            fg=Theme.ACCENT_CYAN,
            bg=Theme.BG_CARD_ALT
        ).pack(side="left", padx=(0, 8))

        tk.Label(
            callout,
            text="HTTP 429 automatically triggers provider/key cooldowns • Rotation cycles according to policy • Exponential backoff guards network calls.",
            font=Theme.font_caption(),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD_ALT
        ).pack(side="left")

        # Initial strategy combo load
        self._on_strat_prov_changed()

    def _on_strat_prov_changed(self, event=None):
        prov = self.strat_prov_var.get()
        current_strat = self.ctx.key_rotation.get_strategy(prov)
        self.strat_choice_var.set(ROTATION_STRATEGY_LABELS.get(current_strat, ROTATION_STRATEGIES[0]))
        self.lbl_strat_status.config(text="")

    def _on_save_strategy(self):
        prov = self.strat_prov_var.get()
        chosen_label = self.strat_choice_var.get()
        strat_key = None
        for k, v in ROTATION_STRATEGY_LABELS.items():
            if v == chosen_label:
                strat_key = k
                break
        if strat_key:
            self.ctx.key_rotation.set_strategy(prov, strat_key)
            self.lbl_strat_status.config(text=f"✓ Saved for {prov}!", fg=Theme.ACCENT_EMERALD)
            self.after(2500, lambda: self.lbl_strat_status.config(text=""))
            self.refresh_table()

    def refresh_table(self):
        """Fetch all registered keys from SQLite and update table and stat cards"""
        self.table.clear()
        keys = self.ctx.api_keys.get_keys()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for k in keys:
            # Determine health string and tag
            raw_health = k["status"]
            cooldown_target = k["cooldown_until"]
            in_cooldown = cooldown_target and cooldown_target > now_str
            cooldown_display = "Active" if in_cooldown else "None"

            if in_cooldown:
                health_str = "⏳ Rate Limited"
                row_tag = "warning_tag"
            elif raw_health == "HEALTHY":
                health_str = "🟢 Healthy"
                row_tag = "active_tag"
            elif raw_health == "INVALID_KEY":
                health_str = "🔴 Invalid Key"
                row_tag = "danger_tag"
            elif raw_health == "ERROR":
                health_str = "⚠️ Error"
                row_tag = "warning_tag"
            else:
                health_str = "⚪ Untested"
                row_tag = "active_tag" if k["is_active"] else "disabled_tag"

            prio_display = f"P{k['priority']}"
            last_used_disp = format_timestamp(k["last_used_at"]) if k["last_used_at"] else "Never"
            err_stat_disp = f"{k['rate_limit_count']} / {k['error_count']}"

            self.table.insert_row(
                (
                    k["id"],
                    k["provider"],
                    k["name"],
                    prio_display,
                    k["masked_key"],
                    k["status_str"],
                    health_str,
                    cooldown_display,
                    last_used_disp,
                    err_stat_disp
                ),
                tags=(row_tag,)
            )

        # Update Summary Stat Cards with Live Health
        summary = self.ctx.api_keys.count_summary()
        by_prov = summary["by_provider"]

        for prov, card in [
            (PROVIDER_FINNHUB, self.card_fh),
            (PROVIDER_TWELVE_DATA, self.card_td),
            (PROVIDER_NEWS_API, self.card_na)
        ]:
            prov_stat = by_prov.get(prov, {"total": 0, "active": 0})
            health_info = self.ctx.health_monitor.get_health(prov)
            strat = self.ctx.key_rotation.get_strategy(prov)
            status_text = f"Health: {health_info['status']} • {strat.upper()}"
            card.update_value(
                f"{prov_stat['active']} / {prov_stat['total']}",
                status_text=status_text
            )

    def _get_selected_key_id(self) -> Optional[int]:
        selected = self.table.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select an API key from the table first.")
            return None
        item = self.table.tree.item(selected[0])
        return int(item["values"][0])

    def _on_add_key(self):
        dialog = ApiKeyDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            try:
                self.ctx.api_keys.add_key(
                    provider=dialog.result["provider"],
                    name=dialog.result["name"],
                    raw_key=dialog.result["raw_key"],
                    is_active=dialog.result["is_active"],
                    priority=dialog.result.get("priority", 1)
                )
                self.refresh_table()
            except Exception as e:
                messagebox.showerror("Error Adding Key", str(e))

    def _on_edit_key(self):
        key_id = self._get_selected_key_id()
        if not key_id:
            return

        key_data = self.ctx.api_keys.get_key_by_id(key_id)
        if not key_data:
            return

        dialog = ApiKeyDialog(self, edit_data=key_data)
        self.wait_window(dialog)

        if dialog.result:
            try:
                self.ctx.api_keys.update_key(
                    key_id=key_id,
                    name=dialog.result["name"],
                    raw_key=dialog.result["raw_key"],
                    is_active=dialog.result["is_active"],
                    priority=dialog.result.get("priority", 1)
                )
                self.refresh_table()
            except Exception as e:
                messagebox.showerror("Error Updating Key", str(e))

    def _on_toggle_key(self):
        key_id = self._get_selected_key_id()
        if not key_id:
            return
        self.ctx.api_keys.toggle_key_status(key_id)
        self.refresh_table()

    def _on_delete_key(self):
        key_id = self._get_selected_key_id()
        if not key_id:
            return

        key_data = self.ctx.api_keys.get_key_by_id(key_id)
        if not key_data:
            return

        confirm = ConfirmDialog(
            self,
            title="Delete API Key",
            message=f"Are you sure you want to permanently delete API key '{key_data['name']}' for {key_data['provider']}?",
            confirm_label="Delete",
            is_danger=True
        )
        self.wait_window(confirm)

        if confirm.confirmed:
            self.ctx.api_keys.delete_key(key_id)
            self.refresh_table()

    def _on_test_key(self):
        """Execute non-blocking test of selected key via TaskManager"""
        key_id = self._get_selected_key_id()
        if not key_id:
            return

        if self._test_in_progress:
            return

        self._test_in_progress = True
        self.lbl_test_spinner.config(text="Testing key connection...")

        def run_test():
            return self.ctx.api_keys.test_key_connection(key_id, app_context=self.ctx)

        def on_done(res):
            self._test_in_progress = False
            self.lbl_test_spinner.config(text="")
            self.refresh_table()
            if res.get("success"):
                messagebox.showinfo("Test Succeeded", res.get("message", "Connection OK"))
            else:
                messagebox.showwarning("Test Failed", res.get("message", "Connection Failed"))

        def on_err(err):
            self._test_in_progress = False
            self.lbl_test_spinner.config(text="")
            self.refresh_table()
            messagebox.showerror("Test Error", str(err))

        self.ctx.tasks.submit_task(
            "Test Key Connection",
            run_test,
            on_complete=on_done,
            on_error=on_err
        )

    def _on_test_provider(self):
        """Execute non-blocking test of active provider via rotation manager"""
        prov = self.strat_prov_var.get()
        if self._test_in_progress:
            return

        self._test_in_progress = True
        self.lbl_test_spinner.config(text=f"Testing {prov} pool...")

        def run_prov_test():
            if prov == PROVIDER_FINNHUB:
                client = self.ctx.finnhub
            elif prov == PROVIDER_TWELVE_DATA:
                client = self.ctx.twelve_data
            elif prov == PROVIDER_NEWS_API:
                client = self.ctx.newsapi
            else:
                return {"success": False, "message": f"Unknown provider {prov}"}

            ok = client.test_connection()
            return {"success": ok, "message": f"Successfully connected to {prov} pool!"}

        def on_done(res):
            self._test_in_progress = False
            self.lbl_test_spinner.config(text="")
            self.refresh_table()
            if res.get("success"):
                messagebox.showinfo("Provider Pool Healthy", res.get("message"))
            else:
                messagebox.showwarning("Provider Test Failed", res.get("message"))

        def on_err(err):
            self._test_in_progress = False
            self.lbl_test_spinner.config(text="")
            self.refresh_table()
            messagebox.showerror("Provider Test Failed", str(err))

        self.ctx.tasks.submit_task(
            f"Test Provider {prov}",
            run_prov_test,
            on_complete=on_done,
            on_error=on_err
        )

    def _show_failover_logs_dialog(self):
        """Display Failover and Request Telemetry Audit Modal"""
        win = tk.Toplevel(self)
        win.title("API Infrastructure & Key Failover Telemetry")
        win.geometry("780x520")
        win.configure(bg=Theme.BG_MODAL)
        win.transient(self)
        win.grab_set()

        pad = tk.Frame(win, bg=Theme.BG_MODAL, padx=16, pady=16)
        pad.pack(fill="both", expand=True)

        tk.Label(
            pad,
            text="API Key Failover & Request History",
            font=Theme.font_title(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_MODAL
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            pad,
            text="Real-time audit log of automated key rotation failovers, outbound HTTP requests, and provider errors",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_MODAL
        ).pack(anchor="w", pady=(0, 12))

        nb = ttk.Notebook(pad)
        nb.pack(fill="both", expand=True, pady=(0, 12))

        # Tab 1: Failovers
        tab_fo = tk.Frame(nb, bg=Theme.BG_CONTENT)
        nb.add(tab_fo, text="  Failover Events  ")
        tree_fo = SortableTreeview(
            tab_fo,
            columns=["timestamp", "provider", "from_key", "to_key", "reason"],
            headings=["Timestamp", "Provider", "From Key", "Switched To", "Trigger Reason"],
            widths=[130, 90, 110, 110, 220]
        )
        tree_fo.pack(fill="both", expand=True)

        failovers = self.ctx.health_monitor.get_failover_history(limit=50)
        if not failovers:
            tree_fo.insert_row(("-", "-", "No failovers recorded", "-", "-"), tags=("disabled_tag",))
        else:
            for fo in failovers:
                tree_fo.insert_row((fo["timestamp"], fo["provider"], fo["from_key"], fo["to_key"], fo["reason"]))

        # Tab 2: Requests Log
        tab_req = tk.Frame(nb, bg=Theme.BG_CONTENT)
        nb.add(tab_req, text="  Recent Requests  ")
        tree_req = SortableTreeview(
            tab_req,
            columns=["timestamp", "provider", "endpoint", "status", "latency"],
            headings=["Timestamp", "Provider", "Endpoint", "Status Code", "Latency (ms)"],
            widths=[130, 100, 260, 90, 90]
        )
        tree_req.pack(fill="both", expand=True)

        reqs = self.ctx.health_monitor.get_recent_requests(limit=50)
        if not reqs:
            tree_req.insert_row(("-", "-", "No requests dispatched yet", "-", "-"), tags=("disabled_tag",))
        else:
            for r in reqs:
                tree_req.insert_row((r["timestamp"], r["provider"], r["endpoint"], str(r["status_code"]), f"{r['response_time_ms']} ms"))

        # Tab 3: Errors Log
        tab_err = tk.Frame(nb, bg=Theme.BG_CONTENT)
        nb.add(tab_err, text="  Error Audit  ")
        tree_err = SortableTreeview(
            tab_err,
            columns=["timestamp", "provider", "endpoint", "error"],
            headings=["Timestamp", "Provider", "Endpoint", "Error Detail"],
            widths=[130, 100, 180, 270]
        )
        tree_err.pack(fill="both", expand=True)

        errs = self.ctx.health_monitor.get_recent_errors(limit=50)
        if not errs:
            tree_err.insert_row(("-", "-", "No provider errors recorded", "Clean status"), tags=("disabled_tag",))
        else:
            for e in errs:
                tree_err.insert_row((e["timestamp"], e["provider"], e["endpoint"], e.get("error_message", "-")))

        tk.Button(
            pad,
            text="Close",
            font=Theme.font_body_bold(),
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=win.destroy
        ).pack(side="right")
