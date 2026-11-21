"""
M4DI~UciH4 Trading Intelligence System
Window, GUI & System Helper Functions
"""
import tkinter as tk


def center_window(window: tk.Toplevel, width: int = 500, height: int = 400, parent=None):
    """Center a modal or top-level window relative to screen or parent window"""
    window.update_idletasks()
    
    if parent and parent.winfo_exists():
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        
        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2
    else:
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        
    x = max(10, x)
    y = max(10, y)
    window.geometry(f"{width}x{height}+{x}+{y}")
