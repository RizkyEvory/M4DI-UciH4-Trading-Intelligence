"""
M4DI~UciH4 Trading Intelligence System
Normalized Data Models
Decouples internal trading analytics from raw provider API formats.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class NormalizedQuote:
    """Standardized real-time or snapshot market quote"""
    symbol: str
    bid: float = 0.0
    ask: float = 0.0
    last: float = 0.0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    provider_source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedQuote":
        return cls(
            symbol=str(data.get("symbol", "")),
            bid=float(data.get("bid", 0.0) or 0.0),
            ask=float(data.get("ask", 0.0) or 0.0),
            last=float(data.get("last", 0.0) or 0.0),
            open=float(data.get("open", 0.0) or 0.0),
            high=float(data.get("high", 0.0) or 0.0),
            low=float(data.get("low", 0.0) or 0.0),
            close=float(data.get("close", 0.0) or 0.0),
            volume=float(data.get("volume", 0.0) or 0.0),
            change=float(data.get("change", 0.0) or 0.0),
            change_percent=float(data.get("change_percent", 0.0) or 0.0),
            timestamp=str(data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
            provider_source=str(data.get("provider_source", ""))
        )


@dataclass
class NormalizedCandle:
    """Standardized OHLCV candlestick bar"""
    symbol: str
    timeframe: str = "D1"
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedCandle":
        return cls(
            symbol=str(data.get("symbol", "")),
            timeframe=str(data.get("timeframe", "D1")),
            open=float(data.get("open", 0.0) or 0.0),
            high=float(data.get("high", 0.0) or 0.0),
            low=float(data.get("low", 0.0) or 0.0),
            close=float(data.get("close", 0.0) or 0.0),
            volume=float(data.get("volume", 0.0) or 0.0),
            timestamp=str(data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        )


@dataclass
class NormalizedNews:
    """Standardized market, macroeconomic, or corporate news headline"""
    title: str
    description: str = ""
    content: str = ""
    url: str = ""
    source: str = ""
    author: str = ""
    published_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    category: str = "general"
    sentiment: str = "neutral"
    provider_source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedNews":
        return cls(
            title=str(data.get("title", "")),
            description=str(data.get("description", "") or ""),
            content=str(data.get("content", "") or ""),
            url=str(data.get("url", "") or ""),
            source=str(data.get("source", "") or ""),
            author=str(data.get("author", "") or ""),
            published_at=str(data.get("published_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
            category=str(data.get("category", "general")),
            sentiment=str(data.get("sentiment", "neutral")),
            provider_source=str(data.get("provider_source", ""))
        )


@dataclass
class NormalizedCompany:
    """Standardized fundamental company profile"""
    symbol: str
    name: str
    exchange: str = ""
    currency: str = ""
    country: str = ""
    industry: str = ""
    sector: str = ""
    market_cap: float = 0.0
    website: str = ""
    logo: str = ""
    description: str = ""
    provider_source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedCompany":
        return cls(
            symbol=str(data.get("symbol", "")),
            name=str(data.get("name", "")),
            exchange=str(data.get("exchange", "") or ""),
            currency=str(data.get("currency", "") or ""),
            country=str(data.get("country", "") or ""),
            industry=str(data.get("industry", "") or ""),
            sector=str(data.get("sector", "") or ""),
            market_cap=float(data.get("market_cap", 0.0) or 0.0),
            website=str(data.get("website", "") or ""),
            logo=str(data.get("logo", "") or ""),
            description=str(data.get("description", "") or ""),
            provider_source=str(data.get("provider_source", ""))
        )


@dataclass
class NormalizedSymbol:
    """Standardized financial instrument search result"""
    symbol: str
    name: str
    type: str = ""
    exchange: str = ""
    currency: str = ""
    country: str = ""
    provider_source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NormalizedSymbol":
        return cls(
            symbol=str(data.get("symbol", "")),
            name=str(data.get("name", "")),
            type=str(data.get("type", "") or ""),
            exchange=str(data.get("exchange", "") or ""),
            currency=str(data.get("currency", "") or ""),
            country=str(data.get("country", "") or ""),
            provider_source=str(data.get("provider_source", ""))
        )
