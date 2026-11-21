"""
M4DI~UciH4 Trading Intelligence System
Modern Dark Theme Styling & TTK Widget Configuration
"""
import tkinter as tk
from tkinter import ttk

class Theme:
    """Design System & Color Tokens for Dark Charcoal / Modern UI"""
    
    # Background Palettes
    BG_ROOT = "#0B0F17"           # Root application window
    BG_SIDEBAR = "#080C13"        # Sidebar background
    BG_HEADER = "#0E1420"         # Top header bar
    BG_CONTENT = "#0D111A"        # Main content background
    BG_CARD = "#141C2B"           # Card / Section containers
    BG_CARD_ALT = "#182234"       # Elevated cards / hovered row
    BG_INPUT = "#0A0E17"          # Input entries, comboboxes
    BG_MODAL = "#121A27"          # Modal dialog background
    
    # Borders & Dividers
    BORDER_SUBTLE = "#1E2B3E"     # Default subtle card border
    BORDER_FOCUS = "#00E5FF"      # Focused input border / active indicator
    BORDER_ACCENT = "#00B4D8"     # Secondary accent border
    
    # Accent Colors
    ACCENT_CYAN = "#00E5FF"       # Brand Primary Accent (Cyan)
    ACCENT_CYAN_HOVER = "#33ECFF" # Hovered cyan
    ACCENT_TURQUOISE = "#00F5D4"  # Turquoise / Success
    ACCENT_GOLD = "#FFD700"       # Imperial Gold
    ACCENT_EMERALD = "#10B981"    # Green (Win / Active / Online)
    ACCENT_ROSE = "#F43F5E"       # Crimson / Red (Loss / Error / Offline)
    ACCENT_AMBER = "#F59E0B"      # Warning / Standby
    ACCENT_PURPLE = "#A855F7"     # Institutional Tag
    ACCENT_MAGENTA = "#D946EF"    # High-impact / Critical Tag
    SUCCESS = "#10B981"           # Green (Win / Active / Online)
    ERROR = "#F43F5E"             # Crimson / Red (Loss / Error / Offline)
    WARNING = "#F59E0B"           # Warning / Standby
    
    # Typography Colors
    TEXT_PRIMARY = "#F8FAFC"      # White / High-contrast primary text
    TEXT_SECONDARY = "#94A3B8"    # Cool Silver / Secondary label
    TEXT_MUTED = "#64748B"        # Muted gray / Disabled text
    TEXT_CYAN = "#00E5FF"         # Highlighted cyan text
    TEXT_GOLD = "#FCD34D"         # Highlighted gold text
    
    # Typography Fonts (Cross-platform modern font choices)
    FONT_FAMILY = "Segoe UI"
    FONT_MONO = "Consolas"

    @classmethod
    def set_palette(cls, theme_name: str):
        """Dynamically switch color accents based on selected theme"""
        if "Gold" in theme_name:
            cls.ACCENT_CYAN = "#FFD700"
            cls.ACCENT_CYAN_HOVER = "#FFE44D"
            cls.BORDER_FOCUS = "#FFD700"
            cls.TEXT_CYAN = "#FCD34D"
        elif "Emerald" in theme_name:
            cls.ACCENT_CYAN = "#10B981"
            cls.ACCENT_CYAN_HOVER = "#34D399"
            cls.BORDER_FOCUS = "#10B981"
            cls.TEXT_CYAN = "#34D399"
        elif "Cyberpunk" in theme_name:
            cls.ACCENT_CYAN = "#00F5D4"
            cls.ACCENT_CYAN_HOVER = "#7000FF"
            cls.BORDER_FOCUS = "#D946EF"
            cls.TEXT_CYAN = "#00F5D4"
        else:  # Dark Charcoal (Default)
            cls.ACCENT_CYAN = "#00E5FF"
            cls.ACCENT_CYAN_HOVER = "#33ECFF"
            cls.BORDER_FOCUS = "#00E5FF"
            cls.TEXT_CYAN = "#00E5FF"
    
    @classmethod
    def font_title(cls):
        return (cls.FONT_FAMILY, 14, "bold")
        
    @classmethod
    def font_subtitle(cls):
        return (cls.FONT_FAMILY, 11, "bold")
        
    @classmethod
    def font_body(cls):
        return (cls.FONT_FAMILY, 9)
        
    @classmethod
    def font_body_bold(cls):
        return (cls.FONT_FAMILY, 9, "bold")
        
    @classmethod
    def font_caption(cls):
        return (cls.FONT_FAMILY, 8)
        
    @classmethod
    def font_mono(cls):
        return (cls.FONT_MONO, 9)

    @classmethod
    def font_hero(cls):
        return (cls.FONT_FAMILY, 20, "bold")

    @classmethod
    def apply_ttk_styles(cls, root: tk.Tk):
        """Configure native TTK widgets with the custom dark charcoal styling"""
        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
            
        # Global Frame Styling
        style.configure("TFrame", background=cls.BG_CONTENT)
        style.configure("Root.TFrame", background=cls.BG_ROOT)
        style.configure("Sidebar.TFrame", background=cls.BG_SIDEBAR)
        style.configure("Header.TFrame", background=cls.BG_HEADER)
        style.configure("Card.TFrame", background=cls.BG_CARD, relief="flat")
        
        # Labels
        style.configure("TLabel", background=cls.BG_CONTENT, foreground=cls.TEXT_PRIMARY, font=cls.font_body())
        style.configure("Card.TLabel", background=cls.BG_CARD, foreground=cls.TEXT_PRIMARY, font=cls.font_body())
        style.configure("Muted.TLabel", background=cls.BG_CARD, foreground=cls.TEXT_MUTED, font=cls.font_caption())
        style.configure("HeaderTitle.TLabel", background=cls.BG_HEADER, foreground=cls.TEXT_PRIMARY, font=cls.font_title())
        style.configure("HeaderSub.TLabel", background=cls.BG_HEADER, foreground=cls.ACCENT_CYAN, font=cls.font_caption())
        style.configure("CardTitle.TLabel", background=cls.BG_CARD, foreground=cls.ACCENT_CYAN, font=cls.font_subtitle())
        style.configure("StatValue.TLabel", background=cls.BG_CARD, foreground=cls.TEXT_PRIMARY, font=cls.font_hero())
        
        # Buttons
        style.configure(
            "Primary.TButton",
            background=cls.ACCENT_CYAN,
            foreground="#06090E",
            font=cls.font_body_bold(),
            borderwidth=0,
            focuscolor=cls.ACCENT_CYAN,
            padding=(12, 6)
        )
        style.map(
            "Primary.TButton",
            background=[("active", cls.ACCENT_CYAN_HOVER), ("disabled", cls.BORDER_SUBTLE)],
            foreground=[("disabled", cls.TEXT_MUTED)]
        )
        
        style.configure(
            "Secondary.TButton",
            background=cls.BG_CARD_ALT,
            foreground=cls.TEXT_PRIMARY,
            font=cls.font_body_bold(),
            borderwidth=1,
            relief="solid",
            padding=(10, 5)
        )
        style.map(
            "Secondary.TButton",
            background=[("active", cls.BORDER_SUBTLE)],
            foreground=[("active", cls.ACCENT_CYAN)]
        )

        style.configure(
            "Danger.TButton",
            background="#7F1D1D",
            foreground="#FECDD3",
            font=cls.font_body_bold(),
            borderwidth=0,
            padding=(10, 5)
        )
        style.map(
            "Danger.TButton",
            background=[("active", cls.ACCENT_ROSE)]
        )

        # Nav Button (Sidebar)
        style.configure(
            "Nav.TButton",
            background=cls.BG_SIDEBAR,
            foreground=cls.TEXT_SECONDARY,
            font=(cls.FONT_FAMILY, 9),
            anchor="w",
            borderwidth=0,
            padding=(14, 9)
        )
        style.map(
            "Nav.TButton",
            background=[("active", cls.BG_CARD), ("selected", cls.BG_CARD_ALT)],
            foreground=[("active", cls.TEXT_PRIMARY), ("selected", cls.ACCENT_CYAN)]
        )

        # Treeview (Modern Dark Tables)
        style.configure(
            "Treeview",
            background=cls.BG_CARD,
            foreground=cls.TEXT_PRIMARY,
            fieldbackground=cls.BG_CARD,
            borderwidth=0,
            font=cls.font_body(),
            rowheight=28
        )
        style.configure(
            "Treeview.Heading",
            background=cls.BG_CARD_ALT,
            foreground=cls.ACCENT_CYAN,
            font=cls.font_body_bold(),
            borderwidth=0,
            relief="flat",
            padding=(6, 6)
        )
        style.map(
            "Treeview",
            background=[("selected", "#1E3A5F")],
            foreground=[("selected", cls.TEXT_PRIMARY)]
        )
        style.map(
            "Treeview.Heading",
            background=[("active", cls.BORDER_SUBTLE)],
            foreground=[("active", cls.ACCENT_TURQUOISE)]
        )

        # Entry & Combobox
        style.configure(
            "TEntry",
            fieldbackground=cls.BG_INPUT,
            foreground=cls.TEXT_PRIMARY,
            insertcolor=cls.ACCENT_CYAN,
            borderwidth=1,
            padding=5
        )
        style.configure(
            "TCombobox",
            fieldbackground=cls.BG_INPUT,
            background=cls.BG_CARD_ALT,
            foreground=cls.TEXT_PRIMARY,
            arrowcolor=cls.ACCENT_CYAN,
            borderwidth=1,
            padding=5
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", cls.BG_INPUT)],
            selectbackground=[("readonly", cls.BG_CARD_ALT)],
            selectforeground=[("readonly", cls.TEXT_PRIMARY)]
        )

        # Scrollbar
        style.configure(
            "Vertical.TScrollbar",
            background=cls.BG_CARD_ALT,
            troughcolor=cls.BG_ROOT,
            borderwidth=0,
            arrowsize=12
        )
        style.configure(
            "Horizontal.TScrollbar",
            background=cls.BG_CARD_ALT,
            troughcolor=cls.BG_ROOT,
            borderwidth=0,
            arrowsize=12
        )
