"""
M4DI~UciH4 Trading Intelligence System
Mathematical OHLCV Resampling Engine
Aggregates lower-timeframe bars into higher-timeframe bars without candle fabrication.
"""
from datetime import datetime
from typing import List, Optional
from collections import OrderedDict

from api.models import NormalizedCandle
from config.constants import TIMEFRAME_SECONDS, TF_1M, TF_5M, TF_15M, TF_30M, TF_1H, TF_4H, TF_1D, TF_1W, TF_1MO
from engine.data_validator import DataValidator
from core.logger import get_app_logger

logger = get_app_logger("Resampler")


class Resampler:
    """Mathematical OHLCV Timeframe Aggregation Engine"""

    @classmethod
    def get_timeframe_seconds(cls, timeframe: str) -> Optional[int]:
        """Convert timeframe code to seconds duration"""
        tf_clean = timeframe.strip().lower()
        mapping = {
            "1m": 60, "m1": 60,
            "5m": 300, "m5": 300,
            "15m": 900, "m15": 900,
            "30m": 1800, "m30": 1800,
            "1h": 3600, "h1": 3600, "60m": 3600,
            "4h": 14400, "h4": 14400,
            "1d": 86400, "d1": 86400, "d": 86400,
            "1w": 604800, "w1": 604800, "w": 604800,
            "1mo": 2592000, "1m_month": 2592000, "m": 2592000
        }
        return mapping.get(tf_clean, TIMEFRAME_SECONDS.get(timeframe))

    @classmethod
    def resample(
        cls,
        candles: List[NormalizedCandle],
        target_timeframe: str,
        source_timeframe: Optional[str] = None
    ) -> List[NormalizedCandle]:
        """
        Resamples a list of lower-timeframe candles to target_timeframe.
        Guarantees:
        - Open is first bar open
        - High is max of all bar highs
        - Low is min of all bar lows
        - Close is last bar close
        - Volume is sum of all bar volumes
        - NEVER fabricates or interpolates missing buckets
        """
        if not candles:
            return []

        target_sec = cls.get_timeframe_seconds(target_timeframe)
        if not target_sec:
            logger.warning(f"Unknown target timeframe: {target_timeframe}")
            return candles

        # Clean and sort source bars first
        sorted_bars = DataValidator.clean_and_sort_candles(candles, expected_timeframe=source_timeframe)
        if not sorted_bars:
            return []

        # Check source duration if available
        first_tf = sorted_bars[0].timeframe
        source_sec = cls.get_timeframe_seconds(first_tf) if first_tf else None
        if source_sec and source_sec > target_sec:
            raise ValueError(f"Cannot downsample higher timeframe ({first_tf}={source_sec}s) to lower timeframe ({target_timeframe}={target_sec}s)")

        if source_sec and source_sec == target_sec:
            # Already in desired timeframe
            return sorted_bars

        # Group bars into target time buckets
        buckets: OrderedDict[int, List[NormalizedCandle]] = OrderedDict()

        for bar in sorted_bars:
            dt = DataValidator.parse_timestamp(bar.timestamp)
            if not dt:
                continue
            epoch = int(dt.timestamp())
            # Calculate bucket boundary
            bucket_epoch = (epoch // target_sec) * target_sec

            if bucket_epoch not in buckets:
                buckets[bucket_epoch] = []
            buckets[bucket_epoch].append(bar)

        symbol = sorted_bars[0].symbol
        resampled: List[NormalizedCandle] = []

        for b_epoch, bar_list in buckets.items():
            if not bar_list:
                continue

            open_p = bar_list[0].open
            close_p = bar_list[-1].close
            high_p = max(b.high for b in bar_list)
            low_p = min(b.low for b in bar_list)
            vol = sum(b.volume for b in bar_list)
            b_ts = datetime.fromtimestamp(b_epoch).strftime("%Y-%m-%d %H:%M:%S")

            resampled.append(NormalizedCandle(
                symbol=symbol,
                timeframe=target_timeframe,
                open=round(open_p, 5),
                high=round(high_p, 5),
                low=round(low_p, 5),
                close=round(close_p, 5),
                volume=round(vol, 2),
                timestamp=b_ts
            ))

        return resampled
