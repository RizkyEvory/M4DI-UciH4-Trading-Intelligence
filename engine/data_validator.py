"""
M4DI~UciH4 Trading Intelligence System
Data Integrity & Validation Engine
Guarantees clean OHLCV data: rejects future timestamps, duplicates, malformed bars, and gaps.
"""
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Optional

from api.models import NormalizedCandle
from core.logger import get_app_logger

logger = get_app_logger("DataValidator")


class DataValidator:
    """Validates, cleans, deduplicates, and chronologically sorts candlestick series"""

    @staticmethod
    def parse_timestamp(ts_str: str) -> Optional[datetime]:
        """Safely parse various ISO and SQL datetime strings"""
        if not ts_str:
            return None
        clean_str = ts_str.replace("T", " ").replace("Z", "").strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                expected_len = 19 if "%S" in fmt else (16 if "%M" in fmt else 10)
                return datetime.strptime(clean_str[:expected_len], fmt)
            except ValueError:
                continue
        return None

    @classmethod
    def validate_candle(cls, candle: NormalizedCandle, max_future_buffer_sec: int = 300) -> Tuple[bool, str]:
        """
        Validate single OHLCV bar integrity.
        Returns: (is_valid: bool, error_reason: str)
        """
        if candle.open <= 0 or candle.high <= 0 or candle.low <= 0 or candle.close <= 0:
            return False, f"Non-positive price in OHLC: O={candle.open}, H={candle.high}, L={candle.low}, C={candle.close}"

        if candle.volume < 0:
            return False, f"Negative volume: {candle.volume}"

        if candle.high < candle.low:
            return False, f"High ({candle.high}) is lower than Low ({candle.low})"

        if candle.high < candle.open or candle.high < candle.close:
            return False, f"High ({candle.high}) must be >= Open ({candle.open}) and Close ({candle.close})"

        if candle.low > candle.open or candle.low > candle.close:
            return False, f"Low ({candle.low}) must be <= Open ({candle.open}) and Close ({candle.close})"

        # Check timestamp
        dt = cls.parse_timestamp(candle.timestamp)
        if dt is None:
            return False, f"Malformed timestamp string: '{candle.timestamp}'"

        # Check future timestamp
        now = datetime.now()
        diff_sec = (dt - now).total_seconds()
        if diff_sec > max_future_buffer_sec:
            return False, f"Future timestamp detected: {candle.timestamp} (Current: {now.strftime('%Y-%m-%d %H:%M:%S')})"

        return True, ""

    @classmethod
    def clean_and_sort_candles(
        cls,
        candles: List[NormalizedCandle],
        expected_timeframe: Optional[str] = None
    ) -> List[NormalizedCandle]:
        """
        Filters out invalid candles, eliminates duplicates by timestamp,
        enforces single timeframe, and sorts chronologically ascending.
        """
        if not candles:
            return []

        valid_map: Dict[str, NormalizedCandle] = {}

        for c in candles:
            if expected_timeframe and c.timeframe:
                from engine.resampler import Resampler
                c_sec = Resampler.get_timeframe_seconds(c.timeframe)
                exp_sec = Resampler.get_timeframe_seconds(expected_timeframe)
                if c_sec and exp_sec and c_sec != exp_sec:
                    # Genuinely different timeframe duration
                    continue

            ok, reason = cls.validate_candle(c)
            if not ok:
                logger.warning(f"Rejected invalid candle for {c.symbol} [{c.timestamp}]: {reason}")
                continue

            # Normalized key to deduplicate: e.g. "2026-03-20 14:00:00"
            dt = cls.parse_timestamp(c.timestamp)
            if dt:
                norm_ts = dt.strftime("%Y-%m-%d %H:%M:%S")
                # Deduplication: last appearance wins
                valid_map[norm_ts] = NormalizedCandle(
                    symbol=c.symbol,
                    timeframe=expected_timeframe or c.timeframe,
                    open=c.open,
                    high=c.high,
                    low=c.low,
                    close=c.close,
                    volume=c.volume,
                    timestamp=norm_ts
                )

        # Sort chronologically ascending
        sorted_candles = sorted(
            valid_map.values(),
            key=lambda item: cls.parse_timestamp(item.timestamp) or datetime.min
        )
        return sorted_candles

    @classmethod
    def detect_gaps(
        cls,
        candles: List[NormalizedCandle],
        expected_interval_sec: int
    ) -> List[Tuple[str, str, float]]:
        """
        Detect gaps between consecutive bars exceeding 1.5x expected interval.
        Returns list of (prev_ts, next_ts, missing_seconds).
        """
        gaps = []
        if len(candles) < 2 or expected_interval_sec <= 0:
            return gaps

        for i in range(1, len(candles)):
            t1 = cls.parse_timestamp(candles[i - 1].timestamp)
            t2 = cls.parse_timestamp(candles[i].timestamp)
            if t1 and t2:
                diff = (t2 - t1).total_seconds()
                if diff > expected_interval_sec * 1.5:
                    gaps.append((candles[i - 1].timestamp, candles[i].timestamp, diff))
        return gaps
