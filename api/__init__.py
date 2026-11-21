"""
M4DI~UciH4 Trading Intelligence System
API Management Package — Clients, Multi-Key Rotation, Rate Limiting, Caching & Telemetry
"""
from api.key_manager import ApiKeyManager
from api.rate_limiter import RateLimitManager
from api.key_rotation import KeyRotationManager
from api.health_monitor import ProviderHealthMonitor
from api.cache import ResponseCache
from api.base_client import BaseApiClient
from api.finnhub_client import FinnhubClient
from api.twelve_data_client import TwelveDataClient
from api.newsapi_client import NewsApiClient
from api.models import (
    NormalizedQuote,
    NormalizedCandle,
    NormalizedNews,
    NormalizedCompany,
    NormalizedSymbol
)
from api.exceptions import (
    ApiException,
    ApiNetworkTimeoutException,
    ApiConnectionException,
    ApiRateLimitException,
    ApiAuthenticationException,
    ApiInvalidResponseException,
    ApiProviderDownException,
    NoActiveApiKeyException
)
