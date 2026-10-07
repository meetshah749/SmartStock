from typing import List, Dict, Any, Optional


def calculate_sma(prices: List[float], period: int) -> List[Optional[float]]:
    sma = []
    for i in range(len(prices)):
        if i < period - 1:
            sma.append(None)
        else:
            window = prices[i - period + 1 : i + 1]
            sma.append(round(sum(window) / period, 2))
    return sma


def calculate_ema(prices: List[float], period: int) -> List[Optional[float]]:
    ema = []
    k = 2 / (period + 1)
    prev_ema = None

    for i in range(len(prices)):
        if i < period - 1:
            ema.append(None)
        elif i == period - 1:
            window = prices[:period]
            prev_ema = sum(window) / period
            ema.append(round(prev_ema, 2))
        else:
            curr_ema = (prices[i] * k) + (prev_ema * (1 - k))
            prev_ema = curr_ema
            ema.append(round(curr_ema, 2))
    return ema


def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    rsi = [None] * len(prices)
    if len(prices) <= period:
        return rsi

    gains = []
    losses = []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(diff))

    if len(gains) < period:
        return rsi

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        rsi[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi[period] = round(100 - (100 / (1 + rs)), 2)

    for i in range(period + 1, len(prices)):
        idx = i - 1
        avg_gain = (avg_gain * (period - 1) + gains[idx]) / period
        avg_loss = (avg_loss * (period - 1) + losses[idx]) / period

        if avg_loss == 0:
            rsi[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i] = round(100 - (100 / (1 + rs)), 2)

    return rsi


def calculate_macd(
    prices: List[float], fast: int = 12, slow: int = 26, signal_period: int = 9
) -> Dict[str, List[Optional[float]]]:
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)

    macd_line: List[Optional[float]] = []
    valid_macd_values: List[float] = []
    valid_indices: List[int] = []

    for i in range(len(prices)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            val = round(ema_fast[i] - ema_slow[i], 2)
            macd_line.append(val)
            valid_macd_values.append(val)
            valid_indices.append(i)
        else:
            macd_line.append(None)

    signal_line: List[Optional[float]] = [None] * len(prices)
    histogram: List[Optional[float]] = [None] * len(prices)

    if len(valid_macd_values) >= signal_period:
        signal_calc = calculate_ema(valid_macd_values, signal_period)
        for idx, sig in zip(valid_indices, signal_calc):
            signal_line[idx] = sig
            if macd_line[idx] is not None and sig is not None:
                histogram[idx] = round(macd_line[idx] - sig, 2)

    return {
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram,
    }


def compute_indicators_series(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not history:
        return {
            "sma20": [],
            "sma50": [],
            "ema12": [],
            "ema26": [],
            "rsi14": [],
            "macd": {"macd_line": [], "signal_line": [], "histogram": []},
            "latest": {"rsi": 50.0, "macd_signal": "NEUTRAL", "sma20": None},
        }

    closes = [item["close"] for item in history]

    sma20 = calculate_sma(closes, 20)
    sma50 = calculate_sma(closes, 50)
    ema12 = calculate_ema(closes, 12)
    ema26 = calculate_ema(closes, 26)
    rsi14 = calculate_rsi(closes, 14)
    macd = calculate_macd(closes, 12, 26, 9)

    latest_rsi = next((r for r in reversed(rsi14) if r is not None), 50.0)
    latest_hist = next((h for h in reversed(macd["histogram"]) if h is not None), 0.0)

    rsi_status = "NEUTRAL"
    if latest_rsi >= 70:
        rsi_status = "OVERBOUGHT"
    elif latest_rsi <= 30:
        rsi_status = "OVERSOLD"

    macd_status = "BULLISH" if latest_hist > 0 else "BEARISH" if latest_hist < 0 else "NEUTRAL"

    return {
        "sma20": sma20,
        "sma50": sma50,
        "ema12": ema12,
        "ema26": ema26,
        "rsi14": rsi14,
        "macd": macd,
        "latest": {
            "rsi": latest_rsi,
            "rsi_status": rsi_status,
            "macd_histogram": latest_hist,
            "macd_status": macd_status,
            "sma20": next((s for s in reversed(sma20) if s is not None), None),
        },
    }
