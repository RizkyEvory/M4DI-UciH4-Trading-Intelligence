"""
M4DI~UciH4 Trading Intelligence System - News Intelligence Package
"""
from news.categories import NewsClassifier
from news.sentiment_analyzer import FinancialSentimentAnalyzer, SentimentResult
from news.impact_scorer import NewsImpactScorer
from news.deduplicator import NewsDeduplicator
from news.models import EnrichedNewsArticle
from news.news_engine import NewsEngine

__all__ = [
    "NewsClassifier",
    "FinancialSentimentAnalyzer",
    "SentimentResult",
    "NewsImpactScorer",
    "NewsDeduplicator",
    "EnrichedNewsArticle",
    "NewsEngine",
]
