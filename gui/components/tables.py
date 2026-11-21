"""
M4DI~UciH4 Trading Intelligence System
Sortable Dark Treeview Table Component
"""
import tkinter as tk
from tkinter import ttk
from config.theme import Theme


class SortableTreeview(tk.Frame):
    """
    Modern TTK Treeview table with sorting, alternating row colors,
    and responsive dark-themed scrollbars.
    """
    def __init__(self, parent, columns: list, headings: list, widths: list = None,
                 selectmode: str = "browse", *args, **kwargs):
        super().__init__(parent, bg=Theme.BG_CARD, *args, **kwargs)

        self.columns = columns
        self._sort_reverse = {col: False for col in columns}

        # Treeview Widget
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            selectmode=selectmode,
            style="Treeview"
        )

        # Scrollbars
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview, style="Horizontal.TScrollbar")
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        # Layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Configure columns & sort handlers
        for idx, col in enumerate(columns):
            heading_text = headings[idx] if idx < len(headings) else col
            w = widths[idx] if widths and idx < len(widths) else 120
            self.tree.heading(col, text=heading_text, command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=w, anchor="w", stretch=True)

        # Alternating row tag colors
        self.tree.tag_configure("evenrow", background=Theme.BG_CARD)
        self.tree.tag_configure("oddrow", background=Theme.BG_CARD_ALT)
        self.tree.tag_configure("active_tag", foreground=Theme.ACCENT_EMERALD)
        self.tree.tag_configure("disabled_tag", foreground=Theme.TEXT_MUTED)
        self.tree.tag_configure("error_tag", foreground=Theme.ACCENT_ROSE)
        self.tree.tag_configure("warn_tag", foreground=Theme.ACCENT_AMBER)
        self.tree.tag_configure("info_tag", foreground=Theme.TEXT_PRIMARY)

    def sort_column(self, col: str):
        """Sort treeview rows by column value (alphabetical or numeric)"""
        items = self.tree.get_children("")
        if not items:
            return

        reverse = self._sort_reverse.get(col, False)
        
        # Determine value type for sorting
        sample_val = self.tree.set(items[0], col)
        
        def _get_sort_val(item):
            val = self.tree.set(item, col)
            # Try float conversion
            try:
                return float(val.replace("$", "").replace("%", "").replace(",", "").strip())
            except ValueError:
                return val.lower()

        sorted_items = sorted(items, key=_get_sort_val, reverse=reverse)

        for index, item in enumerate(sorted_items):
            self.tree.move(item, "", index)
            # Reapply alternating row colors
            current_tags = list(self.tree.item(item, "tags"))
            current_tags = [t for t in current_tags if t not in ("evenrow", "oddrow")]
            current_tags.append("evenrow" if index % 2 == 0 else "oddrow")
            self.tree.item(item, tags=tuple(current_tags))

        # Toggle sort direction
        self._sort_reverse[col] = not reverse

    def clear(self):
        """Remove all rows from treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insert_row(self, values: tuple, tags: tuple = ()):
        """Insert row with automatic alternate row coloring"""
        row_count = len(self.tree.get_children())
        base_tag = "evenrow" if row_count % 2 == 0 else "oddrow"
        combined_tags = (base_tag,) + tags
        return self.tree.insert("", "end", values=values, tags=combined_tags)
