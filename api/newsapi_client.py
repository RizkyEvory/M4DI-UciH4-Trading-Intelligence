"""
M4DI~UciH4 Trading Intelligence System
NewsAPI.org Macro & Financial News Intelligence Client
Covers Macro headlines, keyword search, company search, and multi-parameter filtering.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from config.constants import (
    PROVIDER_NEWS_API,
    CACHE_TTL_NEWS
)
from api.base_client import BaseApiClient
from api.models import NormalizedNews
from api.cache import make_news_key
from core.logger import get_app_logger

logger = get_app_logger("NewsApiClient")


class NewsApiClient(BaseApiClient):
    """NewsAPI.org Intelligence Client with Data Normalization"""

    def __init__(
        self,
        base_url: str = "https://newsapi.org/v2",
        rate_limiter=None,
        key_rotation=None,
        health_monitor=None,
        cache=None
    ):
        super().__init__(
            provider_name=PROVIDER_NEWS_API,
            base_url=base_url,
            rate_limiter=rate_limiter,
            key_rotation=key_rotation,
            health_monitor=health_monitor,
            cache=cache,
            timeout_sec=10.0
        )

    def _inject_auth(self, params: Dict[str, Any], headers: Dict[str, str], api_key: Optional[str]):
        """NewsAPI accepts X-Api-Key header or apiKey param"""
        if api_key:
            headers["X-Api-Key"] = api_key
        return params, headers

    def test_connection(self, override_api_key: Optional[str] = None) -> bool:
        """Test API connection with a minimal top headlines query"""
        try:
            res = self.request(
                method="GET",
                endpoint="top-headlines",
                params={"category": "business", "pageSize": 1, "language": "en"},
                override_api_key=override_api_key
            )
            return isinstance(res, dict) and res.get("status") == "ok"
        except Exception as e:
            logger.warning(f"NewsAPI connection test failed: {e}")
            raise

    def get_everything(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = "en",
        sources: Optional[str] = None,
        domains: Optional[str] = None,
        sort_by: str = "publishedAt",
        page_size: int = 25
    ) -> List[NormalizedNews]:
        """
        Search millions of articles with granular keyword, language, date, and source filtering.
        """
        q = query.strip()
        params: Dict[str, Any] = {
            "q": q,
            "language": language,
            "sortBy": sort_by,
            "pageSize": min(page_size, 100)
        }
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if sources:
            params["sources"] = sources
        if domains:
            params["domains"] = domains

        cache_key = make_news_key(PROVIDER_NEWS_API, f"search_{q}_{language}_{from_date}_{to_date}")

        data = self.request(
            method="GET",
            endpoint="everything",
            params=params,
            cache_key=cache_key,
            cache_ttl=CACHE_TTL_NEWS
        )

        return self._normalize_articles(data.get("articles", []), category="search")

    def get_top_headlines(
        self,
        category: str = "business",
        country: Optional[str] = "us",
        query: Optional[str] = None,
        page_size: int = 25
    ) -> List[NormalizedNews]:
        """Fetch breaking top headlines for economics and business"""
        params: Dict[str, Any] = {
            "category": category,
            "pageSize": min(page_size, 100)
        }
        if country:
            params["country"] = country
        if query:
            params["q"] = query

        cache_key = make_news_key(PROVIDER_NEWS_API, f"top_{category}_{country}_{query}")

        data = self.request(
            method="GET",
            endpoint="top-headlines",
            params=params,
            cache_key=cache_key,
            cache_ttl=CACHE_TTL_NEWS
        )

        return self._normalize_articles(data.get("articles", []), category=category)

    def get_market_news(self, market_topic: str = "Forex OR Gold OR Fed") -> List[NormalizedNews]:
        """Fetch news specifically tailored to institutional market macro drivers"""
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        return self.get_everything(query=market_topic, from_date=seven_days_ago, sort_by="publishedAt")

    def get_company_news(self, company_name: str) -> List[NormalizedNews]:
        """Fetch news specifically mentioning a company or stock ticker"""
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        return self.get_everything(query=company_name, from_date=seven_days_ago, sort_by="relevancy")

    def _normalize_articles(self, raw_articles: List[Dict[str, Any]], category: str) -> List[NormalizedNews]:
        """Convert raw NewsAPI article objects into NormalizedNews"""
        news_items: List[NormalizedNews] = []
        if not isinstance(raw_articles, list):
            return news_items

        for item in raw_articles:
            src_info = item.get("source", {})
            src_name = src_info.get("name", "NewsAPI") if isinstance(src_info, dict) else "NewsAPI"

            raw_dt = item.get("publishedAt", "")
            if raw_dt and "T" in raw_dt:
                # Format 2026-03-20T14:30:00Z -> 2026-03-20 14:30:00
                pub_clean = raw_dt.replace("T", " ").replace("Z", "")[:19]
            else:
                pub_clean = raw_dt or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            news_items.append(NormalizedNews(
                title=item.get("title", ""),
                description=item.get("description", "") or "",
                content=item.get("content", "") or "",
                url=item.get("url", "") or "",
                source=src_name,
                author=item.get("author", "") or "",
                published_at=pub_clean,
                category=category,
                provider_source=PROVIDER_NEWS_API
            ))
        return news_items
