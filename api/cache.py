"""
M4DI~UciH4 Trading Intelligence System
Thread-Safe In-Memory Response Cache with Configurable Expiry (TTL)
"""
import time
import threading
from typing import Any, Optional, Dict
from config.constants import (
    CACHE_TTL_QUOTE, CACHE_TTL_CANDLE, CACHE_TTL_COMPANY, CACHE_TTL_NEWS, CACHE_TTL_SEARCH
)


class ResponseCache:
    """
    High-performance thread-safe in-memory cache with TTL expiration.
    Caches quotes, candles, company fundamentals, and news articles.
    """

    def __init__(self):
        self._lock = threading.RLock()
        # Key -> (payload, expire_time)
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Retrieve item if present and not expired; returns None on miss or expiry"""
        now = time.time()
        with self._lock:
            if key in self._cache:
                data, expire_at = self._cache[key]
                if expire_at > now:
                    self._hits += 1
                    return data
                else:
                    # Expired
                    del self._cache[key]
            self._misses += 1
            return None

    def set(self, key: str, data: Any, ttl_seconds: float = 60.0):
        """Store an item with expiration timestamp"""
        expire_at = time.time() + float(ttl_seconds)
        with self._lock:
            self._cache[key] = (data, expire_at)

    def invalidate(self, key: str) -> bool:
        """Manually remove an item by exact key"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def invalidate_prefix(self, prefix: str) -> int:
        """Remove all entries matching a prefix pattern (e.g. 'Finnhub:quote:')"""
        removed = 0
        with self._lock:
            keys_to_del = [k for k in self._cache.keys() if k.startswith(prefix)]
            for k in keys_to_del:
                del self._cache[k]
                removed += 1
        return removed

    def clear(self):
        """Clear the entire cache"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def prune_expired(self) -> int:
        """Remove all expired entries from cache to free memory"""
        now = time.time()
        count = 0
        with self._lock:
            expired_keys = [k for k, (_, exp) in self._cache.items() if exp <= now]
            for k in expired_keys:
                del self._cache[k]
                count += 1
        return count

    def stats(self) -> Dict[str, Any]:
        """Return cache health metrics & performance statistics"""
        now = time.time()
        with self._lock:
            active_count = sum(1 for _, exp in self._cache.values() if exp > now)
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100.0) if total_requests > 0 else 0.0
            return {
                "active_items": active_count,
                "total_entries": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_pct": round(hit_rate, 2)
            }


# Cache key helper utilities
def make_quote_key(provider: str, symbol: str) -> str:
    return f"{provider.lower()}:quote:{symbol.upper().strip()}"

def make_candle_key(provider: str, symbol: str, timeframe: str) -> str:
    return f"{provider.lower()}:candle:{symbol.upper().strip()}:{timeframe.upper().strip()}"

def make_company_key(provider: str, symbol: str) -> str:
    return f"{provider.lower()}:company:{symbol.upper().strip()}"

def make_news_key(provider: str, query: str) -> str:
    return f"{provider.lower()}:news:{query.lower().strip()}"

def make_search_key(provider: str, query: str) -> str:
    return f"{provider.lower()}:search:{query.lower().strip()}"
