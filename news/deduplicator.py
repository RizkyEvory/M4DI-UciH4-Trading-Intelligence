"""
M4DI~UciH4 Trading Intelligence System
News Deduplication Engine
Removes duplicate and syndicated news stories using URL normalization and fuzzy headline similarity.
"""
import re
from typing import List, Dict, Any
from urllib.parse import urlparse, urlunparse


def _normalize_title(title: str) -> str:
    """Normalize headline string: lowercase, remove non-alphanumeric, strip whitespace"""
    if not title:
        return ""
    text = title.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return " ".join(text.split())


def _clean_url(url: str) -> str:
    """Remove tracking query params like utm_*, ref, etc."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        # Drop query strings containing tracking markers
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    except Exception:
        return url.strip().lower()


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """Calculate token overlap ratio between two word sets"""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return float(intersection) / float(union) if union > 0 else 0.0


class NewsDeduplicator:
    """Detects and merges duplicate articles across multiple API providers"""

    @classmethod
    def deduplicate(cls, articles: List[Any], similarity_threshold: float = 0.60) -> List[Any]:
        """
        Deduplicates a list of news items (objects with title, url, description, etc.).
        Returns only unique, highest-quality articles.
        """
        if not articles:
            return []

        seen_urls = set()
        unique_articles = []
        token_sets: List[set] = []

        for article in articles:
            title = getattr(article, "title", "") or ""
            url = getattr(article, "url", "") or ""

            norm_url = _clean_url(url)
            if norm_url and norm_url in seen_urls:
                # Direct URL duplicate
                continue

            norm_title = _normalize_title(title)
            words = set(w for w in norm_title.split() if len(w) >= 2)

            # Check fuzzy similarity with already accepted articles
            is_duplicate = False
            for prev_set in token_sets:
                sim = _jaccard_similarity(words, prev_set)
                if sim >= similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                if norm_url:
                    seen_urls.add(norm_url)
                if words:
                    token_sets.append(words)
                unique_articles.append(article)

        return unique_articles
