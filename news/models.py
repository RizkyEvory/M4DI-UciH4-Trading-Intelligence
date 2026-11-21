"""
M4DI~UciH4 Trading Intelligence System
Enriched News Article Model
Structured representation of categorized, sentiment-analyzed, and impact-scored news intelligence.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime

from config.constants import (
    NEWS_CAT_MARKET_SENTIMENT,
    SENTIMENT_NEUTRAL,
    IMPACT_LOW
)
from api.models import NormalizedNews
from news.categories import NewsClassifier
from news.sentiment_analyzer import FinancialSentimentAnalyzer
from news.impact_scorer import NewsImpactScorer


@dataclass
class EnrichedNewsArticle:
    """Full-spectrum intelligence article with classification, sentiment, and market impact"""
    title: str
    description: str = ""
    content: str = ""
    url: str = ""
    source: str = ""
    author: str = ""
    published_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    symbol: str = ""
    category: str = NEWS_CAT_MARKET_SENTIMENT
    category_confidence: float = 0.5
    sentiment: str = SENTIMENT_NEUTRAL
    sentiment_score: float = 0.0          # -1.0 to +1.0
    sentiment_intensity: float = 0.0      # 0.0 to 1.0
    sentiment_reasons: List[str] = field(default_factory=list)
    impact: str = IMPACT_LOW               # LOW, MEDIUM, HIGH, CRITICAL
    impact_score: float = 20.0             # 0 to 100
    impact_breakdown: Dict[str, Any] = field(default_factory=dict)
    provider_source: str = ""
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_normalized(cls, item: NormalizedNews, symbol: str = "") -> "EnrichedNewsArticle":
        """
        Enrich a NormalizedNews instance by running through:
        1. Institutional Category Classifier (11 categories)
        2. Local Deterministic Financial Sentiment Analyzer
        3. Market Impact Scorer
        """
        title = item.title or ""
        desc = item.description or ""
        content = item.content or ""

        # 1. Classification
        category, cat_conf = NewsClassifier.classify(title, desc, content)

        # 2. Sentiment
        sentiment_res = FinancialSentimentAnalyzer.analyze(f"{title}. {desc}")

        # 3. Impact
        impact_level, impact_score, breakdown = NewsImpactScorer.calculate_impact(
            category=category,
            sentiment_score=sentiment_res.score,
            title=title,
            description=desc,
            published_at=item.published_at
        )

        # Clean summary
        summary = desc if desc else (content[:250] + "..." if len(content) > 250 else content)
        if not summary:
            summary = title

        return cls(
            title=title,
            description=desc,
            content=content,
            url=item.url,
            source=item.source or "Market News",
            author=item.author or "",
            published_at=item.published_at,
            symbol=symbol or item.category if symbol else "",
            category=category,
            category_confidence=cat_conf,
            sentiment=sentiment_res.sentiment,
            sentiment_score=sentiment_res.score,
            sentiment_intensity=sentiment_res.intensity,
            sentiment_reasons=sentiment_res.reasons,
            impact=impact_level,
            impact_score=impact_score,
            impact_breakdown=breakdown,
            provider_source=item.provider_source,
            summary=summary
        )
