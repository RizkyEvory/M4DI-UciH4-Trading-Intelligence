"""
M4DI~UciH4 Trading Intelligence System
Application Header Bar Component
"""
import tkinter as tk
from datetime import datetime
from config.constants import APP_NAME, APP_VERSION
from config.theme import Theme


class Header(tk.Frame):
    """
    Top Header Bar featuring branding, live real-time clock,
    and system status pills (Tasks, DB status, Edition badge).
    """
    def __init__(self, parent, app_context, *args, **kwargs):
        super().__init__(
            parent,
            bg=Theme.BG_HEADER,
            height=60,
            highlightbackground=Theme.BORDER_SUBTLE,
            highlightthickness=1,
            padx=18,
            pady=8,
            *args,
            **kwargs
        )
        self.ctx = app_context
        self._is_alive = True

        self._build_ui()
        self._start_clock()
        self._start_telemetry_polling()

    def _build_ui(self):
        # 1. Left Branding Section
        left_box = tk.Frame(self, bg=Theme.BG_HEADER)
        left_box.pack(side="left", fill="y")

        brand_logo = tk.Label(
            left_box,
            text="👑",
            font=(Theme.FONT_FAMILY, 15),
            bg=Theme.BG_HEADER,
            fg=Theme.ACCENT_GOLD
        )
        brand_logo.pack(side="left", padx=(0, 8))

        brand_text_box = tk.Frame(left_box, bg=Theme.BG_HEADER)
        brand_text_box.pack(side="left")

        title_lbl = tk.Label(
            brand_text_box,
            text=APP_NAME,
            font=Theme.font_subtitle(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_HEADER,
            anchor="w"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            brand_text_box,
            text="Institutional Trading Intelligence • Enterprise Edition",
            font=Theme.font_caption(),
            fg=Theme.ACCENT_CYAN,
            bg=Theme.BG_HEADER,
            anchor="w"
        )
        sub_lbl.pack(anchor="w")

        # 2. Right Status Section (Pills)
        right_box = tk.Frame(self, bg=Theme.BG_HEADER)
        right_box.pack(side="right", fill="y")

        # Institutional Edition Badge
        self.grade_pill = tk.Label(
            right_box,
            text=" INSTITUTIONAL GRADE • PRODUCTION ",
            font=(Theme.FONT_FAMILY, 8, "bold"),
            fg="#042F2E",
            bg=Theme.ACCENT_TURQUOISE,
            padx=8,
            pady=3
        )
        self.grade_pill.pack(side="right", padx=(8, 0))

        # DB Status Pill
        self.db_pill = tk.Label(
            right_box,
            text=" 💾 SQLite: Connected ",
            font=(Theme.FONT_FAMILY, 8),
            fg=Theme.ACCENT_EMERALD,
            bg="#11221D",
            highlightbackground="#164E63",
            highlightthickness=1,
            padx=6,
            pady=3
        )
        self.db_pill.pack(side="right", padx=(8, 0))

        # Tasks Pill
        self.task_pill = tk.Label(
            right_box,
            text=" ⚡ Tasks: 0 ",
            font=(Theme.FONT_FAMILY, 8),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD,
            highlightbackground=Theme.BORDER_SUBTLE,
            highlightthickness=1,
            padx=6,
            pady=3
        )
        self.task_pill.pack(side="right", padx=(8, 0))

        # 3. Center Section: Live Clock & System Status
        center_box = tk.Frame(self, bg=Theme.BG_HEADER)
        center_box.pack(side="right", fill="y", padx=(0, 20))

        self.clock_lbl = tk.Label(
            center_box,
            text="",
            font=(Theme.FONT_MONO, 10, "bold"),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_HEADER
        )
        self.clock_lbl.pack(anchor="e")

        self.status_lbl = tk.Label(
            center_box,
            text="🟢 SYSTEM ACTIVE | IDLE",
            font=(Theme.FONT_FAMILY, 7, "bold"),
            fg=Theme.ACCENT_EMERALD,
            bg=Theme.BG_HEADER
        )
        self.status_lbl.pack(anchor="e")

    def _start_clock(self):
        """Update live system time every second"""
        if not self._is_alive:
            return
        now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        self.clock_lbl.config(text=now_str)
        self.after(1000, self._start_clock)

    def _start_telemetry_polling(self):
        """Poll active task count and update task pill"""
        if not self._is_alive:
            return
        try:
            tasks_count = self.ctx.tasks.active_tasks_count()
            if tasks_count > 0:
                self.task_pill.config(
                    text=f" ⚡ Tasks: {tasks_count} Active ",
                    fg=Theme.ACCENT_CYAN,
                    bg="#0E2838"
                )
                self.status_lbl.config(
                    text="🔵 BACKGROUND TASK RUNNING",
                    fg=Theme.ACCENT_CYAN
                )
            else:
                self.task_pill.config(
                    text=" ⚡ Tasks: 0 ",
                    fg=Theme.TEXT_SECONDARY,
                    bg=Theme.BG_CARD
                )
                self.status_lbl.config(
                    text="🟢 SYSTEM ACTIVE | IDLE",
                    fg=Theme.ACCENT_EMERALD
                )
        except Exception:
            pass

        self.after(500, self._start_telemetry_polling)

    def destroy(self):
        self._is_alive = False
        super().destroy()
