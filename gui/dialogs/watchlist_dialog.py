"""
M4DI~UciH4 Trading Intelligence System
Watchlist Management Modal Dialog — Enterprise Edition
Allows creating, renaming, deleting watchlists, adding/removing symbols,
setting institutional notes, configuring price alerts, and launching scanner.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional

from config.theme import Theme
from config.constants import SUPPORTED_MARKETS
from gui.components.tables import SortableTreeview
from gui.dialogs.confirm_dialog import ConfirmDialog
from core.logger import get_logger

logger = get_logger("WatchlistDialog")


class WatchlistDialog(tk.Toplevel):
    """Modal dialog for complete multi-watchlist and symbol lifecycle management"""

    def __init__(self, parent, app_context, on_watchlist_changed=None):
        super().__init__(parent)
        self.ctx = app_context
        self.on_watchlist_changed = on_watchlist_changed
        self.title("Watchlist & Symbol Surveillance Manager")
        self.geometry("820x560")
        self.configure(bg=Theme.BG_MODAL)
        self.transient(parent)
        self.grab_set()

        self._current_wl_id: Optional[int] = None
        self._build_ui()
        self._load_watchlists()

    def _build_ui(self):
        root_pad = tk.Frame(self, bg=Theme.BG_MODAL, padx=16, pady=16)
        root_pad.pack(fill="both", expand=True)

        # -------------------------------------------------------------
        # 1. Header Bar
        # -------------------------------------------------------------
        header = tk.Frame(root_pad, bg=Theme.BG_MODAL)
        header.pack(fill="x", pady=(0, 14))

        tk.Label(
            header,
            text="Multi-Watchlist Management",
            font=Theme.font_title(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_MODAL
        ).pack(side="left")

        tk.Label(
            header,
            text="Organize asset classes, configure price alert limits, and add trading thesis notes",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_MODAL
        ).pack(side="left", padx=(12, 0), pady=(4, 0))

        # -------------------------------------------------------------
        # 2. Watchlist Selector & Watchlist Actions Row
        # -------------------------------------------------------------
        wl_bar = tk.Frame(root_pad, bg=Theme.BG_CARD, padx=12, pady=10, highlightbackground=Theme.BORDER_SUBTLE, highlightthickness=1)
        wl_bar.pack(fill="x", pady=(0, 14))

        tk.Label(
            wl_bar,
            text="Active Watchlist:",
            font=Theme.font_body_bold(),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        ).pack(side="left", padx=(0, 8))

        self.wl_combo = ttk.Combobox(wl_bar, state="readonly", width=26, font=Theme.font_body())
        self.wl_combo.pack(side="left", padx=(0, 12))
        self.wl_combo.bind("<<ComboboxSelected>>", lambda e: self._on_select_watchlist())

        # Watchlist buttons
        tk.Button(
            wl_bar,
            text="➕ New Watchlist",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ACCENT_CYAN,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._on_create_watchlist
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            wl_bar,
            text="✏️ Rename",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.TEXT_PRIMARY,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._on_rename_watchlist
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            wl_bar,
            text="🗑️ Delete",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ACCENT_ROSE,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._on_delete_watchlist
        ).pack(side="left")

        # -------------------------------------------------------------
        # 3. Add Symbol Strip
        # -------------------------------------------------------------
        add_bar = tk.Frame(root_pad, bg=Theme.BG_CARD, padx=12, pady=8, highlightbackground=Theme.BORDER_SUBTLE, highlightthickness=1)
        add_bar.pack(fill="x", pady=(0, 10))

        tk.Label(add_bar, text="Add Symbol:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.ent_symbol = ttk.Entry(add_bar, width=12)
        self.ent_symbol.pack(side="left", padx=(0, 8))

        tk.Label(add_bar, text="Market:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.cmb_market = ttk.Combobox(add_bar, values=SUPPORTED_MARKETS, state="readonly", width=18)
        self.cmb_market.set(SUPPORTED_MARKETS[0])
        self.cmb_market.pack(side="left", padx=(0, 8))

        tk.Label(add_bar, text="Alert (> / <):", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.ent_alert = ttk.Entry(add_bar, width=12)
        self.ent_alert.pack(side="left", padx=(0, 8))

        tk.Button(
            add_bar,
            text="➕ Add to Pool",
            font=Theme.font_body_bold(),
            bg=Theme.ACCENT_EMERALD,
            fg="#080C13",
            relief="flat",
            padx=12,
            pady=3,
            cursor="hand2",
            command=self._on_add_symbol
        ).pack(side="left")

        # -------------------------------------------------------------
        # 4. Symbols Table
        # -------------------------------------------------------------
        self.table = SortableTreeview(
            root_pad,
            columns=["symbol", "market", "alert", "notes", "added"],
            headings=["Symbol", "Asset Class", "Price Alert Rule", "Institutional Notes", "Date Added"],
            widths=[90, 140, 120, 260, 110]
        )
        self.table.pack(fill="both", expand=True, pady=(0, 12))

        # -------------------------------------------------------------
        # 5. Bottom Actions Bar
        # -------------------------------------------------------------
        btm_bar = tk.Frame(root_pad, bg=Theme.BG_MODAL)
        btm_bar.pack(fill="x")

        tk.Button(
            btm_bar,
            text="✏️ Edit Notes",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD,
            fg=Theme.ACCENT_GOLD,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._on_edit_notes
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btm_bar,
            text="🔔 Update Alert Rule",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD,
            fg=Theme.ACCENT_TURQUOISE,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._on_edit_alert
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            btm_bar,
            text="🗑️ Remove Selected Symbol",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD,
            fg=Theme.ACCENT_ROSE,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._on_remove_symbol
        ).pack(side="left")

        tk.Button(
            btm_bar,
            text="Close",
            font=Theme.font_body_bold(),
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.destroy
        ).pack(side="right")

    def _load_watchlists(self, select_id: Optional[int] = None):
        """Fetch watchlists and populate combo"""
        wls = self.ctx.watchlists.get_watchlists()
        self._wl_cache = wls
        names = [f"{w['name']} ({w['symbol_count']} symbols)" for w in wls]
        self.wl_combo["values"] = names

        if wls:
            idx = 0
            if select_id is not None:
                for i, w in enumerate(wls):
                    if w["id"] == select_id:
                        idx = i
                        break
            self.wl_combo.current(idx)
            self._current_wl_id = wls[idx]["id"]
            self._load_symbols()
        else:
            self._current_wl_id = None
            self.table.clear()

    def _on_select_watchlist(self):
        idx = self.wl_combo.current()
        if idx >= 0 and idx < len(self._wl_cache):
            self._current_wl_id = self._wl_cache[idx]["id"]
            self._load_symbols()

    def _load_symbols(self):
        """Populate table with symbols of currently selected watchlist"""
        self.table.clear()
        if not self._current_wl_id:
            return

        symbols = self.ctx.watchlists.get_symbols(self._current_wl_id)
        for s in symbols:
            self.table.insert_row((
                s["symbol"],
                s["market"],
                s["alert_condition"] or "None",
                s["notes"] or "No notes",
                s["added_at"]
            ))

    def _on_create_watchlist(self):
        name = simpledialog.askstring("New Watchlist", "Enter unique watchlist name:", parent=self)
        if name and name.strip():
            ok, msg, wid = self.ctx.watchlists.create_watchlist(name.strip())
            if ok:
                self._load_watchlists(select_id=wid)
                if self.on_watchlist_changed:
                    self.on_watchlist_changed()
            else:
                messagebox.showerror("Error", msg, parent=self)

    def _on_rename_watchlist(self):
        if not self._current_wl_id:
            return
        old_name = self._wl_cache[self.wl_combo.current()]["name"]
        new_name = simpledialog.askstring("Rename Watchlist", f"Enter new name for '{old_name}':", parent=self)
        if new_name and new_name.strip():
            ok, msg = self.ctx.watchlists.rename_watchlist(self._current_wl_id, new_name.strip())
            if ok:
                self._load_watchlists(select_id=self._current_wl_id)
                if self.on_watchlist_changed:
                    self.on_watchlist_changed()
            else:
                messagebox.showerror("Error", msg, parent=self)

    def _on_delete_watchlist(self):
        if not self._current_wl_id:
            return
        wl_name = self._wl_cache[self.wl_combo.current()]["name"]
        confirm = ConfirmDialog(
            self,
            title="Delete Watchlist",
            message=f"Are you sure you want to permanently delete watchlist '{wl_name}' and all its tracked symbols?",
            confirm_label="Delete",
            is_danger=True
        )
        self.wait_window(confirm)
        if confirm.confirmed:
            ok, msg = self.ctx.watchlists.delete_watchlist(self._current_wl_id)
            if ok:
                self._load_watchlists()
                if self.on_watchlist_changed:
                    self.on_watchlist_changed()
            else:
                messagebox.showerror("Error", msg, parent=self)

    def _on_add_symbol(self):
        if not self._current_wl_id:
            return
        sym = self.ent_symbol.get().strip().upper()
        mkt = self.cmb_market.get().strip()
        alert = self.ent_alert.get().strip()

        if not sym:
            messagebox.showwarning("Validation Error", "Please enter a symbol ticker.", parent=self)
            return

        ok, msg = self.ctx.watchlists.add_symbol(
            watchlist_id=self._current_wl_id,
            symbol=sym,
            market=mkt,
            alert_condition=alert
        )
        if ok:
            self.ent_symbol.delete(0, "end")
            self.ent_alert.delete(0, "end")
            self._load_symbols()
            self._load_watchlists(select_id=self._current_wl_id)
            if self.on_watchlist_changed:
                self.on_watchlist_changed()
        else:
            messagebox.showerror("Error", msg, parent=self)

    def _on_remove_symbol(self):
        sel = self.table.get_selected_row()
        if not sel or not self._current_wl_id:
            messagebox.showinfo("Selection Required", "Please select a symbol from the table.", parent=self)
            return
        sym = sel[0]
        ok, msg = self.ctx.watchlists.remove_symbol(self._current_wl_id, sym)
        if ok:
            self._load_symbols()
            self._load_watchlists(select_id=self._current_wl_id)
            if self.on_watchlist_changed:
                self.on_watchlist_changed()
        else:
            messagebox.showerror("Error", msg, parent=self)

    def _on_edit_notes(self):
        sel = self.table.get_selected_row()
        if not sel or not self._current_wl_id:
            messagebox.showinfo("Selection Required", "Please select a symbol from the table.", parent=self)
            return
        sym = sel[0]
        current_notes = sel[3] if len(sel) > 3 and sel[3] != "No notes" else ""
        new_notes = simpledialog.askstring("Institutional Notes", f"Enter analysis notes for {sym}:", initialvalue=current_notes, parent=self)
        if new_notes is not None:
            self.ctx.watchlists.update_symbol_notes(self._current_wl_id, sym, new_notes)
            self._load_symbols()

    def _on_edit_alert(self):
        sel = self.table.get_selected_row()
        if not sel or not self._current_wl_id:
            messagebox.showinfo("Selection Required", "Please select a symbol from the table.", parent=self)
            return
        sym = sel[0]
        current_alert = sel[2] if len(sel) > 2 and sel[2] != "None" else ""
        new_alert = simpledialog.askstring(
            "Price Alert Condition",
            f"Enter price trigger for {sym} (e.g. '> 2650.00' or '< 2580.00', leave empty to clear):",
            initialvalue=current_alert,
            parent=self
        )
        if new_alert is not None:
            ok, msg = self.ctx.watchlists.set_symbol_alert(self._current_wl_id, sym, new_alert)
            if ok:
                self._load_symbols()
            else:
                messagebox.showerror("Invalid Format", msg, parent=self)
