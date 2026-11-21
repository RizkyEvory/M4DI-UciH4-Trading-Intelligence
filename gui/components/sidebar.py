"""
M4DI~UciH4 Trading Intelligence System
Navigation Sidebar Component (10 Pages)
"""
import tkinter as tk
from typing import Callable, Dict
from config.constants import NAV_ITEMS, APP_AUTHOR, APP_VERSION
from config.theme import Theme


class Sidebar(tk.Frame):
    """
    Left Navigation Sidebar providing access to all 10 application views
    with active indicators and sleek dark aesthetics.
    """
    def __init__(self, parent, on_navigate: Callable[[str], None], *args, **kwargs):
        super().__init__(
            parent,
            bg=Theme.BG_SIDEBAR,
            width=220,
            highlightbackground=Theme.BORDER_SUBTLE,
            highlightthickness=1,
            *args,
            **kwargs
        )
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self.current_page = ""
        self.buttons: Dict[str, tk.Frame] = {}

        self._build_ui()

    def _build_ui(self):
        # Section Label
        lbl_nav = tk.Label(
            self,
            text="NAVIGATION",
            font=(Theme.FONT_FAMILY, 7, "bold"),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_SIDEBAR,
            anchor="w",
            padx=16,
            pady=12
        )
        lbl_nav.pack(fill="x")

        # Scrollable container or clean pack list
        nav_container = tk.Frame(self, bg=Theme.BG_SIDEBAR)
        nav_container.pack(fill="both", expand=True)

        for page_name, icon in NAV_ITEMS:
            btn_frame = self._create_nav_button(nav_container, page_name, icon)
            btn_frame.pack(fill="x", padx=6, pady=2)
            self.buttons[page_name] = btn_frame

        # Bottom Footer
        footer = tk.Frame(self, bg=Theme.BG_SIDEBAR, padx=12, pady=14)
        footer.pack(side="bottom", fill="x")

        divider = tk.Frame(footer, bg=Theme.BORDER_SUBTLE, height=1)
        divider.pack(fill="x", pady=(0, 10))

        v_lbl = tk.Label(
            footer,
            text=f"Build: {APP_VERSION}",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_SIDEBAR,
            anchor="w"
        )
        v_lbl.pack(anchor="w")

        author_lbl = tk.Label(
            footer,
            text=f"👑 {APP_AUTHOR}",
            font=Theme.font_caption(),
            fg=Theme.ACCENT_GOLD,
            bg=Theme.BG_SIDEBAR,
            anchor="w"
        )
        author_lbl.pack(anchor="w")

    def _create_nav_button(self, parent, page_name: str, icon: str) -> tk.Frame:
        """Create a custom interactive navigation button with left indicator pill"""
        frame = tk.Frame(parent, bg=Theme.BG_SIDEBAR, cursor="hand2")

        # Left cyan accent strip (active indicator)
        indicator = tk.Frame(frame, bg=Theme.BG_SIDEBAR, width=3)
        indicator.pack(side="left", fill="y")

        # Content box
        content = tk.Frame(frame, bg=Theme.BG_SIDEBAR, padx=10, pady=7)
        content.pack(side="left", fill="both", expand=True)

        icon_lbl = tk.Label(
            content,
            text=icon,
            font=(Theme.FONT_FAMILY, 11),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_SIDEBAR
        )
        icon_lbl.pack(side="left", padx=(0, 10))

        text_lbl = tk.Label(
            content,
            text=page_name,
            font=Theme.font_body(),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_SIDEBAR,
            anchor="w"
        )
        text_lbl.pack(side="left", fill="x", expand=True)

        # Store widget references for state updates
        frame._indicator = indicator
        frame._content = content
        frame._icon = icon_lbl
        frame._text = text_lbl
        frame._page_name = page_name

        # Bind hover and click events
        def _on_click(event=None):
            self.set_active(page_name)
            self.on_navigate(page_name)

        def _on_enter(event=None):
            if self.current_page != page_name:
                frame.config(bg=Theme.BG_CARD)
                content.config(bg=Theme.BG_CARD)
                icon_lbl.config(bg=Theme.BG_CARD, fg=Theme.TEXT_PRIMARY)
                text_lbl.config(bg=Theme.BG_CARD, fg=Theme.TEXT_PRIMARY)

        def _on_leave(event=None):
            if self.current_page != page_name:
                frame.config(bg=Theme.BG_SIDEBAR)
                content.config(bg=Theme.BG_SIDEBAR)
                icon_lbl.config(bg=Theme.BG_SIDEBAR, fg=Theme.TEXT_SECONDARY)
                text_lbl.config(bg=Theme.BG_SIDEBAR, fg=Theme.TEXT_SECONDARY)

        for w in (frame, content, icon_lbl, text_lbl):
            w.bind("<Button-1>", _on_click)
            w.bind("<Enter>", _on_enter)
            w.bind("<Leave>", _on_leave)

        return frame

    def set_active(self, page_name: str):
        """Highlight active navigation page and reset others"""
        self.current_page = page_name

        for name, frame in self.buttons.items():
            is_active = (name == page_name)
            bg_col = Theme.BG_CARD_ALT if is_active else Theme.BG_SIDEBAR
            text_col = Theme.ACCENT_CYAN if is_active else Theme.TEXT_SECONDARY
            font_choice = Theme.font_body_bold() if is_active else Theme.font_body()
            indicator_col = Theme.ACCENT_CYAN if is_active else Theme.BG_SIDEBAR

            frame.config(bg=bg_col)
            frame._content.config(bg=bg_col)
            frame._icon.config(bg=bg_col, fg=text_col)
            frame._text.config(bg=bg_col, fg=text_col, font=font_choice)
            frame._indicator.config(bg=indicator_col)
