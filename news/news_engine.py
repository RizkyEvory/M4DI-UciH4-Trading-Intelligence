"""
M4DI~UciH4 Trading Intelligence System
Central News Intelligence Engine
Coordinates Finnhub and NewsAPI clients, performs deduplication, categorization,
sentiment quantification, and symbol-level sentiment aggregation.
"""
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime

from config.constants import (
    PROVIDER_FINNHUB,
    PROVIDER_NEWS_API,
    NEWS_CATEGORIES,
    SENTIMENT_POSITIVE,
    SENTIMENT_NEGATIVE,
    SENTIMENT_NEUTRAL,
    IMPACT_CRITICAL,
    IMPACT_HIGH
)
from api.models import NormalizedNews
from news.models import EnrichedNewsArticle
from news.deduplicator import NewsDeduplicator
from core.logger import get_app_logger

logger = get_app_logger("NewsEngine")


class NewsEngine:
    """Central orchestrator for news intelligence, sentiment analysis, and market impact"""

    def __init__(self, finnhub_client=None, newsapi_client=None, cache=None):
        self.finnhub = finnhub_client
        self.newsapi = newsapi_client
        self.cache = cache
        self._lock = threading.RLock()
        self._memory_cache: List[EnrichedNewsArticle] = []

    def get_cached_articles(self, limit: int = 50) -> List[EnrichedNewsArticle]:
        """Return memory-cached enriched articles without outbound network calls"""
        with self._lock:
            return list(self._memory_cache[:limit])

    def get_market_news(self, category: str = "general", limit: int = 50) -> List[EnrichedNewsArticle]:
        """
        Fetch macro and market financial headlines across Finnhub & NewsAPI.
        Deduplicates, classifies into 11 categories, and calculates sentiment/impact.
        """
        raw_articles: List[NormalizedNews] = []

        # 1. Fetch from Finnhub
        if self.finnhub:
            try:
                fh_news = self.finnhub.get_market_news(category=category)
                if fh_news:
                    raw_articles.extend(fh_news)
            except Exception as e:
                logger.warning(f"Failed to fetch market news from Finnhub: {e}")

        # 2. Fetch from NewsAPI
        if self.newsapi:
            try:
                napi_news = self.newsapi.get_everything(
                    query="market OR stocks OR federal reserve OR inflation OR gold",
                    sort_by="publishedAt",
                    page_size=min(limit, 50)
                )
                if napi_news:
                    raw_articles.extend(napi_news)
            except Exception as e:
                logger.warning(f"Failed to fetch market news from NewsAPI: {e}")

        # 3. Deduplicate
        unique_raw = NewsDeduplicator.deduplicate(raw_articles)

        # 4. Enrich
        enriched: List[EnrichedNewsArticle] = [
            EnrichedNewsArticle.from_normalized(item) for item in unique_raw
        ]

        # Sort by impact score descending, then published_at descending
        enriched.sort(key=lambda x: (x.impact_score, x.published_at), reverse=True)

        with self._lock:
            # Update memory cache
            self._memory_cache = enriched[:150]

        return enriched[:limit]

    def get_company_news(self, symbol: str, limit: int = 30) -> List[EnrichedNewsArticle]:
        """
        Fetch symbol-specific news from Finnhub & NewsAPI.
        """
        sym = symbol.upper().strip()
        raw_articles: List[NormalizedNews] = []

        # Finnhub company news
        if self.finnhub:
            try:
                fh_news = self.finnhub.get_company_news(sym, days_back=7)
                if fh_news:
                    raw_articles.extend(fh_news)
            except Exception as e:
                logger.warning(f"Finnhub company news failed for {sym}: {e}")

        # NewsAPI symbol search
        if self.newsapi:
            try:
                napi_news = self.newsapi.get_everything(
                    query=sym,
                    sort_by="publishedAt",
                    page_size=limit
                )
                if napi_news:
                    raw_articles.extend(napi_news)
            except Exception as e:
                logger.warning(f"NewsAPI company news failed for {sym}: {e}")

        unique_raw = NewsDeduplicator.deduplicate(raw_articles)
        enriched: List[EnrichedNewsArticle] = [
            EnrichedNewsArticle.from_normalized(item, symbol=sym) for item in unique_raw
        ]

        enriched.sort(key=lambda x: (x.impact_score, x.published_at), reverse=True)
        return enriched[:limit]

    def search_news(self, query: str, limit: int = 50) -> List[EnrichedNewsArticle]:
        """Keyword search across integrated news providers"""
        q = query.strip()
        if not q:
            return self.get_market_news(limit=limit)

        raw_articles: List[NormalizedNews] = []

        if self.newsapi:
            try:
                napi_news = self.newsapi.get_everything(query=q, page_size=limit)
                if napi_news:
                    raw_articles.extend(napi_news)
            except Exception as e:
                logger.warning(f"NewsAPI keyword search failed for '{q}': {e}")

        if not raw_articles and self.finnhub:
            # Fallback to market news filtering
            try:
                m_news = self.finnhub.get_market_news()
                raw_articles = [n for n in m_news if q.lower() in (n.title + n.description).lower()]
            except Exception as e:
                logger.warning(f"Finnhub search fallback failed: {e}")

        unique_raw = NewsDeduplicator.deduplicate(raw_articles)
        enriched = [EnrichedNewsArticle.from_normalized(item) for item in unique_raw]
        enriched.sort(key=lambda x: (x.impact_score, x.published_at), reverse=True)
        return enriched[:limit]

    def get_symbol_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Calculates aggregate sentiment profile for a specific trading symbol.
        Used by the Trading Signal Engine to factor in fundamental and macro sentiment.
        """
        articles = self.get_company_news(symbol, limit=20)
        if not articles:
            return {
                "symbol": symbol,
                "sentiment": SENTIMENT_NEUTRAL,
                "sentiment_score": 0.0,
                "article_count": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "has_critical_news": False,
                "top_headlines": []
            }

        bullish = sum(1 for a in articles if a.sentiment == SENTIMENT_POSITIVE)
        bearish = sum(1 for a in articles if a.sentiment == SENTIMENT_NEGATIVE)
        neutral = len(articles) - (bullish + bearish)

        # Weighted sentiment score based on impact score
        total_weight = 0.0
        weighted_score_sum = 0.0
        has_critical = False

        for a in articles:
            weight = max(1.0, a.impact_score / 20.0)
            weighted_score_sum += a.sentiment_score * weight
            total_weight += weight
            if a.impact in (IMPACT_CRITICAL, IMPACT_HIGH):
                has_critical = True

        avg_score = weighted_score_sum / total_weight if total_weight > 0 else 0.0
        avg_score = max(-1.0, min(1.0, round(avg_score, 3)))

        if avg_score >= 0.15:
            overall_sentiment = SENTIMENT_POSITIVE
        elif avg_score <= -0.15:
            overall_sentiment = SENTIMENT_NEGATIVE
        else:
            overall_sentiment = SENTIMENT_NEUTRAL

        return {
            "symbol": symbol,
            "sentiment": overall_sentiment,
            "sentiment_score": avg_score,
            "article_count": len(articles),
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral,
            "has_critical_news": has_critical,
            "top_headlines": [a.title for a in articles[:3]]
        }

    @staticmethod
    def filter_news(
        news_list: List[EnrichedNewsArticle],
        symbol: Optional[str] = None,
        category: Optional[str] = None,
        sentiment: Optional[str] = None,
        impact: Optional[str] = None,
        search_text: Optional[str] = None,
        min_impact_score: Optional[float] = None
    ) -> List[EnrichedNewsArticle]:
        """Multi-parameter filter for GUI and automated pipelines"""
        results = news_list

        if symbol and symbol != "ALL":
            s_up = symbol.upper()
            results = [a for a in results if s_up in a.symbol.upper() or s_up in (a.title + a.description).upper()]

        if category and category != "ALL":
            results = [a for a in results if a.category == category]

        if sentiment and sentiment != "ALL":
            results = [a for a in results if a.sentiment == sentiment]

        if impact and impact != "ALL":
            results = [a for a in results if a.impact == impact]

        if min_impact_score is not None:
            results = [a for a in results if a.impact_score >= min_impact_score]

        if search_text and search_text.strip():
            st = search_text.strip().lower()
            results = [
                a for a in results
                if st in a.title.lower() or st in a.description.lower() or st in a.source.lower()
            ]

        return results
