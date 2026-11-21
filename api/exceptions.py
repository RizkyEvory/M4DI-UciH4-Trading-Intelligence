"""
M4DI~UciH4 Trading Intelligence System
API Exceptions Hierarchy
"""

class ApiException(Exception):
    """Base exception for all trading intelligence API errors"""
    def __init__(self, message: str, provider: str = "", status_code: int = 0, raw_error: str = ""):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.status_code = status_code
        self.raw_error = raw_error

    def __str__(self):
        prov_prefix = f"[{self.provider}] " if self.provider else ""
        code_str = f" (Status {self.status_code})" if self.status_code else ""
        return f"{prov_prefix}{self.message}{code_str}"


class ApiNetworkTimeoutException(ApiException):
    """Network connection or read timeout"""
    pass


class ApiConnectionException(ApiException):
    """Network connection failure, DNS resolution error, or unreachable host"""
    pass


class ApiRateLimitException(ApiException):
    """Provider rate limit reached (HTTP 429 or quota exhaustion)"""
    def __init__(self, message: str, provider: str = "", retry_after_sec: int = 60, **kwargs):
        super().__init__(message, provider=provider, **kwargs)
        self.retry_after_sec = retry_after_sec


class ApiAuthenticationException(ApiException):
    """Unauthorized, forbidden, or invalid API key credential (HTTP 401/403)"""
    pass


class ApiInvalidResponseException(ApiException):
    """Invalid JSON, malformed payload, or unexpected structure from provider"""
    pass


class ApiProviderDownException(ApiException):
    """Provider internal server error or maintenance downtime (HTTP 5xx)"""
    pass


class NoActiveApiKeyException(ApiException):
    """No active or cooldown-free API keys available for requested provider"""
    pass
