"""
M4DI~UciH4 Trading Intelligence System
Interactive Institutional Candlestick Chart Widget
Built on native high-performance Tkinter Canvas with Pan, Zoom, Crosshair, and Overlays.
"""
import tkinter as tk
from typing import List, Optional, Tuple, Dict, Any

from config.theme import Theme
from api.models import NormalizedCandle
from analytics.indicators import (
    calculate_ema,
    calculate_sma,
    calculate_bollinger_bands,
    calculate_rsi,
    calculate_macd
)


class CandlestickChart(tk.Frame):
    """
    Hardware-accelerated native Tkinter Canvas Candlestick Chart.
    Supports Zooming, Panning, Interactive Crosshair HUD, EMAs, Bollinger Bands, Volume, RSI, and MACD.
    """

    def __init__(self, parent, bg_color=Theme.BG_CARD, *args, **kwargs):
        super().__init__(parent, bg=bg_color, *args, **kwargs)
        self.bg_color = bg_color

        # Chart Series Data
        self.candles: List[NormalizedCandle] = []

        # Viewport Window state (index range of candles currently displayed)
        self.view_start = 0
        self.view_count = 50  # Default number of candles visible

        # Display Toggles
        self.show_ema9 = True
        self.show_ema21 = True
        self.show_ema50 = False
        self.show_ema200 = False
        self.show_bollinger = True
        self.sub_chart_mode = "volume"  # "volume", "rsi", "macd", "none"

        # Interactive Pan state
        self._pan_start_x = None
        self._pan_start_view = None

        # Crosshair state
        self._hover_x = None
        self._hover_y = None
        self._hover_candle_idx = None

        self._build_ui()

    def _build_ui(self):
        # 1. Top HUD Bar for Live / Hovered OHLCV Metrics
        self.hud_frame = tk.Frame(self, bg=self.bg_color, padx=12, pady=4)
        self.hud_frame.pack(fill="x")

        self.lbl_symbol_info = tk.Label(
            self.hud_frame,
            text="No Instrument Loaded",
            font=Theme.font_body_bold(),
            fg=Theme.ACCENT_CYAN,
            bg=self.bg_color
        )
        self.lbl_symbol_info.pack(side="left", padx=(0, 16))

        self.lbl_ohlcv_hud = tk.Label(
            self.hud_frame,
            text="O: -  H: -  L: -  C: -  Vol: -",
            font=Theme.font_caption(),
            fg=Theme.TEXT_SECONDARY,
            bg=self.bg_color
        )
        self.lbl_ohlcv_hud.pack(side="left")

        # 2. Main Drawing Canvas
        self.canvas = tk.Canvas(
            self,
            bg=self.bg_color,
            highlightthickness=0,
            cursor="crosshair"
        )
        self.canvas.pack(fill="both", expand=True)

        # Event Bindings for Pan, Zoom, and Crosshair
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<ButtonPress-1>", self._on_pan_start)
        self.canvas.bind("<B1-Motion>", self._on_pan_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_pan_end)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Leave>", self._on_mouse_leave)

        # Mousewheel Zoom (Windows / Linux)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", lambda e: self.zoom_in())
        self.canvas.bind("<Button-5>", lambda e: self.zoom_out())

    def set_candles(self, candles: List[NormalizedCandle], symbol: str = ""):
        """Load new candle series into chart and reset viewport to latest bars"""
        self.candles = list(candles)
        n = len(self.candles)
        if n > 0:
            self.view_count = min(60, n)
            self.view_start = max(0, n - self.view_count)
            sym_title = f"{symbol or self.candles[-1].symbol} ({self.candles[-1].timeframe.upper()})"
            self.lbl_symbol_info.config(text=sym_title)
        else:
            self.lbl_symbol_info.config(text="No Data Available")
            self.lbl_ohlcv_hud.config(text="O: -  H: -  L: -  C: -  Vol: -")

        self.redraw()

    def zoom_in(self):
        """Zoom in by reducing visible candle count"""
        if self.view_count > 15:
            self.view_count = max(15, int(self.view_count * 0.85))
            n = len(self.candles)
            self.view_start = max(0, min(self.view_start, n - self.view_count))
            self.redraw()

    def zoom_out(self):
        """Zoom out by increasing visible candle count"""
        n = len(self.candles)
        if self.view_count < n:
            self.view_count = min(n, int(self.view_count * 1.25))
            self.view_start = max(0, min(self.view_start, n - self.view_count))
            self.redraw()

    def reset_view(self):
        """Reset view to show latest candles"""
        n = len(self.candles)
        if n > 0:
            self.view_count = min(60, n)
            self.view_start = max(0, n - self.view_count)
            self.redraw()

    def _on_resize(self, event):
        self.redraw()

    def _on_pan_start(self, event):
        self._pan_start_x = event.x
        self._pan_start_view = self.view_start

    def _on_pan_drag(self, event):
        if self._pan_start_x is None or not self.candles:
            return
        dx = event.x - self._pan_start_x
        width = self.canvas.winfo_width() - 80
        if width <= 0:
            return
        candle_width = width / self.view_count
        candles_shifted = int(dx / candle_width)

        n = len(self.candles)
        new_start = self._pan_start_view - candles_shifted
        self.view_start = max(0, min(new_start, n - self.view_count))
        self.redraw()

    def _on_pan_end(self, event):
        self._pan_start_x = None
        self._pan_start_view = None

    def _on_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def _on_mouse_move(self, event):
        self._hover_x = event.x
        self._hover_y = event.y
        self.redraw()

    def _on_mouse_leave(self, event):
        self._hover_x = None
        self._hover_y = None
        self.redraw()

    def redraw(self):
        """Main chart layout and graphics rendering pipeline"""
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 100 or height < 100:
            return

        if not self.candles:
            self.canvas.create_text(
                width / 2, height / 2,
                text="Awaiting Candlestick Data...",
                font=Theme.font_subtitle(),
                fill=Theme.TEXT_MUTED
            )
            return

        # Layout Geometry
        right_margin = 75
        bottom_margin = 25
        top_margin = 15
        left_margin = 15

        chart_w = width - left_margin - right_margin

        # Split Main Chart vs Sub-Chart (Volume / RSI / MACD)
        has_sub = self.sub_chart_mode != "none"
        if has_sub:
            main_h = (height - top_margin - bottom_margin) * 0.72
            sub_y = top_margin + main_h + 10
            sub_h = height - bottom_margin - sub_y
        else:
            main_h = height - top_margin - bottom_margin
            sub_y = 0
            sub_h = 0

        # Viewport Slice
        n = len(self.candles)
        end_idx = min(n, self.view_start + self.view_count)
        visible_candles = self.candles[self.view_start : end_idx]
        v_count = len(visible_candles)

        if v_count == 0:
            return

        # Price Extrema
        highs = [c.high for c in visible_candles]
        lows = [c.low for c in visible_candles]
        min_p = min(lows)
        max_p = max(highs)
        p_padding = (max_p - min_p) * 0.05 or 1.0
        min_p -= p_padding
        max_p += p_padding
        price_range = max_p - min_p or 1.0

        def price_to_y(p: float) -> float:
            return top_margin + main_h - ((p - min_p) / price_range * main_h)

        def y_to_price(y: float) -> float:
            return min_p + ((top_margin + main_h - y) / main_h * price_range)

        # Grid lines (Price Axis)
        grid_steps = 6
        for i in range(grid_steps + 1):
            gp = min_p + (price_range * (i / grid_steps))
            gy = price_to_y(gp)
            self.canvas.create_line(left_margin, gy, width - right_margin, gy, fill="#131B2B", dash=(2, 4))
            self.canvas.create_text(
                width - right_margin + 6, gy,
                text=f"{gp:.2f}",
                font=("Consolas", 8),
                fill=Theme.TEXT_MUTED,
                anchor="w"
            )

        # Candle Rendering
        slot_w = chart_w / v_count
        body_w = max(2.0, slot_w * 0.72)

        # Precompute indicators across full dataset for continuity
        full_closes = [c.close for c in self.candles]
        full_highs = [c.high for c in self.candles]
        full_lows = [c.low for c in self.candles]

        ema9 = calculate_ema(full_closes, 9) if self.show_ema9 else None
        ema21 = calculate_ema(full_closes, 21) if self.show_ema21 else None
        ema50 = calculate_ema(full_closes, 50) if self.show_ema50 else None
        ema200 = calculate_ema(full_closes, 200) if self.show_ema200 else None
        bb_upper, bb_mid, bb_lower, _ = calculate_bollinger_bands(full_closes, 20, 2.0) if self.show_bollinger else (None, None, None, None)

        candle_centers = []

        for i, c in enumerate(visible_candles):
            global_idx = self.view_start + i
            cx = left_margin + (i * slot_w) + (slot_w / 2)
            candle_centers.append((cx, c, global_idx))

            is_bull = c.close >= c.open
            color = Theme.ACCENT_EMERALD if is_bull else Theme.ACCENT_ROSE
            wick_color = color

            y_high = price_to_y(c.high)
            y_low = price_to_y(c.low)
            y_open = price_to_y(c.open)
            y_close = price_to_y(c.close)

            # Draw Wick
            self.canvas.create_line(cx, y_high, cx, y_low, fill=wick_color, width=1)

            # Draw Body
            y_top = min(y_open, y_close)
            y_bot = max(y_open, y_close)
            if y_bot - y_top < 1:
                y_bot = y_top + 1  # Doji bar minimum 1px

            self.canvas.create_rectangle(
                cx - (body_w / 2), y_top,
                cx + (body_w / 2), y_bot,
                fill=color,
                outline=color
            )

        # Draw Indicator Overlays on Main Chart
        self._draw_overlay_curve(candle_centers, ema9, Theme.ACCENT_CYAN, price_to_y, width=1)
        self._draw_overlay_curve(candle_centers, ema21, Theme.ACCENT_GOLD, price_to_y, width=1)
        self._draw_overlay_curve(candle_centers, ema50, "#FF6B6B", price_to_y, width=1)
        self._draw_overlay_curve(candle_centers, ema200, "#A78BFA", price_to_y, width=1.5)

        # Draw Bollinger Bands (Cloud / Bands)
        if self.show_bollinger and bb_upper and bb_lower:
            self._draw_overlay_curve(candle_centers, bb_upper, "#38BDF8", price_to_y, width=1, dash=(3, 3))
            self._draw_overlay_curve(candle_centers, bb_mid, "#94A3B8", price_to_y, width=1, dash=(2, 2))
            self._draw_overlay_curve(candle_centers, bb_lower, "#38BDF8", price_to_y, width=1, dash=(3, 3))

        # 3. Sub-Chart Panel Rendering
        if has_sub and sub_h > 20:
            # Sub-panel border
            self.canvas.create_line(left_margin, sub_y - 5, width - right_margin, sub_y - 5, fill="#1E293B", width=1)

            if self.sub_chart_mode == "volume":
                self._render_volume_subchart(visible_candles, candle_centers, sub_y, sub_h, left_margin, width - right_margin)
            elif self.sub_chart_mode == "rsi":
                self._render_rsi_subchart(candle_centers, full_closes, sub_y, sub_h, left_margin, width - right_margin)
            elif self.sub_chart_mode == "macd":
                self._render_macd_subchart(candle_centers, full_closes, sub_y, sub_h, left_margin, width - right_margin)

        # 4. Interactive Crosshair & HUD
        self._render_crosshair(candle_centers, price_to_y, y_to_price, left_margin, width - right_margin, top_margin, height - bottom_margin)

    def _draw_overlay_curve(self, candle_centers, indicator_series, color, price_to_y, width=1, dash=None):
        if not indicator_series:
            return
        points = []
        for cx, _, global_idx in candle_centers:
            if global_idx < len(indicator_series):
                val = indicator_series[global_idx]
                if val is not None:
                    points.extend([cx, price_to_y(val)])

        if len(points) >= 4:
            self.canvas.create_line(points, fill=color, width=width, dash=dash, smooth=False)

    def _render_volume_subchart(self, visible_candles, candle_centers, sub_y, sub_h, x_min, x_max):
        vols = [c.volume for c in visible_candles]
        max_v = max(vols) if vols and max(vols) > 0 else 1.0

        # Sub-chart label
        self.canvas.create_text(x_min + 4, sub_y + 4, text="VOL", font=("Consolas", 8, "bold"), fill=Theme.TEXT_MUTED, anchor="nw")

        for cx, c, _ in candle_centers:
            v_height = (c.volume / max_v) * sub_h
            vy1 = sub_y + sub_h - v_height
            vy2 = sub_y + sub_h
            v_color = Theme.ACCENT_EMERALD if c.close >= c.open else Theme.ACCENT_ROSE
            bw = max(2.0, (x_max - x_min) / len(visible_candles) * 0.6)
            self.canvas.create_rectangle(cx - bw/2, vy1, cx + bw/2, vy2, fill=v_color, outline=v_color)

    def _render_rsi_subchart(self, candle_centers, full_closes, sub_y, sub_h, x_min, x_max):
        rsi = calculate_rsi(full_closes, 14)
        self.canvas.create_text(x_min + 4, sub_y + 4, text="RSI (14)", font=("Consolas", 8, "bold"), fill=Theme.TEXT_MUTED, anchor="nw")

        def rsi_to_y(val: float) -> float:
            return sub_y + sub_h - (val / 100.0 * sub_h)

        # 70 and 30 threshold lines
        y70 = rsi_to_y(70)
        y30 = rsi_to_y(30)
        self.canvas.create_line(x_min, y70, x_max, y70, fill="#334155", dash=(2, 4))
        self.canvas.create_line(x_min, y30, x_max, y30, fill="#334155", dash=(2, 4))
        self.canvas.create_text(x_max + 6, y70, text="70", font=("Consolas", 7), fill=Theme.TEXT_MUTED, anchor="w")
        self.canvas.create_text(x_max + 6, y30, text="30", font=("Consolas", 7), fill=Theme.TEXT_MUTED, anchor="w")

        # RSI curve
        points = []
        for cx, _, g_idx in candle_centers:
            if g_idx < len(rsi) and rsi[g_idx] is not None:
                points.extend([cx, rsi_to_y(rsi[g_idx])])

        if len(points) >= 4:
            self.canvas.create_line(points, fill=Theme.ACCENT_GOLD, width=1.2)

    def _render_macd_subchart(self, candle_centers, full_closes, sub_y, sub_h, x_min, x_max):
        macd_l, sig_l, hist_l = calculate_macd(full_closes, 12, 26, 9)
        self.canvas.create_text(x_min + 4, sub_y + 4, text="MACD (12,26,9)", font=("Consolas", 8, "bold"), fill=Theme.TEXT_MUTED, anchor="nw")

        visible_hists = [hist_l[g_idx] for _, _, g_idx in candle_centers if g_idx < len(hist_l) and hist_l[g_idx] is not None]
        max_h = max([abs(h) for h in visible_hists]) if visible_hists else 1.0
        zero_y = sub_y + (sub_h / 2)

        self.canvas.create_line(x_min, zero_y, x_max, zero_y, fill="#334155", dash=(2, 2))

        bw = max(2.0, (x_max - x_min) / len(candle_centers) * 0.5)

        for cx, _, g_idx in candle_centers:
            if g_idx < len(hist_l) and hist_l[g_idx] is not None:
                h_val = hist_l[g_idx]
                h_px = (h_val / max_h) * (sub_h / 2)
                h_color = Theme.ACCENT_EMERALD if h_val >= 0 else Theme.ACCENT_ROSE
                self.canvas.create_rectangle(cx - bw/2, zero_y - h_px, cx + bw/2, zero_y, fill=h_color, outline=h_color)

    def _render_crosshair(self, candle_centers, price_to_y, y_to_price, x_min, x_max, y_min, y_max):
        if self._hover_x is None or self._hover_y is None:
            return

        hx = self._hover_x
        hy = self._hover_y

        if not (x_min <= hx <= x_max and y_min <= hy <= y_max):
            return

        # Find closest candle
        closest = min(candle_centers, key=lambda c: abs(c[0] - hx))
        snap_x, candle, _ = closest

        # 1. Vertical & Horizontal Dotted Crosshair
        self.canvas.create_line(snap_x, y_min, snap_x, y_max, fill="#475569", dash=(3, 3))
        self.canvas.create_line(x_min, hy, x_max, hy, fill="#475569", dash=(3, 3))

        # 2. Right Price Badge
        hover_price = y_to_price(hy)
        self.canvas.create_rectangle(x_max, hy - 9, x_max + 65, hy + 9, fill="#1E293B", outline=Theme.ACCENT_CYAN)
        self.canvas.create_text(x_max + 4, hy, text=f"{hover_price:.2f}", font=("Consolas", 8, "bold"), fill=Theme.ACCENT_CYAN, anchor="w")

        # 3. Bottom Date Badge
        date_str = candle.timestamp[:16]
        self.canvas.create_rectangle(snap_x - 45, y_max, snap_x + 45, y_max + 18, fill="#1E293B", outline=Theme.BORDER_SUBTLE)
        self.canvas.create_text(snap_x, y_max + 9, text=date_str, font=("Consolas", 7), fill=Theme.TEXT_SECONDARY)

        # 4. Update HUD Header
        change_sign = "+" if candle.close >= candle.open else ""
        diff = candle.close - candle.open
        pct = (diff / candle.open * 100.0) if candle.open > 0 else 0.0

        hud_text = f"O: {candle.open:.2f}  H: {candle.high:.2f}  L: {candle.low:.2f}  C: {candle.close:.2f}  ({change_sign}{pct:.2f}%)  Vol: {candle.volume:,.0f}  [{candle.timestamp}]"
        self.lbl_ohlcv_hud.config(text=hud_text, fg=Theme.ACCENT_EMERALD if diff >= 0 else Theme.ACCENT_ROSE)
