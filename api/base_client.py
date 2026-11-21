"""
M4DI~UciH4 Trading Intelligence System
Base API Client with Rate Limiting, Key Rotation, Caching, and Exponential Backoff
"""
import json
import time
import requests
from typing import Optional, Dict, Any, Union
from urllib.parse import urljoin

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
from core.logger import get_app_logger

logger = get_app_logger("BaseApiClient")


class BaseApiClient:
    """
    Modular Base HTTP Client for institutional market data providers.
    Manages key rotation, automatic backoff, failovers, and caching.
    """

    def __init__(
        self,
        provider_name: str,
        base_url: str,
        rate_limiter=None,
        key_rotation=None,
        health_monitor=None,
        cache=None,
        timeout_sec: float = 12.0,
        max_retries: int = 3
    ):
        self.provider_name = provider_name
        self.base_url = base_url.rstrip("/")
        self.rate_limiter = rate_limiter
        self.key_rotation = key_rotation
        self.health_monitor = health_monitor
        self.cache = cache
        self.timeout_sec = timeout_sec
        self.max_retries = max(1, min(max_retries, 5))  # Capped strictly at 5
        self.session = requests.Session()

    def _build_url(self, endpoint: str) -> str:
        clean_ep = endpoint.lstrip("/")
        return f"{self.base_url}/{clean_ep}"

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json_data: Optional[Any] = None,
        cache_key: Optional[str] = None,
        cache_ttl: Optional[float] = None,
        override_api_key: Optional[str] = None
    ) -> Any:
        """
        Execute an HTTP request with rate-limiting, key rotation, failover, and retry.
        If cache_key is provided, checks cache before sending outbound network call.
        """
        # 1. Check Cache
        if self.cache and cache_key:
            cached_val = self.cache.get(cache_key)
            if cached_val is not None:
                return cached_val

        url = self._build_url(endpoint)
        req_params = dict(params or {})
        req_headers = dict(headers or {})

        # Retry loop for failovers and temporary errors
        last_exception = None

        for attempt in range(self.max_retries):
            # 2. Select API Key (unless explicitly overridden for connection testing)
            key_data = None
            if override_api_key is not None:
                active_key_str = override_api_key
            else:
                if self.key_rotation:
                    key_data = self.key_rotation.get_key_for_request(self.provider_name)
                    if not key_data:
                        raise NoActiveApiKeyException(
                            f"No active, non-cooldown API key available for {self.provider_name}",
                            provider=self.provider_name
                        )
                    active_key_str = key_data["raw_key"]
                else:
                    active_key_str = None

            # Inject Auth token (Subclasses customize via _inject_auth)
            auth_params, auth_headers = self._inject_auth(req_params, req_headers, active_key_str)

            # 3. Rate Limit Permit Acquisition
            if self.rate_limiter:
                permit = self.rate_limiter.acquire_permit(self.provider_name, timeout_sec=self.timeout_sec)
                if not permit:
                    # Provider rate limit throttle wait timed out
                    if self.health_monitor:
                        self.health_monitor.record_rate_limit(self.provider_name)
                    raise ApiRateLimitException(
                        f"Rate limit timeout exceeded for {self.provider_name}",
                        provider=self.provider_name
                    )

            # 4. Outbound Request Execution
            t0 = time.time()
            try:
                resp = self.session.request(
                    method=method.upper(),
                    url=url,
                    params=auth_params,
                    headers=auth_headers,
                    data=data,
                    json=json_data,
                    timeout=self.timeout_sec
                )
                elapsed_ms = (time.time() - t0) * 1000.0

                # HTTP 200 OK
                if resp.status_code == 200:
                    try:
                        parsed_json = resp.json()
                    except (json.JSONDecodeError, ValueError) as jde:
                        raise ApiInvalidResponseException(
                            f"Failed to parse JSON response: {jde}",
                            provider=self.provider_name,
                            raw_error=resp.text[:300]
                        )

                    # Update Health and Key metrics
                    if key_data and self.key_rotation:
                        self.key_rotation.record_key_success(key_data["id"])
                    if self.health_monitor:
                        self.health_monitor.record_success(self.provider_name)
                        if hasattr(self.health_monitor, "record_request"):
                            self.health_monitor.record_request(
                                provider=self.provider_name,
                                endpoint=endpoint,
                                status_code=200,
                                is_success=True,
                                response_time_ms=elapsed_ms,
                                key_id=key_data.get("id") if key_data else None
                            )

                    # Save to cache if key provided
                    if self.cache and cache_key and cache_ttl is not None:
                        self.cache.set(cache_key, parsed_json, ttl_seconds=cache_ttl)

                    return parsed_json

                # HTTP 429 Rate Limited
                elif resp.status_code == 429:
                    cooldown = 60
                    # Check Retry-After header
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        cooldown = int(retry_after)

                    if key_data and self.key_rotation:
                        self.key_rotation.record_key_rate_limit(key_data["id"], cooldown_sec=cooldown)
                    if self.rate_limiter:
                        self.rate_limiter.set_cooldown(self.provider_name, duration_seconds=cooldown)
                    if self.health_monitor:
                        self.health_monitor.record_rate_limit(self.provider_name, cooldown_sec=cooldown)
                        if hasattr(self.health_monitor, "record_request"):
                            self.health_monitor.record_request(
                                provider=self.provider_name,
                                endpoint=endpoint,
                                status_code=429,
                                is_success=False,
                                response_time_ms=elapsed_ms,
                                error_message="Rate limit 429",
                                key_id=key_data.get("id") if key_data else None
                            )

                    last_exception = ApiRateLimitException(
                        f"Rate limit (429) hit for {self.provider_name}",
                        provider=self.provider_name,
                        status_code=429,
                        retry_after_sec=cooldown
                    )
                    # Attempt next iteration to try failover key if available
                    continue

                # HTTP 401 / 403 Unauthorized
                elif resp.status_code in (401, 403):
                    if key_data and self.key_rotation:
                        self.key_rotation.record_key_auth_error(key_data["id"])
                    if self.health_monitor:
                        self.health_monitor.record_auth_error(
                            self.provider_name,
                            f"HTTP {resp.status_code}: Unauthorized credentials"
                        )
                        if hasattr(self.health_monitor, "record_request"):
                            self.health_monitor.record_request(
                                provider=self.provider_name,
                                endpoint=endpoint,
                                status_code=resp.status_code,
                                is_success=False,
                                response_time_ms=elapsed_ms,
                                error_message=f"HTTP {resp.status_code} Auth Error",
                                key_id=key_data.get("id") if key_data else None
                            )
                    last_exception = ApiAuthenticationException(
                        f"Authentication failed (HTTP {resp.status_code}): Invalid or disabled API key",
                        provider=self.provider_name,
                        status_code=resp.status_code,
                        raw_error=resp.text[:200]
                    )
                    # Attempt next iteration to try failover key
                    continue

                # HTTP 5xx Provider Server Error
                elif resp.status_code >= 500:
                    if key_data and self.key_rotation:
                        self.key_rotation.record_key_error(key_data["id"], error_msg=f"HTTP {resp.status_code}")
                    if self.health_monitor:
                        self.health_monitor.record_error(self.provider_name, f"HTTP {resp.status_code} Server Error")

                    last_exception = ApiProviderDownException(
                        f"Provider {self.provider_name} returned server error (HTTP {resp.status_code})",
                        provider=self.provider_name,
                        status_code=resp.status_code
                    )

                    # Backoff before retrying
                    if attempt < self.max_retries - 1:
                        backoff = self.rate_limiter.calculate_backoff(attempt) if self.rate_limiter else (1.5 ** attempt)
                        time.sleep(backoff)
                    continue

                else:
                    # Client Error 4xx other than 401/429
                    err_msg = f"HTTP {resp.status_code} Client Error"
                    if self.health_monitor:
                        self.health_monitor.record_error(self.provider_name, err_msg)
                    raise ApiException(
                        f"Request failed with HTTP {resp.status_code}: {resp.text[:200]}",
                        provider=self.provider_name,
                        status_code=resp.status_code
                    )

            except requests.Timeout as te:
                if key_data and self.key_rotation:
                    self.key_rotation.record_key_error(key_data["id"], error_msg="Timeout")
                if self.health_monitor:
                    self.health_monitor.record_error(self.provider_name, f"Request timeout ({self.timeout_sec}s)")

                last_exception = ApiNetworkTimeoutException(
                    f"Connection to {self.provider_name} timed out after {self.timeout_sec}s",
                    provider=self.provider_name
                )
                if attempt < self.max_retries - 1:
                    time.sleep(1.0)
                continue

            except requests.ConnectionError as ce:
                if key_data and self.key_rotation:
                    self.key_rotation.record_key_error(key_data["id"], error_msg="ConnectionError")
                if self.health_monitor:
                    self.health_monitor.record_error(self.provider_name, "Network connection error")

                last_exception = ApiConnectionException(
                    f"Network connection failed when reaching {self.provider_name}",
                    provider=self.provider_name
                )
                if attempt < self.max_retries - 1:
                    time.sleep(1.0)
                continue

        # If all retries exhausted
        if last_exception:
            raise last_exception
        raise ApiException(f"Request failed after {self.max_retries} attempts", provider=self.provider_name)

    def _inject_auth(
        self,
        params: Dict[str, Any],
        headers: Dict[str, str],
        api_key: Optional[str]
    ) -> tuple[Dict[str, Any], Dict[str, str]]:
        """Hook for provider subclasses to inject auth token into params or headers"""
        return params, headers
