"""
M4DI~UciH4 Trading Intelligence System
Technical Analysis Indicators Engine
Mathematically verified pure Python / NumPy implementations.
"""
import math
from typing import List, Tuple, Optional, Dict, Any


def calculate_sma(data: List[float], period: int = 20) -> List[Optional[float]]:
    """Simple Moving Average (SMA)"""
    n = len(data)
    result: List[Optional[float]] = [None] * n
    if n < period or period <= 0:
        return result

    running_sum = sum(data[:period])
    result[period - 1] = running_sum / period

    for i in range(period, n):
        running_sum += data[i] - data[i - period]
        result[i] = running_sum / period
    return result


def calculate_ema(data: List[float], period: int = 20) -> List[Optional[float]]:
    """Exponential Moving Average (EMA) with standard 2/(N+1) multiplier"""
    n = len(data)
    result: List[Optional[float]] = [None] * n
    if n < period or period <= 0:
        return result

    # Initial EMA is SMA of the first period
    initial_sma = sum(data[:period]) / period
    result[period - 1] = initial_sma

    multiplier = 2.0 / (period + 1)
    prev_ema = initial_sma

    for i in range(period, n):
        current_ema = (data[i] - prev_ema) * multiplier + prev_ema
        result[i] = current_ema
        prev_ema = current_ema
    return result


def calculate_rsi(closes: List[float], period: int = 14) -> List[Optional[float]]:
    """
    Relative Strength Index (RSI) using standard Wilder's Smoothing.
    Values normalized to [0, 100].
    """
    n = len(closes)
    result: List[Optional[float]] = [None] * n
    if n <= period or period <= 0:
        return result

    gains = [0.0] * n
    losses = [0.0] * n

    for i in range(1, n):
        delta = closes[i] - closes[i - 1]
        if delta > 0:
            gains[i] = delta
        else:
            losses[i] = -delta

    avg_gain = sum(gains[1:period + 1]) / period
    avg_loss = sum(losses[1:period + 1]) / period

    if avg_loss == 0:
        result[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        result[period] = 100.0 - (100.0 / (1.0 + rs))

    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            result[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i] = 100.0 - (100.0 / (1.0 + rs))

    return result


def calculate_macd(
    closes: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """
    Moving Average Convergence Divergence (MACD).
    Returns: (macd_line, signal_line, histogram)
    """
    n = len(closes)
    fast_ema = calculate_ema(closes, period=fast_period)
    slow_ema = calculate_ema(closes, period=slow_period)

    macd_line: List[Optional[float]] = [None] * n
    for i in range(n):
        if fast_ema[i] is not None and slow_ema[i] is not None:
            macd_line[i] = fast_ema[i] - slow_ema[i]

    # Calculate Signal Line as EMA of valid MACD line elements
    valid_indices = [i for i, v in enumerate(macd_line) if v is not None]
    signal_line: List[Optional[float]] = [None] * n
    histogram: List[Optional[float]] = [None] * n

    if len(valid_indices) >= signal_period:
        valid_macd_values = [macd_line[i] for i in valid_indices]
        valid_signals = calculate_ema(valid_macd_values, period=signal_period)

        for idx, sig_val in zip(valid_indices, valid_signals):
            signal_line[idx] = sig_val
            if macd_line[idx] is not None and sig_val is not None:
                histogram[idx] = macd_line[idx] - sig_val

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    closes: List[float],
    period: int = 20,
    num_std: float = 2.0
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """
    Bollinger Bands (Upper, Middle/SMA, Lower, Bandwidth%).
    Bandwidth = (Upper - Lower) / Middle * 100
    """
    n = len(closes)
    sma = calculate_sma(closes, period=period)
    upper: List[Optional[float]] = [None] * n
    lower: List[Optional[float]] = [None] * n
    bandwidth: List[Optional[float]] = [None] * n

    for i in range(period - 1, n):
        mean = sma[i]
        if mean is None:
            continue
        slice_vals = closes[i - period + 1 : i + 1]
        variance = sum((x - mean) ** 2 for x in slice_vals) / period
        std_dev = math.sqrt(variance)

        u = mean + (num_std * std_dev)
        l = mean - (num_std * std_dev)
        upper[i] = u
        lower[i] = l
        bandwidth[i] = ((u - l) / mean * 100.0) if mean != 0 else 0.0

    return upper, sma, lower, bandwidth


def calculate_atr(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14
) -> List[Optional[float]]:
    """Average True Range (ATR) using Wilder's Smoothing"""
    n = len(closes)
    result: List[Optional[float]] = [None] * n
    if n < period or period <= 0:
        return result

    tr = [0.0] * n
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, hc, lc)

    # First ATR is simple average of initial TRs
    initial_atr = sum(tr[:period]) / period
    result[period - 1] = initial_atr

    prev_atr = initial_atr
    for i in range(period, n):
        current_atr = (prev_atr * (period - 1) + tr[i]) / period
        result[i] = current_atr
        prev_atr = current_atr

    return result


def calculate_adx(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """
    Average Directional Index (ADX) with +DI and -DI.
    Returns: (adx_line, plus_di, minus_di)
    """
    n = len(closes)
    adx_line: List[Optional[float]] = [None] * n
    plus_di: List[Optional[float]] = [None] * n
    minus_di: List[Optional[float]] = [None] * n

    if n < period * 2 or period <= 0:
        return adx_line, plus_di, minus_di

    tr = [0.0] * n
    plus_dm = [0.0] * n
    minus_dm = [0.0] * n

    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, hc, lc)

        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]

        if up_move > down_move and up_move > 0:
            plus_dm[i] = up_move
        if down_move > up_move and down_move > 0:
            minus_dm[i] = down_move

    # Wilder's smoothing for TR and DMs
    smooth_tr = sum(tr[1:period + 1])
    smooth_pdm = sum(plus_dm[1:period + 1])
    smooth_mdm = sum(minus_dm[1:period + 1])

    dx_list: List[Optional[float]] = [None] * n

    for i in range(period, n):
        if i > period:
            smooth_tr = smooth_tr - (smooth_tr / period) + tr[i]
            smooth_pdm = smooth_pdm - (smooth_pdm / period) + plus_dm[i]
            smooth_mdm = smooth_mdm - (smooth_mdm / period) + minus_dm[i]

        pdi_val = (smooth_pdm / smooth_tr * 100.0) if smooth_tr > 0 else 0.0
        mdi_val = (smooth_mdm / smooth_tr * 100.0) if smooth_tr > 0 else 0.0
        plus_di[i] = pdi_val
        minus_di[i] = mdi_val

        di_sum = pdi_val + mdi_val
        dx = (abs(pdi_val - mdi_val) / di_sum * 100.0) if di_sum > 0 else 0.0
        dx_list[i] = dx

    # Calculate ADX from DX using smoothing
    valid_dx = [x for x in dx_list[period:] if x is not None]
    if len(valid_dx) >= period:
        first_adx_idx = period + period - 1
        curr_adx = sum(valid_dx[:period]) / period
        adx_line[first_adx_idx] = curr_adx

        for i in range(first_adx_idx + 1, n):
            dx_val = dx_list[i]
            if dx_val is not None:
                curr_adx = (curr_adx * (period - 1) + dx_val) / period
                adx_line[i] = curr_adx

    return adx_line, plus_di, minus_di


def calculate_stochastic(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    k_period: int = 14,
    d_period: int = 3
) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    """
    Stochastic Oscillator (%K and %D).
    Returns: (percent_k, percent_d)
    """
    n = len(closes)
    raw_k: List[Optional[float]] = [None] * n

    for i in range(k_period - 1, n):
        lowest_low = min(lows[i - k_period + 1 : i + 1])
        highest_high = max(highs[i - k_period + 1 : i + 1])
        rng = highest_high - lowest_low
        if rng == 0:
            raw_k[i] = 50.0
        else:
            raw_k[i] = ((closes[i] - lowest_low) / rng) * 100.0

    # %D is SMA of %K
    percent_d: List[Optional[float]] = [None] * n
    for i in range(k_period + d_period - 2, n):
        slice_k = [k for k in raw_k[i - d_period + 1 : i + 1] if k is not None]
        if len(slice_k) == d_period:
            percent_d[i] = sum(slice_k) / d_period

    return raw_k, percent_d


def calculate_stochastic_rsi(
    closes: List[float],
    rsi_period: int = 14,
    stoch_period: int = 14,
    k_period: int = 3,
    d_period: int = 3
) -> Tuple[List[Optional[float]], List[Optional[float]]]:
    """
    Stochastic RSI.
    Applies Stochastic formula to RSI values.
    Returns: (stoch_rsi_k, stoch_rsi_d)
    """
    n = len(closes)
    rsi_vals = calculate_rsi(closes, period=rsi_period)
    stoch_rsi_raw: List[Optional[float]] = [None] * n

    for i in range(n):
        if i >= rsi_period + stoch_period - 1:
            window = [r for r in rsi_vals[i - stoch_period + 1 : i + 1] if r is not None]
            if len(window) == stoch_period:
                min_rsi = min(window)
                max_rsi = max(window)
                rng = max_rsi - min_rsi
                if rng == 0:
                    stoch_rsi_raw[i] = 50.0
                else:
                    stoch_rsi_raw[i] = ((rsi_vals[i] - min_rsi) / rng) * 100.0

    # Calculate K as SMA of stoch_rsi_raw
    k_line: List[Optional[float]] = [None] * n
    for i in range(n):
        window = [v for v in stoch_rsi_raw[max(0, i - k_period + 1) : i + 1] if v is not None]
        if len(window) == k_period:
            k_line[i] = sum(window) / k_period

    # Calculate D as SMA of K
    d_line: List[Optional[float]] = [None] * n
    for i in range(n):
        window = [v for v in k_line[max(0, i - d_period + 1) : i + 1] if v is not None]
        if len(window) == d_period:
            d_line[i] = sum(window) / d_period

    return k_line, d_line


def calculate_vwap(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: List[float]
) -> List[Optional[float]]:
    """Volume Weighted Average Price (VWAP)"""
    n = len(closes)
    result: List[Optional[float]] = [None] * n
    if n == 0:
        return result

    cum_pv = 0.0
    cum_vol = 0.0

    for i in range(n):
        typical_price = (highs[i] + lows[i] + closes[i]) / 3.0
        v = volumes[i]
        cum_pv += typical_price * v
        cum_vol += v
        if cum_vol > 0:
            result[i] = cum_pv / cum_vol
        else:
            result[i] = typical_price

    return result


def calculate_obv(closes: List[float], volumes: List[float]) -> List[float]:
    """On-Balance Volume (OBV)"""
    n = len(closes)
    result = [0.0] * n
    if n == 0:
        return result

    result[0] = volumes[0]
    for i in range(1, n):
        if closes[i] > closes[i - 1]:
            result[i] = result[i - 1] + volumes[i]
        elif closes[i] < closes[i - 1]:
            result[i] = result[i - 1] - volumes[i]
        else:
            result[i] = result[i - 1]
    return result


class TechnicalIndicators:
    """Convenience namespace wrapper for technical indicator functions"""
    sma = staticmethod(calculate_sma)
    ema = staticmethod(calculate_ema)
    rsi = staticmethod(calculate_rsi)
    macd = staticmethod(calculate_macd)
    bollinger_bands = staticmethod(calculate_bollinger_bands)
    atr = staticmethod(calculate_atr)
    adx = staticmethod(calculate_adx)
    stochastic = staticmethod(calculate_stochastic)
    stochastic_rsi = staticmethod(calculate_stochastic_rsi)
    vwap = staticmethod(calculate_vwap)
    obv = staticmethod(calculate_obv)

