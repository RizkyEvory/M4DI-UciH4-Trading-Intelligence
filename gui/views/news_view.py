"""
M4DI~UciH4 Trading Intelligence System
News Intelligence & Sentiment Analysis GUI View — Enterprise Edition
Integrates Finnhub & NewsAPI, provides 11-category classification, local NLP sentiment scoring,
multi-parameter filters, and full article inspection.
"""
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional

from config.theme import Theme
from config.constants import (
    NEWS_CATEGORIES,
    SENTIMENTS,
    IMPACT_LEVELS,
    SENTIMENT_POSITIVE,
    SENTIMENT_NEGATIVE,
    IMPACT_CRITICAL,
    IMPACT_HIGH,
    IMPACT_MEDIUM,
    IMPACT_LOW
)
from gui.components.cards import CardFrame, StatCard
from gui.components.tables import SortableTreeview
from news.models import EnrichedNewsArticle
from utils.formatters import format_timestamp


class NewsView(tk.Frame):
    """Real-time News Intelligence, Sentiment Analysis, and Market Impact Hub"""

    def __init__(self, parent, app_context, *args, **kwargs):
        super().__init__(parent, bg=Theme.BG_CONTENT, padx=20, pady=16, *args, **kwargs)
        self.ctx = app_context

        self._all_articles: List[EnrichedNewsArticle] = []
        self._filtered_articles: List[EnrichedNewsArticle] = []
        self._selected_article: Optional[EnrichedNewsArticle] = None

        self._build_ui()
        # Initial load after window mounts
        self.after(200, self._load_initial_news)

    def _build_ui(self):
        # 1. Header Row
        title_box = tk.Frame(self, bg=Theme.BG_CONTENT)
        title_box.pack(fill="x", pady=(0, 14))

        tk.Label(
            title_box,
            text="News Intelligence & Sentiment Analysis",
            font=Theme.font_title(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CONTENT
        ).pack(side="left")

        tk.Label(
            title_box,
            text="Macro events, financial headlines & deterministic NLP sentiment",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CONTENT
        ).pack(side="left", padx=(12, 0), pady=(4, 0))

        tk.Label(
            title_box,
            text=" SENTIMENT & INTELLIGENCE WIRE ",
            font=(Theme.FONT_FAMILY, 8, "bold"),
            fg="#042F2E",
            bg=Theme.ACCENT_CYAN,
            padx=8,
            pady=3
        ).pack(side="right")

        # 2. Telemetry Stat Cards
        stats_row = tk.Frame(self, bg=Theme.BG_CONTENT)
        stats_row.pack(fill="x", pady=(0, 14))
        stats_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="news_stats")

        self.card_total = StatCard(stats_row, icon="📰", value="0", label="Total News Wire", status_text="Deduplicated", accent_color=Theme.ACCENT_CYAN)
        self.card_total.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.card_impact = StatCard(stats_row, icon="⚡", value="0", label="Critical / High Impact", status_text="Market Catalysts", accent_color=Theme.ACCENT_MAGENTA)
        self.card_impact.grid(row=0, column=1, sticky="nsew", padx=(0, 8))

        self.card_bullish = StatCard(stats_row, icon="🐂", value="0%", label="Bullish Sentiment", status_text="Positive Flow", accent_color=Theme.SUCCESS)
        self.card_bullish.grid(row=0, column=2, sticky="nsew", padx=(0, 8))

        self.card_bearish = StatCard(stats_row, icon="🐻", value="0%", label="Bearish Sentiment", status_text="Negative Pressure", accent_color=Theme.ERROR)
        self.card_bearish.grid(row=0, column=3, sticky="nsew")

        # 3. Filter Controls Bar
        filter_card = CardFrame(self, title="News Filtering & Keyword Surveillance")
        filter_card.pack(fill="x", pady=(0, 14))

        f_bar = tk.Frame(filter_card.body, bg=Theme.BG_CARD)
        f_bar.pack(fill="x")

        # Search box
        tk.Label(f_bar, text="Search:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.var_search = tk.StringVar()
        self.entry_search = tk.Entry(
            f_bar,
            textvariable=self.var_search,
            font=Theme.font_body(),
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.ACCENT_CYAN,
            relief="flat",
            width=20
        )
        self.entry_search.pack(side="left", padx=(0, 14), ipady=3)
        self.entry_search.bind("<Return>", lambda e: self._on_filter_changed())

        # Symbol dropdown
        tk.Label(f_bar, text="Symbol:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.var_symbol = tk.StringVar(value="ALL")
        symbols = ["ALL", "XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "AAPL", "NVDA", "MSFT", "TSLA", "BTC"]
        cb_symbol = ttk.Combobox(f_bar, textvariable=self.var_symbol, values=symbols, state="readonly", width=9)
        cb_symbol.pack(side="left", padx=(0, 14))
        cb_symbol.bind("<<ComboboxSelected>>", lambda e: self._on_filter_changed())

        # Category dropdown
        tk.Label(f_bar, text="Category:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.var_category = tk.StringVar(value="ALL")
        cat_choices = ["ALL"] + NEWS_CATEGORIES
        cb_cat = ttk.Combobox(f_bar, textvariable=self.var_category, values=cat_choices, state="readonly", width=18)
        cb_cat.pack(side="left", padx=(0, 14))
        cb_cat.bind("<<ComboboxSelected>>", lambda e: self._on_filter_changed())

        # Sentiment dropdown
        tk.Label(f_bar, text="Sentiment:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.var_sentiment = tk.StringVar(value="ALL")
        cb_sent = ttk.Combobox(f_bar, textvariable=self.var_sentiment, values=["ALL"] + SENTIMENTS, state="readonly", width=10)
        cb_sent.pack(side="left", padx=(0, 14))
        cb_sent.bind("<<ComboboxSelected>>", lambda e: self._on_filter_changed())

        # Impact dropdown
        tk.Label(f_bar, text="Impact:", font=Theme.font_body_bold(), fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD).pack(side="left", padx=(0, 6))
        self.var_impact = tk.StringVar(value="ALL")
        cb_imp = ttk.Combobox(f_bar, textvariable=self.var_impact, values=["ALL"] + IMPACT_LEVELS, state="readonly", width=10)
        cb_imp.pack(side="left", padx=(0, 14))
        cb_imp.bind("<<ComboboxSelected>>", lambda e: self._on_filter_changed())

        # Refresh button
        self.btn_refresh = tk.Button(
            f_bar,
            text="🔄 Refresh Wire",
            font=Theme.font_body_bold(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ACCENT_CYAN,
            activebackground=Theme.BG_SIDEBAR,
            activeforeground=Theme.ACCENT_TURQUOISE,
            relief="flat",
            padx=10,
            pady=3,
            command=self._fetch_news_background
        )
        self.btn_refresh.pack(side="right")

        # Export button
        tk.Button(
            f_bar,
            text="📥 Export",
            font=Theme.font_caption(),
            bg=Theme.BG_CARD_ALT,
            fg=Theme.ACCENT_TURQUOISE,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self._on_export_news
        ).pack(side="right", padx=(0, 8))

        # 4. Main Body: Split Table and Detail Inspector
        body_split = tk.PanedWindow(self, orient="horizontal", bg=Theme.BG_CONTENT, sashwidth=4, bd=0)
        body_split.pack(fill="both", expand=True)

        # Left Pane: Table
        left_card = CardFrame(body_split, title="News Intelligence Wire", subtitle="Deduplicated & scored articles")
        body_split.add(left_card, minsize=500, stretch="always")

        self.table = SortableTreeview(
            left_card.body,
            columns=["timestamp", "symbol", "category", "headline", "source", "sentiment", "impact"],
            headings=["Time", "Sym", "Category", "Headline", "Source", "Sentiment", "Impact"],
            widths=[110, 60, 120, 320, 90, 80, 75]
        )
        self.table.pack(fill="both", expand=True)
        self.table.tree.bind("<<TreeviewSelect>>", self._on_table_select)

        # Configure row tags for visual coloring
        self.table.tree.tag_configure("positive", foreground=Theme.SUCCESS)
        self.table.tree.tag_configure("negative", foreground=Theme.ERROR)
        self.table.tree.tag_configure("critical", foreground=Theme.ACCENT_MAGENTA)

        # Right Pane: Article Detail Inspector
        right_card = CardFrame(body_split, title="Article Intelligence Inspector", subtitle="NLP Breakdown & Market Impact")
        body_split.add(right_card, minsize=380, stretch="never")

        inspector = tk.Frame(right_card.body, bg=Theme.BG_CARD)
        inspector.pack(fill="both", expand=True)

        # Headline
        self.lbl_detail_headline = tk.Label(
            inspector,
            text="Select an article from the wire to inspect details",
            font=Theme.font_subtitle(),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD,
            wraplength=360,
            justify="left",
            anchor="w"
        )
        self.lbl_detail_headline.pack(fill="x", pady=(0, 8))

        # Meta info
        self.lbl_detail_meta = tk.Label(
            inspector,
            text="Source: - | Published: - | Category: -",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD,
            anchor="w"
        )
        self.lbl_detail_meta.pack(fill="x", pady=(0, 10))

        # Badges row
        badges_row = tk.Frame(inspector, bg=Theme.BG_CARD)
        badges_row.pack(fill="x", pady=(0, 12))

        self.lbl_badge_sent = tk.Label(
            badges_row,
            text="SENTIMENT: -",
            font=(Theme.FONT_FAMILY, 8, "bold"),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD_ALT,
            padx=8,
            pady=3
        )
        self.lbl_badge_sent.pack(side="left", padx=(0, 8))

        self.lbl_badge_impact = tk.Label(
            badges_row,
            text="IMPACT: -",
            font=(Theme.FONT_FAMILY, 8, "bold"),
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD_ALT,
            padx=8,
            pady=3
        )
        self.lbl_badge_impact.pack(side="left")

        # NLP Analysis Frame
        nlp_frame = tk.LabelFrame(
            inspector,
            text=" NLP Reasoning & Sentiment Drivers ",
            font=Theme.font_caption(),
            fg=Theme.ACCENT_CYAN,
            bg=Theme.BG_CARD_ALT,
            padx=8,
            pady=6,
            relief="solid",
            bd=1
        )
        nlp_frame.pack(fill="x", pady=(0, 10))

        self.lbl_nlp_reasons = tk.Label(
            nlp_frame,
            text="• Select article to view sentiment cues",
            font=Theme.font_caption(),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD_ALT,
            justify="left",
            wraplength=340,
            anchor="w"
        )
        self.lbl_nlp_reasons.pack(fill="x")

        # Summary box
        tk.Label(
            inspector,
            text="Executive Summary & Article Excerpt:",
            font=Theme.font_caption(),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD,
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        self.txt_summary = tk.Text(
            inspector,
            font=Theme.font_body(),
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            relief="flat",
            wrap="word",
            height=8
        )
        self.txt_summary.pack(fill="both", expand=True, pady=(0, 10))
        self.txt_summary.insert("1.0", "No article selected.")
        self.txt_summary.configure(state="disabled")

        # Open in Browser button
        self.btn_open_article = tk.Button(
            inspector,
            text="🌐 Open Full Article in Browser",
            font=Theme.font_body_bold(),
            bg=Theme.ACCENT_CYAN,
            fg="#042F2E",
            activebackground=Theme.ACCENT_TURQUOISE,
            activeforeground="#042F2E",
            relief="flat",
            pady=6,
            command=self._open_in_browser,
            state="disabled"
        )
        self.btn_open_article.pack(fill="x")

    def _load_initial_news(self):
        """Initial background fetch"""
        self._fetch_news_background()

    def _fetch_news_background(self):
        """Query NewsEngine in background worker thread"""
        self.btn_refresh.configure(text="⏳ Fetching...", state="disabled")

        def task():
            return self.ctx.news_engine.get_market_news(limit=60)

        def on_complete(articles):
            self.btn_refresh.configure(text="🔄 Refresh Wire", state="normal")
            self._all_articles = articles or []
            self._apply_filters()

        def on_error(err):
            self.btn_refresh.configure(text="🔄 Refresh Wire", state="normal")
            messagebox.showwarning("News Fetch Error", f"Failed to retrieve news wire: {err}")

        self.ctx.tasks.submit_task(
            "FetchNewsWire",
            task,
            on_success=on_complete,
            on_error=on_error
        )

    def _on_filter_changed(self):
        """User changed a filter dropdown or search input"""
        self._apply_filters()

    def _apply_filters(self):
        """Filter articles and update table"""
        sym = self.var_symbol.get()
        cat = self.var_category.get()
        sent = self.var_sentiment.get()
        imp = self.var_impact.get()
        q = self.var_search.get()

        filtered = self.ctx.news_engine.filter_news(
            self._all_articles,
            symbol=sym,
            category=cat,
            sentiment=sent,
            impact=imp,
            search_text=q
        )
        self._filtered_articles = filtered

        # Update stats
        total = len(self._all_articles)
        self.card_total.set_value(str(total))

        crit_high = sum(1 for a in self._all_articles if a.impact in (IMPACT_CRITICAL, IMPACT_HIGH))
        self.card_impact.set_value(str(crit_high))

        bullish_count = sum(1 for a in self._all_articles if a.sentiment == SENTIMENT_POSITIVE)
        bearish_count = sum(1 for a in self._all_articles if a.sentiment == SENTIMENT_NEGATIVE)
        bull_pct = round((bullish_count / max(1, total)) * 100)
        bear_pct = round((bearish_count / max(1, total)) * 100)

        self.card_bullish.set_value(f"{bull_pct}%")
        self.card_bearish.set_value(f"{bear_pct}%")

        # Repopulate table
        self.table.clear()
        for idx, a in enumerate(filtered):
            # Assign tag
            tag = ""
            if a.impact == IMPACT_CRITICAL:
                tag = "critical"
            elif a.sentiment == SENTIMENT_POSITIVE:
                tag = "positive"
            elif a.sentiment == SENTIMENT_NEGATIVE:
                tag = "negative"

            time_str = a.published_at.split()[1][:5] if " " in a.published_at else a.published_at[:10]

            self.table.insert(
                iid=str(idx),
                values=(
                    time_str,
                    a.symbol or "MACRO",
                    a.category,
                    a.title,
                    a.source,
                    f"{a.sentiment} ({a.sentiment_score:+.2f})",
                    f"{a.impact} ({a.impact_score:.0f})"
                ),
                tags=(tag,) if tag else ()
            )

        # Select first if available
        if filtered:
            self.table.tree.selection_set("0")
            self._on_table_select(None)
        else:
            self._clear_detail()

    def _on_table_select(self, event):
        """User selected a row in the news table"""
        selected = self.table.tree.selection()
        if not selected:
            return

        try:
            idx = int(selected[0])
            if 0 <= idx < len(self._filtered_articles):
                article = self._filtered_articles[idx]
                self._display_article(article)
        except Exception:
            pass

    def _display_article(self, article: EnrichedNewsArticle):
        """Populate article details panel"""
        self._selected_article = article

        self.lbl_detail_headline.configure(text=article.title)
        self.lbl_detail_meta.configure(
            text=f"Source: {article.source} | Published: {article.published_at} | Category: {article.category}"
        )

        # Sentiment badge
        sent_color = Theme.SUCCESS if article.sentiment == SENTIMENT_POSITIVE else (
            Theme.ERROR if article.sentiment == SENTIMENT_NEGATIVE else Theme.TEXT_MUTED
        )
        self.lbl_badge_sent.configure(
            text=f"SENTIMENT: {article.sentiment} ({article.sentiment_score:+.2f})",
            fg=sent_color
        )

        # Impact badge
        imp_color = Theme.ACCENT_MAGENTA if article.impact in (IMPACT_CRITICAL, IMPACT_HIGH) else Theme.ACCENT_CYAN
        self.lbl_badge_impact.configure(
            text=f"IMPACT: {article.impact} ({article.impact_score:.0f}/100)",
            fg=imp_color
        )

        # NLP reasons
        reasons_text = "\n".join([f"• {r}" for r in article.sentiment_reasons[:4]]) or "• Neutral baseline"
        self.lbl_nlp_reasons.configure(text=reasons_text)

        # Summary box
        self.txt_summary.configure(state="normal")
        self.txt_summary.delete("1.0", "end")
        self.txt_summary.insert("1.0", article.summary or article.description or article.title)
        self.txt_summary.configure(state="disabled")

        # Browser button
        if article.url:
            self.btn_open_article.configure(state="normal")
        else:
            self.btn_open_article.configure(state="disabled")

    def _clear_detail(self):
        """Reset detail panel to empty state"""
        self._selected_article = None
        self.lbl_detail_headline.configure(text="No articles match the current filter")
        self.lbl_detail_meta.configure(text="Source: - | Published: - | Category: -")
        self.lbl_badge_sent.configure(text="SENTIMENT: -", fg=Theme.TEXT_MUTED)
        self.lbl_badge_impact.configure(text="IMPACT: -", fg=Theme.TEXT_MUTED)
        self.lbl_nlp_reasons.configure(text="• No article selected")
        self.txt_summary.configure(state="normal")
        self.txt_summary.delete("1.0", "end")
        self.txt_summary.insert("1.0", "No matching news items.")
        self.txt_summary.configure(state="disabled")
        self.btn_open_article.configure(state="disabled")

    def _open_in_browser(self):
        """Open selected article in system default browser"""
        if self._selected_article and self._selected_article.url:
            webbrowser.open(self._selected_article.url)

    def _on_export_news(self):
        """Export news intelligence articles to CSV or JSON"""
        articles = self._cached_articles
        if not articles:
            messagebox.showinfo("Export", "No news articles to export.")
            return

        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export News Intelligence Data",
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet", "*.csv"), ("JSON Data", "*.json")]
        )
        if path:
            fmt = "json" if path.endswith(".json") else "csv"
            ok, msg = self.ctx.exporter.export_news(articles, path, fmt=fmt)
            if ok:
                messagebox.showinfo("Export Successful", msg)
            else:
                messagebox.showerror("Export Failed", msg)
