"""
M4DI~UciH4 Trading Intelligence System
Audit & System Logs View — Filter, Search, and Event Surveillance
"""
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from typing import Optional

from config.theme import Theme
from gui.components.cards import CardFrame
from gui.components.tables import SortableTreeview
from gui.dialogs.confirm_dialog import ConfirmDialog
from core.logger import get_app_logger

logger = get_app_logger("LogsView")


class LogsView(tk.Frame):
    """
    Real-time Audit & System Logs Surveillance.
    Allows filtering by Level, Module, keyword searching, clearing logs,
    and exporting logs to a text file.
    """
    def __init__(self, parent, app_context, *args, **kwargs):
        super().__init__(parent, bg=Theme.BG_CONTENT, padx=20, pady=16, *args, **kwargs)
        self.ctx = app_context

        self._build_ui()
        self.refresh_logs()

    def _build_ui(self):
        # 1. Header Bar
        title_box = tk.Frame(self, bg=Theme.BG_CONTENT)
        title_box.pack(fill="x", pady=(0, 16))

        tk.Label(
            title_box,
            text="System & Audit Logs",
            font=Theme.font_title(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CONTENT
        ).pack(side="left")

        tk.Label(
            title_box,
            text="Real-time event surveillance & audit trail (SQLite-persisted)",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CONTENT
        ).pack(side="left", padx=(12, 0), pady=(4, 0))

        # 2. Filter Toolbar Card
        filter_card = CardFrame(self, title="Log Filters & Search", subtitle="Multi-criteria Query")
        filter_card.pack(fill="x", pady=(0, 14))

        tool_row = tk.Frame(filter_card.body, bg=Theme.BG_CARD)
        tool_row.pack(fill="x")

        # Level Dropdown
        tk.Label(tool_row, text="Level:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 4))
        self.level_var = tk.StringVar(value="ALL")
        self.level_combo = ttk.Combobox(
            tool_row,
            textvariable=self.level_var,
            values=["ALL", "INFO", "WARNING", "ERROR", "DEBUG"],
            width=10,
            state="readonly",
            style="TCombobox"
        )
        self.level_combo.pack(side="left", padx=(0, 14))

        # Module Dropdown
        tk.Label(tool_row, text="Module:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 4))
        self.module_var = tk.StringVar(value="ALL")
        self.module_combo = ttk.Combobox(
            tool_row,
            textvariable=self.module_var,
            values=["ALL", "App", "ApiKeyManager", "Database", "TaskManager", "SettingsView", "LogsView"],
            width=14,
            state="readonly",
            style="TCombobox"
        )
        self.module_combo.pack(side="left", padx=(0, 14))

        # Search Query
        tk.Label(tool_row, text="Search:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 4))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(tool_row, textvariable=self.search_var, width=22, style="TEntry")
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self.refresh_logs())

        # Buttons
        btn_filter = ttk.Button(tool_row, text="🔍 Filter", style="Primary.TButton", command=self.refresh_logs)
        btn_filter.pack(side="left", padx=(0, 8))

        btn_reset = ttk.Button(tool_row, text="Reset", style="Secondary.TButton", command=self._on_reset_filters)
        btn_reset.pack(side="left", padx=(0, 8))

        btn_clear = ttk.Button(tool_row, text="🗑️ Clear Logs", style="Danger.TButton", command=self._on_clear_logs)
        btn_clear.pack(side="right", padx=(8, 0))

        btn_export = ttk.Button(tool_row, text="📤 Export", style="Secondary.TButton", command=self._on_export_logs)
        btn_export.pack(side="right", padx=(8, 0))

        btn_refresh = ttk.Button(tool_row, text="↻ Refresh", style="Secondary.TButton", command=self.refresh_logs)
        btn_refresh.pack(side="right")

        # 3. Logs Table Card
        table_card = CardFrame(self, title="Event Log Records", subtitle="Click column to sort")
        table_card.pack(fill="both", expand=True, pady=(0, 8))

        self.table = SortableTreeview(
            table_card.body,
            columns=["id", "timestamp", "level", "module", "message"],
            headings=["ID", "Timestamp", "Level", "Module", "Log Message & Details"],
            widths=[45, 140, 80, 130, 520]
        )
        self.table.pack(fill="both", expand=True)

        # 4. Status Counter Bar
        self.status_bar = tk.Label(
            self,
            text="Displaying 0 logs",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CONTENT,
            anchor="w"
        )
        self.status_bar.pack(fill="x")

    def refresh_logs(self):
        """Query SQLite logs table with active filters and populate Treeview"""
        level = self.level_var.get()
        module = self.module_var.get()
        keyword = self.search_var.get().strip()

        conditions = []
        params = []

        if level != "ALL":
            conditions.append("level = ?")
            params.append(level)

        if module != "ALL":
            conditions.append("module LIKE ?")
            params.append(f"%{module}%")

        if keyword:
            conditions.append("message LIKE ?")
            params.append(f"%{keyword}%")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT id, timestamp, level, module, message FROM logs {where_clause} ORDER BY id DESC LIMIT 500"

        try:
            rows = self.ctx.db.fetchall(sql, tuple(params))
            self.table.clear()

            for r in rows:
                lvl = r[2]
                tag = "info_tag"
                if lvl == "ERROR" or lvl == "CRITICAL":
                    tag = "error_tag"
                elif lvl == "WARNING":
                    tag = "warn_tag"

                self.table.insert_row(
                    (r[0], r[1], r[2], r[3], r[4]),
                    tags=(tag,)
                )

            self.status_bar.config(
                text=f"Displaying {len(rows)} log records (Filter: Level={level}, Module={module}, Search='{keyword}')"
            )
        except Exception as e:
            self.status_bar.config(text=f"Error querying logs: {e}")

    def _on_reset_filters(self):
        self.level_var.set("ALL")
        self.module_var.set("ALL")
        self.search_var.set("")
        self.refresh_logs()

    def _on_clear_logs(self):
        """Confirm and purge all logs from SQLite database"""
        confirm = ConfirmDialog(
            self,
            title="Clear Logs",
            message="Are you sure you want to permanently clear all audit and system logs from the database?",
            confirm_label="Clear All",
            is_danger=True
        )
        self.wait_window(confirm)

        if confirm.confirmed:
            self.ctx.db.execute("DELETE FROM logs")
            logger.info("Audit logs purged by user.")
            self.refresh_logs()

    def _on_export_logs(self):
        """Export current log entries to text file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Export System Logs"
        )
        if not file_path:
            return

        try:
            rows = self.ctx.db.fetchall("SELECT timestamp, level, module, message FROM logs ORDER BY id ASC")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"M4DI~UciH4 Trading Intelligence System — Audit Log Export\n")
                f.write(f"{'='*80}\n")
                for r in rows:
                    f.write(f"[{r[0]}] [{r[1]:<7}] [{r[2]}] {r[3]}\n")
            messagebox.showinfo("Export Complete", f"Successfully exported {len(rows)} log records to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
