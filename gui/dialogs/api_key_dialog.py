"""
M4DI~UciH4 Trading Intelligence System
Add / Edit API Key Modal Dialog
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any

from config.constants import API_PROVIDERS, PROVIDER_INFO
from config.theme import Theme
from utils.helpers import center_window


class ApiKeyDialog(tk.Toplevel):
    """
    Modal Dialog to Add or Edit API Keys with Provider selector,
    Key Name, Masked toggle input, and Active status.
    """
    def __init__(self, parent, edit_data: Optional[Dict[str, Any]] = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.edit_data = edit_data
        self.is_edit = edit_data is not None

        dialog_title = "Edit API Key" if self.is_edit else "Add New API Key"
        self.title(dialog_title)
        self.configure(bg=Theme.BG_MODAL)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.result = None
        self._show_key = False

        self._build_ui()
        center_window(self, width=500, height=490, parent=parent)

    def _build_ui(self):
        container = tk.Frame(self, bg=Theme.BG_MODAL, padx=24, pady=20)
        container.pack(fill="both", expand=True)

        # Header Title
        hdr_frame = tk.Frame(container, bg=Theme.BG_MODAL)
        hdr_frame.pack(fill="x", pady=(0, 16))

        icon_lbl = tk.Label(
            hdr_frame,
            text="🔑",
            font=(Theme.FONT_FAMILY, 15),
            bg=Theme.BG_MODAL,
            fg=Theme.ACCENT_CYAN
        )
        icon_lbl.pack(side="left", padx=(0, 8))

        lbl_title = tk.Label(
            hdr_frame,
            text="Edit API Key" if self.is_edit else "Register API Key",
            font=Theme.font_subtitle(),
            bg=Theme.BG_MODAL,
            fg=Theme.TEXT_PRIMARY
        )
        lbl_title.pack(side="left")

        # 1. Provider Selection
        tk.Label(
            container,
            text="API Provider *",
            font=Theme.font_body_bold(),
            bg=Theme.BG_MODAL,
            fg=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 4))

        self.provider_var = tk.StringVar(
            value=self.edit_data.get("provider", API_PROVIDERS[0]) if self.is_edit else API_PROVIDERS[0]
        )
        self.provider_combo = ttk.Combobox(
            container,
            textvariable=self.provider_var,
            values=API_PROVIDERS,
            state="readonly" if not self.is_edit else "disabled",
            style="TCombobox"
        )
        self.provider_combo.pack(fill="x", pady=(0, 14))

        # 2. Key Name / Label
        tk.Label(
            container,
            text="Key Name / Identifier *",
            font=Theme.font_body_bold(),
            bg=Theme.BG_MODAL,
            fg=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 4))

        default_name = self.edit_data.get("name", "") if self.is_edit else "Finnhub Key 1"
        self.name_var = tk.StringVar(value=default_name)
        self.name_entry = ttk.Entry(container, textvariable=self.name_var, style="TEntry")
        self.name_entry.pack(fill="x", pady=(0, 14))

        # 3. API Key Secret Input
        key_label_text = "API Key Value (Leave blank to keep existing)" if self.is_edit else "API Key Secret *"
        tk.Label(
            container,
            text=key_label_text,
            font=Theme.font_body_bold(),
            bg=Theme.BG_MODAL,
            fg=Theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 4))

        key_box = tk.Frame(container, bg=Theme.BG_MODAL)
        key_box.pack(fill="x", pady=(0, 14))

        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(key_box, textvariable=self.key_var, show="•", style="TEntry")
        self.key_entry.pack(side="left", fill="x", expand=True)

        self.btn_toggle_key = tk.Button(
            key_box,
            text="👁️ Show",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.TEXT_SECONDARY,
            activebackground=Theme.BORDER_SUBTLE,
            activeforeground=Theme.ACCENT_CYAN,
            relief="flat",
            padx=8,
            cursor="hand2",
            command=self._toggle_key_visibility
        )
        self.btn_toggle_key.pack(side="right", padx=(8, 0))

        # 4. Priority Selection (1 to 10)
        prio_frame = tk.Frame(container, bg=Theme.BG_MODAL)
        prio_frame.pack(fill="x", pady=(0, 14))

        tk.Label(
            prio_frame,
            text="Key Priority (1-10, Higher = First Selection):",
            font=Theme.font_body_bold(),
            bg=Theme.BG_MODAL,
            fg=Theme.TEXT_SECONDARY
        ).pack(side="left")

        default_prio = self.edit_data.get("priority", 1) if self.is_edit else 1
        self.priority_var = tk.IntVar(value=default_prio)
        self.priority_spin = ttk.Spinbox(
            prio_frame,
            from_=1,
            to=10,
            textvariable=self.priority_var,
            width=6,
            style="TSpinbox"
        )
        self.priority_spin.pack(side="right")

        # 5. Status Checkbox
        status_box = tk.Frame(container, bg=Theme.BG_MODAL)
        status_box.pack(fill="x", pady=(0, 14))

        self.active_var = tk.BooleanVar(
            value=self.edit_data.get("is_active", True) if self.is_edit else True
        )
        self.active_chk = tk.Checkbutton(
            status_box,
            text="Enable API Key immediately (Active status)",
            variable=self.active_var,
            bg=Theme.BG_MODAL,
            fg=Theme.TEXT_PRIMARY,
            selectcolor=Theme.BG_INPUT,
            activebackground=Theme.BG_MODAL,
            activeforeground=Theme.ACCENT_CYAN,
            font=Theme.font_body()
        )
        self.active_chk.pack(anchor="w")

        # 6. Validation Warning Message Label
        self.error_lbl = tk.Label(
            container,
            text="",
            font=Theme.font_caption(),
            bg=Theme.BG_MODAL,
            fg=Theme.ACCENT_ROSE
        )
        self.error_lbl.pack(fill="x", pady=(0, 8))

        # 7. Action Buttons
        btn_box = tk.Frame(container, bg=Theme.BG_MODAL)
        btn_box.pack(fill="x", side="bottom")

        btn_cancel = ttk.Button(
            btn_box,
            text="Cancel",
            style="Secondary.TButton",
            command=self._on_cancel
        )
        btn_cancel.pack(side="right", padx=(8, 0))

        btn_save = ttk.Button(
            btn_box,
            text="Save Key",
            style="Primary.TButton",
            command=self._on_save
        )
        btn_save.pack(side="right")

    def _toggle_key_visibility(self):
        """Toggle password masking on key entry"""
        self._show_key = not self._show_key
        if self._show_key:
            self.key_entry.config(show="")
            self.btn_toggle_key.config(text="🔒 Hide")
        else:
            self.key_entry.config(show="•")
            self.btn_toggle_key.config(text="👁️ Show")

    def _on_save(self):
        """Validate inputs and return payload"""
        provider = self.provider_var.get().strip()
        name = self.name_var.get().strip()
        raw_key = self.key_var.get().strip()
        is_active = self.active_var.get()

        if not name:
            self.error_lbl.config(text="Error: Key Name cannot be empty.")
            self.name_entry.focus_set()
            return

        if not self.is_edit and not raw_key:
            self.error_lbl.config(text="Error: API Key value is required.")
            self.key_entry.focus_set()
            return

        self.result = {
            "provider": provider,
            "name": name,
            "raw_key": raw_key if raw_key else None,
            "is_active": is_active,
            "priority": int(self.priority_var.get() or 1)
        }
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()
