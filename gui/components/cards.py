"""
M4DI~UciH4 Trading Intelligence System
Reusable Card & Panel Components
"""
import tkinter as tk
from tkinter import ttk
from config.theme import Theme


class CardFrame(tk.Frame):
    """
    Modern Dark Card Panel container with subtle border and padding.
    """
    def __init__(self, parent, title: str = "", subtitle: str = "", *args, **kwargs):
        super().__init__(
            parent,
            bg=Theme.BG_CARD,
            highlightbackground=Theme.BORDER_SUBTLE,
            highlightthickness=1,
            padx=14,
            pady=12,
            *args,
            **kwargs
        )
        self.title_text = title
        self.subtitle_text = subtitle

        if title or subtitle:
            self._header_frame = tk.Frame(self, bg=Theme.BG_CARD)
            self._header_frame.pack(fill="x", pady=(0, 10))

            if title:
                self.title_label = tk.Label(
                    self._header_frame,
                    text=title,
                    font=Theme.font_subtitle(),
                    fg=Theme.ACCENT_CYAN,
                    bg=Theme.BG_CARD,
                    anchor="w"
                )
                self.title_label.pack(side="left")

            if subtitle:
                self.subtitle_label = tk.Label(
                    self._header_frame,
                    text=subtitle,
                    font=Theme.font_caption(),
                    fg=Theme.TEXT_MUTED,
                    bg=Theme.BG_CARD,
                    anchor="e"
                )
                self.subtitle_label.pack(side="right")

            # Subtle accent divider line
            self._divider = tk.Frame(self, bg=Theme.BORDER_SUBTLE, height=1)
            self._divider.pack(fill="x", pady=(0, 10))

        # Body container where child widgets are placed
        self.body = tk.Frame(self, bg=Theme.BG_CARD)
        self.body.pack(fill="both", expand=True)


class StatCard(tk.Frame):
    """
    Quick Telemetry Metric Card displaying Icon, Numeric Value, Label, and Status Pill.
    """
    def __init__(self, parent, icon: str, value: str, label: str, status_text: str = "",
                 accent_color: str = Theme.ACCENT_CYAN, *args, **kwargs):
        super().__init__(
            parent,
            bg=Theme.BG_CARD,
            highlightbackground=Theme.BORDER_SUBTLE,
            highlightthickness=1,
            padx=16,
            pady=14,
            *args,
            **kwargs
        )
        self.accent_color = accent_color

        # Top row: Icon and Status Pill
        top_row = tk.Frame(self, bg=Theme.BG_CARD)
        top_row.pack(fill="x")

        self.icon_lbl = tk.Label(
            top_row,
            text=icon,
            font=(Theme.FONT_FAMILY, 16),
            fg=accent_color,
            bg=Theme.BG_CARD
        )
        self.icon_lbl.pack(side="left")

        if status_text:
            self.status_pill = tk.Label(
                top_row,
                text=f" {status_text} ",
                font=Theme.font_caption(),
                fg=Theme.TEXT_PRIMARY,
                bg="#1A283C",
                padx=6,
                pady=2
            )
            self.status_pill.pack(side="right")
        else:
            self.status_pill = None

        # Value Row
        self.val_lbl = tk.Label(
            self,
            text=value,
            font=Theme.font_hero(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD,
            anchor="w"
        )
        self.val_lbl.pack(fill="x", pady=(8, 2))

        # Title Label
        self.lbl_lbl = tk.Label(
            self,
            text=label,
            font=Theme.font_body(),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD,
            anchor="w"
        )
        self.lbl_lbl.pack(fill="x")

    def update_value(self, new_value: str, status_text: str = None):
        """Update metric value dynamically"""
        self.val_lbl.config(text=new_value)
        if status_text is not None and self.status_pill:
            self.status_pill.config(text=f" {status_text} ")
