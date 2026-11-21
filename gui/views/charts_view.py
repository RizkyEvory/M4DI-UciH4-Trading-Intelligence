"""
M4DI~UciH4 Trading Intelligence System
Interactive Charts & Technical Analysis View
High-performance Candlestick Canvas with Pan, Zoom, Crosshair, Multi-Timeframe, and Overlays.
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from typing import Optional, List, Dict, Any

from config.constants import (
    TF_1M, TF_5M, TF_15M, TF_30M, TF_1H, TF_4H, TF_1D, TF_1W,
    TIMEFRAMES,
    PROVIDER_FINNHUB, PROVIDER_TWELVE_DATA
)
from config.theme import Theme
from gui.components.cards import CardFrame, StatCard
from gui.components.candlestick_chart import CandlestickChart
from api.models import NormalizedCandle
from analytics.trend import TrendAnalyzer
from analytics.volatility import VolatilityAnalyzer
from analytics.volume import VolumeAnalyzer
from analytics.technical_score import TechnicalScoreCalculator
from analytics.indicators import calculate_rsi, calculate_macd
from core.logger import get_app_logger

logger = get_app_logger("ChartsView")


class ChartsView(tk.Frame):
    """
    Advanced Interactive Candlestick Charting Workspace — Enterprise Edition.
    Includes Timeframe Selectors, Indicator Overlays, Volume, RSI, MACD, and Crosshair Telemetry.
    """

    DEFAULT_SYMBOLS = ["XAU/USD", "EUR/USD", "GBP/USD", "BTC/USD", "AAPL", "NVDA", "NAS100", "US30"]

    def __init__(self, parent, app_context, *args, **kwargs):
        super().__init__(parent, bg=Theme.BG_CONTENT, padx=16, pady=12, *args, **kwargs)
        self.ctx = app_context

        self.current_symbol = "XAU/USD"
        self.current_timeframe = TF_1D
        self._is_loading = False

        self._build_ui()
        self.load_symbol_candles(self.current_symbol, self.current_timeframe)

    def _build_ui(self):
        # 1. Top Control Strip: Symbol & Quick Bar
        top_bar = tk.Frame(self, bg=Theme.BG_CONTENT)
        top_bar.pack(fill="x", pady=(0, 8))

        tk.Label(
            top_bar,
            text="Symbol:",
            font=Theme.font_body_bold(),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CONTENT
        ).pack(side="left", padx=(0, 6))

        self.sym_var = tk.StringVar(value=self.current_symbol)
        self.sym_combo = ttk.Combobox(
            top_bar,
            textvariable=self.sym_var,
            values=self.DEFAULT_SYMBOLS,
            width=10,
            style="TCombobox"
        )
        self.sym_combo.pack(side="left", padx=(0, 6))
        self.sym_combo.bind("<Return>", lambda e: self._on_symbol_submit())

        btn_load = ttk.Button(
            top_bar,
            text="Load",
            style="Primary.TButton",
            command=self._on_symbol_submit
        )
        btn_load.pack(side="left", padx=(0, 14))

        # Timeframe Selector Buttons
        tk.Label(
            top_bar,
            text="Timeframe:",
            font=Theme.font_body_bold(),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CONTENT
        ).pack(side="left", padx=(0, 6))

        self.tf_buttons: Dict[str, tk.Button] = {}
        tf_display_list = [TF_1M, TF_5M, TF_15M, TF_30M, TF_1H, TF_4H, TF_1D, TF_1W]

        for tf in tf_display_list:
            btn = tk.Button(
                top_bar,
                text=tf.upper(),
                font=Theme.font_caption(),
                bg=Theme.ACCENT_CYAN if tf == self.current_timeframe else Theme.BG_CARD_ALT,
                fg="#042F2E" if tf == self.current_timeframe else Theme.TEXT_SECONDARY,
                activebackground=Theme.ACCENT_CYAN,
                activeforeground="#042F2E",
                relief="flat",
                padx=6,
                pady=2,
                cursor="hand2",
                command=lambda t=tf: self._change_timeframe(t)
            )
            btn.pack(side="left", padx=2)
            self.tf_buttons[tf] = btn

        # Right Zoom and Reset Tools
        btn_reset = ttk.Button(top_bar, text="↺ Reset", style="Secondary.TButton", command=lambda: self.chart.reset_view())
        btn_reset.pack(side="right", padx=(4, 0))

        btn_zoom_out = ttk.Button(top_bar, text="🔍 -", style="Secondary.TButton", width=4, command=lambda: self.chart.zoom_out())
        btn_zoom_out.pack(side="right", padx=(4, 0))

        btn_zoom_in = ttk.Button(top_bar, text="🔍 +", style="Secondary.TButton", width=4, command=lambda: self.chart.zoom_in())
        btn_zoom_in.pack(side="right", padx=(4, 0))

        # 2. Indicator Toggles Strip
        ind_bar = tk.Frame(self, bg=Theme.BG_CARD_ALT, padx=10, pady=4, highlightbackground=Theme.BORDER_SUBTLE, highlightthickness=1)
        ind_bar.pack(fill="x", pady=(0, 8))

        # Overlay Checkboxes
        self.var_ema9 = tk.BooleanVar(value=True)
        self.var_ema21 = tk.BooleanVar(value=True)
        self.var_ema50 = tk.BooleanVar(value=False)
        self.var_ema200 = tk.BooleanVar(value=False)
        self.var_bb = tk.BooleanVar(value=True)

        self._add_toggle_check(ind_bar, "EMA 9", self.var_ema9, Theme.ACCENT_CYAN, self._update_overlays)
        self._add_toggle_check(ind_bar, "EMA 21", self.var_ema21, Theme.ACCENT_GOLD, self._update_overlays)
        self._add_toggle_check(ind_bar, "EMA 50", self.var_ema50, "#FF6B6B", self._update_overlays)
        self._add_toggle_check(ind_bar, "EMA 200", self.var_ema200, "#A78BFA", self._update_overlays)
        self._add_toggle_check(ind_bar, "Bollinger (20,2)", self.var_bb, "#38BDF8", self._update_overlays)

        # Sub-Chart Dropdown
        tk.Label(ind_bar, text="Sub-Indicator:", font=Theme.font_caption(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD_ALT).pack(side="left", padx=(16, 6))
        self.sub_mode_var = tk.StringVar(value="Volume")
        self.sub_combo = ttk.Combobox(
            ind_bar,
            textvariable=self.sub_mode_var,
            values=["Volume", "RSI (14)", "MACD (12,26,9)", "None"],
            state="readonly",
            width=14,
            style="TCombobox"
        )
        self.sub_combo.pack(side="left")
        self.sub_combo.bind("<<ComboboxSelected>>", self._on_sub_mode_changed)

        self.lbl_status = tk.Label(ind_bar, text="", font=Theme.font_caption(), fg=Theme.ACCENT_CYAN, bg=Theme.BG_CARD_ALT)
        self.lbl_status.pack(side="right", padx=(8, 0))

        # 3. Main Chart Canvas Widget
        chart_card = CardFrame(self, title="Interactive Candlestick Canvas", subtitle="Institutional Technical Analysis")
        chart_card.pack(fill="both", expand=True, pady=(0, 8))

        self.chart = CandlestickChart(chart_card.body, bg_color=Theme.BG_CARD)
        self.chart.pack(fill="both", expand=True)

        # 4. Bottom Metrics Strip (Trend, Volatility, RSI, Tech Score)
        self.telemetry_bar = tk.Frame(self, bg=Theme.BG_CARD_ALT, padx=12, pady=6, highlightbackground=Theme.BORDER_SUBTLE, highlightthickness=1)
        self.telemetry_bar.pack(fill="x")

        self.lbl_tel_price = tk.Label(self.telemetry_bar, text="Price: -", font=Theme.font_body_bold(), fg=Theme.TEXT_PRIMARY, bg=Theme.BG_CARD_ALT)
        self.lbl_tel_price.pack(side="left", padx=(0, 16))

        self.lbl_tel_trend = tk.Label(self.telemetry_bar, text="Trend: -", font=Theme.font_body(), fg=Theme.ACCENT_CYAN, bg=Theme.BG_CARD_ALT)
        self.lbl_tel_trend.pack(side="left", padx=(0, 16))

        self.lbl_tel_vol = tk.Label(self.telemetry_bar, text="Volatility: -", font=Theme.font_body(), fg=Theme.ACCENT_GOLD, bg=Theme.BG_CARD_ALT)
        self.lbl_tel_vol.pack(side="left", padx=(0, 16))

        self.lbl_tel_rsi = tk.Label(self.telemetry_bar, text="RSI: -", font=Theme.font_body(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD_ALT)
        self.lbl_tel_rsi.pack(side="left", padx=(0, 16))

        self.lbl_tel_score = tk.Label(self.telemetry_bar, text="Score: -", font=Theme.font_body_bold(), fg=Theme.ACCENT_EMERALD, bg=Theme.BG_CARD_ALT)
        self.lbl_tel_score.pack(side="right")

    def _add_toggle_check(self, parent, label, var, color, command):
        chk = tk.Checkbutton(
            parent,
            text=label,
            variable=var,
            bg=Theme.BG_CARD_ALT,
            fg=color,
            selectcolor=Theme.BG_INPUT,
            activebackground=Theme.BG_CARD_ALT,
            activeforeground=color,
            font=Theme.font_caption(),
            command=command
        )
        chk.pack(side="left", padx=(0, 8))

    def _update_overlays(self):
        self.chart.show_ema9 = self.var_ema9.get()
        self.chart.show_ema21 = self.var_ema21.get()
        self.chart.show_ema50 = self.var_ema50.get()
        self.chart.show_ema200 = self.var_ema200.get()
        self.chart.show_bollinger = self.var_bb.get()
        self.chart.redraw()

    def _on_sub_mode_changed(self, event=None):
        mode = self.sub_mode_var.get().lower()
        if "rsi" in mode:
            self.chart.sub_chart_mode = "rsi"
        elif "macd" in mode:
            self.chart.sub_chart_mode = "macd"
        elif "none" in mode:
            self.chart.sub_chart_mode = "none"
        else:
            self.chart.sub_chart_mode = "volume"
        self.chart.redraw()

    def _on_symbol_submit(self):
        sym = self.sym_var.get().strip().upper()
        if sym:
            self.current_symbol = sym
            self.load_symbol_candles(self.current_symbol, self.current_timeframe)

    def _change_timeframe(self, tf: str):
        self.current_timeframe = tf
        for t, btn in self.tf_buttons.items():
            if t == tf:
                btn.config(bg=Theme.ACCENT_CYAN, fg="#042F2E")
            else:
                btn.config(bg=Theme.BG_CARD_ALT, fg=Theme.TEXT_SECONDARY)
        self.load_symbol_candles(self.current_symbol, self.current_timeframe)

    def load_symbol_candles(self, symbol: str, timeframe: str):
        """Asynchronously load candlestick bars and calculate indicators"""
        if self._is_loading:
            return

        self._is_loading = True
        self.lbl_status.config(text=f"Loading {symbol} ({timeframe})...", fg=Theme.ACCENT_CYAN)

        def fetch_task():
            candles = self.ctx.market_data.get_candles(symbol, timeframe=timeframe, count=100)
            return candles

        def on_done(candles):
            self._is_loading = False
            self.lbl_status.config(text="")
            if not candles:
                self.lbl_status.config(text="No data returned", fg=Theme.ACCENT_ROSE)
                return

            self.chart.set_candles(candles, symbol=f"{symbol} ({timeframe.upper()})")
            self._update_telemetry_banner(candles)

        def on_err(err):
            self._is_loading = False
            self.lbl_status.config(text=f"Failed: {err}", fg=Theme.ACCENT_ROSE)
            messagebox.showerror("Chart Data Error", str(err))

        self.ctx.tasks.submit_task(
            f"Load Chart {symbol}",
            fetch_task,
            on_complete=on_done,
            on_error=on_err
        )

    def _update_telemetry_banner(self, candles: List[NormalizedCandle]):
        if len(candles) < 2:
            return

        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        volumes = [c.volume for c in candles]

        curr_price = closes[-1]
        prev_close = closes[-2]
        chg_pct = (curr_price - prev_close) / prev_close * 100.0 if prev_close > 0 else 0.0
        sign = "+" if chg_pct >= 0 else ""

        # Trend & Volatility
        trend_info = TrendAnalyzer.analyze(highs, lows, closes)
        vol_info = VolatilityAnalyzer.analyze(highs, lows, closes)
        vol_data = VolumeAnalyzer.analyze(closes, volumes)

        rsi_vals = calculate_rsi(closes, 14)
        latest_rsi = rsi_vals[-1] or 50.0

        macd_l, sig_l, hist_l = calculate_macd(closes, 12, 26, 9)
        latest_hist = hist_l[-1] or 0.0

        score = TechnicalScoreCalculator.calculate_score(
            trend_info=trend_info,
            rsi_val=latest_rsi,
            macd_hist=latest_hist,
            volatility_info=vol_info,
            volume_info=vol_data
        )

        p_color = Theme.ACCENT_EMERALD if chg_pct >= 0 else Theme.ACCENT_ROSE
        self.lbl_tel_price.config(text=f"Price: {curr_price:.2f} ({sign}{chg_pct:.2f}%)", fg=p_color)
        self.lbl_tel_trend.config(text=f"Trend: {trend_info['overall_trend']} ({trend_info['trend_strength']}%)")
        self.lbl_tel_vol.config(text=f"Vol Regime: {vol_info['regime']} (ATR: {vol_info['atr_percent']}%)")
        self.lbl_tel_rsi.config(text=f"RSI: {latest_rsi:.1f}")
        self.lbl_tel_score.config(text=f"Technical Score: {score}/100")
