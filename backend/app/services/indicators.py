"""Technical indicator calculation service.

Pure computation module — no external API calls, no LLM dependencies.
All functions accept price lists/arrays and return indicator values.
"""
import math
from typing import List, Dict, Optional


def _ema(data: List[float], period: int) -> List[float]:
    """Exponential Moving Average."""
    if len(data) < period:
        return []
    multiplier = 2 / (period + 1)
    ema_values = [sum(data[:period]) / period]
    for price in data[period:]:
        ema_values.append((price - ema_values[-1]) * multiplier + ema_values[-1])
    return ema_values


def _sma(data: List[float], period: int) -> List[float]:
    """Simple Moving Average."""
    if len(data) < period:
        return []
    return [sum(data[i:i + period]) / period for i in range(len(data) - period + 1)]


def calculate_macd(
    prices: List[float],
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> Dict[str, float]:
    """MACD (Moving Average Convergence Divergence)."""
    if len(prices) < slow + signal_period:
        return {"macd_line": 0.0, "signal_line": 0.0, "histogram": 0.0}

    fast_ema = _ema(prices, fast)
    slow_ema = _ema(prices, slow)

    offset = fast - slow
    macd_line = [f - s for f, s in zip(fast_ema[-len(slow_ema):], slow_ema)]

    signal_line = _ema(macd_line, signal_period)
    if not signal_line:
        return {"macd_line": 0.0, "signal_line": 0.0, "histogram": 0.0}

    macd_val = macd_line[-1]
    signal_val = signal_line[-1]

    return {
        "macd_line": round(macd_val, 4),
        "signal_line": round(signal_val, 4),
        "histogram": round(macd_val - signal_val, 4),
    }


def calculate_rsi(prices: List[float], period: int = 14) -> Dict[str, float]:
    """RSI (Relative Strength Index)."""
    if len(prices) < period + 1:
        return {"value": 50.0, "signal": "neutral"}

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

    signal = "neutral"
    if rsi > 70:
        signal = "overbought"
    elif rsi < 30:
        signal = "oversold"

    return {"value": round(rsi, 2), "signal": signal}


def calculate_kdj(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 9,
) -> Dict[str, float]:
    """KDJ indicator."""
    if len(closes) < period or not highs or not lows:
        return {"k": 50.0, "d": 50.0, "j": 50.0, "signal": "neutral"}

    k_values = []
    for i in range(period - 1, len(closes)):
        high_n = max(highs[i - period + 1:i + 1])
        low_n = min(lows[i - period + 1:i + 1])
        if high_n == low_n:
            rsv = 50.0
        else:
            rsv = (closes[i] - low_n) / (high_n - low_n) * 100
        k_values.append(rsv)

    k = 50.0
    d = 50.0
    for rsv in k_values:
        k = 2 / 3 * k + 1 / 3 * rsv
        d = 2 / 3 * d + 1 / 3 * k

    j = 3 * k - 2 * d

    signal = "neutral"
    if k > 80 and d > 80:
        signal = "overbought"
    elif k < 20 and d < 20:
        signal = "oversold"

    return {
        "k": round(k, 2),
        "d": round(d, 2),
        "j": round(j, 2),
        "signal": signal,
    }


def calculate_bollinger(
    prices: List[float],
    period: int = 20,
    num_std: float = 2.0,
) -> Dict[str, float]:
    """Bollinger Bands."""
    if len(prices) < period:
        return {"upper": 0.0, "middle": 0.0, "lower": 0.0, "signal": "neutral"}

    recent = prices[-period:]
    middle = sum(recent) / period
    variance = sum((p - middle) ** 2 for p in recent) / period
    std_dev = math.sqrt(variance)

    upper = middle + num_std * std_dev
    lower = middle - num_std * std_dev
    current = prices[-1]

    signal = "neutral"
    if current > upper:
        signal = "overbought"
    elif current < lower:
        signal = "oversold"

    return {
        "upper": round(upper, 4),
        "middle": round(middle, 4),
        "lower": round(lower, 4),
        "signal": signal,
    }


def calculate_ma(prices: List[float], periods: List[int] = None) -> Dict[str, float]:
    """Multiple Moving Averages."""
    if periods is None:
        periods = [5, 10, 20, 60]
    result = {}
    for p in periods:
        if len(prices) >= p:
            result[f"ma{p}"] = round(sum(prices[-p:]) / p, 4)
        else:
            result[f"ma{p}"] = 0.0
    return result


def calculate_all_indicators(
    closes: List[float],
    highs: Optional[List[float]] = None,
    lows: Optional[List[float]] = None,
) -> Dict:
    """Calculate all technical indicators at once."""
    if highs is None or not highs:
        highs = closes
    if lows is None or not lows:
        lows = closes

    return {
        "macd": calculate_macd(closes),
        "rsi": calculate_rsi(closes),
        "kdj": calculate_kdj(highs, lows, closes),
        "bollinger": calculate_bollinger(closes),
        "ma": calculate_ma(closes),
    }
