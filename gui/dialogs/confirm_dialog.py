"""
M4DI~UciH4 Trading Intelligence System
Modal Confirmation Dialog
"""
import tkinter as tk
from tkinter import ttk
from config.theme import Theme
from utils.helpers import center_window


class ConfirmDialog(tk.Toplevel):
    """
    Professional dark modal dialog for confirmation actions
    (e.g., deleting an API key or clearing logs).
    """
    def __init__(self, parent, title: str, message: str, confirm_label: str = "Confirm",
                 is_danger: bool = False, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.title(title)
        self.configure(bg=Theme.BG_MODAL)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.confirmed = False
        self.message = message
        self.confirm_label = confirm_label
        self.is_danger = is_danger

        self._build_ui()
        center_window(self, width=420, height=200, parent=parent)

    def _build_ui(self):
        container = tk.Frame(self, bg=Theme.BG_MODAL, padx=24, pady=20)
        container.pack(fill="both", expand=True)

        # Icon & Header row
        header_row = tk.Frame(container, bg=Theme.BG_MODAL)
        header_row.pack(fill="x", pady=(0, 12))

        icon_char = "⚠️" if self.is_danger else "ℹ️"
        icon_col = Theme.ACCENT_ROSE if self.is_danger else Theme.ACCENT_CYAN

        icon_lbl = tk.Label(
            header_row,
            text=icon_char,
            font=(Theme.FONT_FAMILY, 16),
            bg=Theme.BG_MODAL,
            fg=icon_col
        )
        icon_lbl.pack(side="left", padx=(0, 10))

        title_lbl = tk.Label(
            header_row,
            text=self.title(),
            font=Theme.font_subtitle(),
            bg=Theme.BG_MODAL,
            fg=Theme.TEXT_PRIMARY
        )
        title_lbl.pack(side="left")

        # Message text
        msg_lbl = tk.Label(
            container,
            text=self.message,
            font=Theme.font_body(),
            bg=Theme.BG_MODAL,
            fg=Theme.TEXT_SECONDARY,
            wraplength=370,
            justify="left"
        )
        msg_lbl.pack(fill="x", pady=(0, 20))

        # Action Buttons
        btn_box = tk.Frame(container, bg=Theme.BG_MODAL)
        btn_box.pack(fill="x", side="bottom")

        btn_cancel = ttk.Button(
            btn_box,
            text="Cancel",
            style="Secondary.TButton",
            command=self._on_cancel
        )
        btn_cancel.pack(side="right", padx=(8, 0))

        btn_style = "Danger.TButton" if self.is_danger else "Primary.TButton"
        btn_confirm = ttk.Button(
            btn_box,
            text=self.confirm_label,
            style=btn_style,
            command=self._on_confirm
        )
        btn_confirm.pack(side="right")

    def _on_confirm(self):
        self.confirmed = True
        self.destroy()

    def _on_cancel(self):
        self.confirmed = False
        self.destroy()
