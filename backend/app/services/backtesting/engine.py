"""Deterministic, long-only historical backtesting engine.

Signals are evaluated only on completed candle closes and executed at the next
candle open. An open position is liquidated at the final close for end-of-period
valuation. All order cash arithmetic is rounded to cents; fractional shares and
leverage are not supported.
"""

from __future__ import annotations

import math
import statistics
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from typing import Any

from app.services.indicators import calculate_ema, calculate_macd, calculate_rsi, calculate_sma

CENT = Decimal("0.01")


def _money(value: Decimal | float | int) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _indicator_series(candles: list[dict[str, Any]]) -> dict[str, list[float | None]]:
    closes = [float(bar["close"]) for bar in candles]
    volumes = [float(bar["volume"]) for bar in candles]
    sma20 = calculate_sma(closes, 20)
    sma50 = calculate_sma(closes, 50)
    sma200 = calculate_sma(closes, 200)
    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)
    rsi14 = calculate_rsi(closes, 14)
    macd = calculate_macd(closes, 12, 26, 9)

    upper: list[float | None] = []
    middle: list[float | None] = []
    lower: list[float | None] = []
    atr14: list[float | None] = []
    true_ranges: list[float] = []
    for index, bar in enumerate(candles):
        if index >= 19:
            window = closes[index - 19 : index + 1]
            mean = sum(window) / 20
            std = math.sqrt(sum((item - mean) ** 2 for item in window) / 20)
            middle.append(mean)
            upper.append(mean + 2 * std)
            lower.append(mean - 2 * std)
        else:
            upper.append(None)
            middle.append(None)
            lower.append(None)

        previous_close = closes[index - 1] if index else float(bar["close"])
        true_ranges.append(max(
            float(bar["high"]) - float(bar["low"]),
            abs(float(bar["high"]) - previous_close),
            abs(float(bar["low"]) - previous_close),
        ))
        atr14.append(sum(true_ranges[index - 13 : index + 1]) / 14 if index >= 13 else None)

    return {
        "SMA20": sma20,
        "SMA50": sma50,
        "SMA200": sma200,
        "EMA20": ema20,
        "EMA50": ema50,
        "RSI": rsi14,
        "MACD": macd["macd_line"],
        "MACD_SIGNAL": macd["signal_line"],
        "BOLLINGER_UPPER": upper,
        "BOLLINGER_MIDDLE": middle,
        "BOLLINGER_LOWER": lower,
        "ATR": atr14,
        "VOLUME": volumes,
    }


def _condition(condition: dict[str, Any], index: int, values: dict[str, list[float | None]]) -> bool:
    left_series = values[condition["left"]]
    left = left_series[index]
    if left is None:
        return False

    right_spec = condition["right"]
    if isinstance(right_spec, dict):
        right_series = values[right_spec["indicator"]]
        right = right_series[index]
        previous_right = right_series[index - 1] if index > 0 else None
    else:
        right = float(right_spec)
        previous_right = right
    if right is None:
        return False

    operator = condition["operator"]
    if operator == ">":
        return left > right
    if operator == "<":
        return left < right
    if operator == ">=":
        return left >= right
    if operator == "<=":
        return left <= right
    previous_left = left_series[index - 1] if index > 0 else None
    if previous_left is None or previous_right is None:
        return False
    if operator == "crosses_above":
        return previous_left <= previous_right and left > right
    if operator == "crosses_below":
        return previous_left >= previous_right and left < right
    return False


def _conditions_match(conditions: list[dict[str, Any]], join: str, index: int, values: dict[str, list[float | None]]) -> bool:
    if not conditions:
        return False
    results = [_condition(item, index, values) for item in conditions]
    return all(results) if join == "AND" else any(results)


def _signal(strategy: dict[str, Any], index: int, values: dict[str, list[float | None]], in_position: bool) -> tuple[str | None, str]:
    kind = strategy["type"]
    if kind == "buy_hold":
        return ("BUY", "Buy & Hold baseline") if index == 0 and not in_position else (None, "")

    if kind == "golden_cross":
        if index == 0 or values["SMA20"][index] is None or values["SMA50"][index] is None:
            return None, ""
        previous_fast, previous_slow = values["SMA20"][index - 1], values["SMA50"][index - 1]
        fast, slow = values["SMA20"][index], values["SMA50"][index]
        if previous_fast is None or previous_slow is None:
            return None, ""
        if not in_position and previous_fast <= previous_slow and fast > slow:
            return "BUY", "SMA20 crossed above SMA50"
        if in_position and previous_fast >= previous_slow and fast < slow:
            return "SELL", "SMA20 crossed below SMA50"
        return None, ""

    if kind == "rsi_momentum":
        if index == 0 or values["RSI"][index] is None or values["RSI"][index - 1] is None:
            return None, ""
        previous, current = values["RSI"][index - 1], values["RSI"][index]
        if not in_position and previous <= 30 < current:
            return "BUY", "RSI crossed above 30"
        if in_position and previous <= 70 < current:
            return "SELL", "RSI crossed above 70"
        return None, ""

    if kind == "macd_trend":
        if index == 0:
            return None, ""
        previous_macd, previous_signal = values["MACD"][index - 1], values["MACD_SIGNAL"][index - 1]
        current_macd, current_signal = values["MACD"][index], values["MACD_SIGNAL"][index]
        if None in (previous_macd, previous_signal, current_macd, current_signal):
            return None, ""
        if not in_position and previous_macd <= previous_signal and current_macd > current_signal:
            return "BUY", "MACD crossed above signal line"
        if in_position and previous_macd >= previous_signal and current_macd < current_signal:
            return "SELL", "MACD crossed below signal line"
        return None, ""

    if kind == "conservative_trend":
        sma50, sma200, rsi = values["SMA50"][index], values["SMA200"][index], values["RSI"][index]
        if sma50 is None or sma200 is None:
            return None, ""
        if not in_position and sma50 > sma200 and rsi is not None and 40 <= rsi <= 65:
            return "BUY", "SMA50 > SMA200 and RSI is between 40 and 65"
        if in_position and sma50 < sma200:
            return "SELL", "SMA50 fell below SMA200"
        return None, ""

    if kind == "custom":
        entry = strategy["entry"]
        exit_rule = strategy["exit"]
        if not in_position and _conditions_match(entry["conditions"], entry["join"], index, values):
            return "BUY", "Custom entry conditions matched"
        if in_position and _conditions_match(exit_rule["conditions"], exit_rule["join"], index, values):
            return "SELL", "Custom exit conditions matched"
    return None, ""


def _strategy_indicators(strategy: dict[str, Any]) -> set[str]:
    required = {
        "golden_cross": {"SMA20", "SMA50"},
        "rsi_momentum": {"RSI"},
        "macd_trend": {"MACD", "MACD_SIGNAL"},
        "conservative_trend": {"SMA50", "SMA200", "RSI"},
        "buy_hold": set(),
    }
    if strategy["type"] != "custom":
        return required[strategy["type"]]
    indicators: set[str] = set()
    for group_key in ("entry", "exit"):
        for condition in strategy[group_key]["conditions"]:
            indicators.add(condition["left"])
            if isinstance(condition["right"], dict):
                indicators.add(condition["right"]["indicator"])
    return indicators


def validate_candles(candles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(candles) < 2:
        raise ValueError("Backtest unavailable because insufficient historical candles were returned.")
    validated: list[dict[str, Any]] = []
    for candle in candles:
        try:
            timestamp = datetime.fromisoformat(str(candle["timestamp"]).replace("Z", "+00:00"))
            values = {name: float(candle[name]) for name in ("open", "high", "low", "close", "volume")}
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Historical data contains missing or invalid OHLCV fields.") from exc
        if any(not math.isfinite(value) for value in values.values()):
            raise ValueError("Historical data contains non-finite OHLCV values.")
        if any(values[key] <= 0 for key in ("open", "high", "low", "close")) or values["volume"] < 0:
            raise ValueError("Historical data contains invalid prices or volume.")
        if values["high"] < max(values["open"], values["close"], values["low"]) or values["low"] > min(values["open"], values["close"], values["high"]):
            raise ValueError("Historical OHLC data is inconsistent.")
        validated.append({**candle, **values, "timestamp": timestamp})

    validated.sort(key=lambda row: row["timestamp"])
    timestamps = [row["timestamp"] for row in validated]
    if len(set(timestamps)) != len(timestamps):
        raise ValueError("Historical data contains duplicate candle timestamps.")
    return validated


def _new_trade(trade_id: int, date: datetime, action: str, symbol: str, raw_price: Decimal, execution_price: Decimal,
              quantity: int, fee: Decimal, slippage: Decimal, cash: Decimal, position: int, reason: str,
              realized_pnl: Decimal | None = None) -> dict[str, Any]:
    gross = _money(execution_price * quantity)
    return {
        "trade_id": f"T{trade_id:04d}",
        "timestamp": date.isoformat(),
        "symbol": symbol,
        "action": action,
        "raw_price": float(raw_price),
        "execution_price": float(execution_price),
        "quantity": quantity,
        "gross_value": float(gross),
        "transaction_cost": float(fee),
        "slippage_cost": float(slippage),
        "net_value": float(_money(gross + fee if action == "BUY" else gross - fee)),
        "remaining_cash": float(cash),
        "position_quantity": position,
        "realized_pnl": float(realized_pnl) if realized_pnl is not None else None,
        "reason": reason,
    }


def run_backtest(
    candles: list[dict[str, Any]],
    symbol: str,
    strategy: dict[str, Any],
    start_date: datetime,
    end_date: datetime,
    initial_capital: Decimal,
    transaction_cost_pct: Decimal,
    slippage_pct: Decimal,
    position_pct: Decimal = Decimal("100"),
) -> dict[str, Any]:
    all_rows = validate_candles(candles)
    selected_indices = [
        index for index, row in enumerate(all_rows)
        if start_date <= row["timestamp"] < end_date
    ]
    rows = [all_rows[index] for index in selected_indices]
    if len(rows) < 2:
        raise ValueError("Backtest unavailable because historical data for the selected period is unavailable.")
    if (rows[-1]["timestamp"] - rows[0]["timestamp"]).days < 2:
        raise ValueError("Insufficient historical period for a backtest.")

    capital = _money(initial_capital)
    cash = capital
    position = 0
    allocated_entry_cost = Decimal("0.00")
    entry_gross = Decimal("0.00")
    entry_date: datetime | None = None
    trades: list[dict[str, Any]] = []
    equity_curve: list[dict[str, Any]] = []
    # Indicators are calculated over the preceding warm-up history too. Each
    # value remains causal (the shared indicator functions only use <= index).
    values = _indicator_series(all_rows)
    required_indicators = _strategy_indicators(strategy)
    if required_indicators and any(
        not any(values[name][source_index] is not None for source_index in selected_indices)
        for name in required_indicators
    ):
        names = ", ".join(sorted(required_indicators))
        raise ValueError(f"Insufficient historical warm-up data for this strategy's indicators: {names}.")
    trade_id = 1

    # Include initial capital before the first period's open/close movement so
    # first-day costs or an opening gap can appear in drawdown and return series.
    equity_curve.append({
        "timestamp": rows[0]["timestamp"].isoformat(),
        "date": rows[0]["timestamp"].date().isoformat(),
        "close": None,
        "cash": float(cash),
        "position_quantity": 0,
        "market_value": 0.0,
        "portfolio_value": float(capital),
        "phase": "initial_capital",
    })

    def execute_buy(bar: dict[str, Any], raw_open: float, reason: str) -> None:
        nonlocal cash, position, allocated_entry_cost, entry_gross, entry_date, trade_id
        raw = Decimal(str(raw_open))
        price = _money(raw * (Decimal("1") + slippage_pct / Decimal("100")))
        target_cash = _money(cash * position_pct / Decimal("100"))
        fee_rate = transaction_cost_pct / Decimal("100")
        unit_cost = price * (Decimal("1") + fee_rate)
        quantity = int((target_cash / unit_cost).to_integral_value(rounding=ROUND_FLOOR))
        if quantity <= 0:
            return
        gross = _money(price * quantity)
        fee = _money(gross * fee_rate)
        if gross + fee > cash:
            quantity = int((cash / unit_cost).to_integral_value(rounding=ROUND_FLOOR))
            if quantity <= 0:
                return
            gross = _money(price * quantity)
            fee = _money(gross * fee_rate)
        slippage_cost = _money(abs(price - raw) * quantity)
        cash = _money(cash - gross - fee)
        position = quantity
        allocated_entry_cost = fee
        entry_gross = gross
        entry_date = bar["timestamp"]
        trades.append(_new_trade(trade_id, bar["timestamp"], "BUY", symbol, raw, price, quantity, fee,
                                 slippage_cost, cash, position, reason))
        trade_id += 1

    def execute_sell(bar: dict[str, Any], raw_close_or_open: float, reason: str) -> None:
        nonlocal cash, position, allocated_entry_cost, entry_gross, entry_date, trade_id
        if position <= 0:
            return
        raw = Decimal(str(raw_close_or_open))
        price = _money(raw * (Decimal("1") - slippage_pct / Decimal("100")))
        gross = _money(price * position)
        fee = _money(gross * transaction_cost_pct / Decimal("100"))
        slippage_cost = _money(abs(raw - price) * position)
        realized = _money(gross - fee - entry_gross - allocated_entry_cost)
        cash = _money(cash + gross - fee)
        quantity = position
        position = 0
        trades.append(_new_trade(trade_id, bar["timestamp"], "SELL", symbol, raw, price, quantity, fee,
                                 slippage_cost, cash, position, reason, realized))
        trades[-1]["realized_pnl_pct"] = round(float(realized / entry_gross * 100), 4) if entry_gross else None
        trades[-1]["holding_period_days"] = max(0, (bar["timestamp"] - entry_date).days) if entry_date else 0
        trade_id += 1
        allocated_entry_cost = Decimal("0.00")
        entry_gross = Decimal("0.00")
        entry_date = None

    # Buy & Hold enters on the first available opening price, with the same costs.
    if strategy["type"] == "buy_hold":
        execute_buy(rows[0], rows[0]["open"], "Buy & Hold at first period open")

    for index, bar in enumerate(rows):
        source_index = selected_indices[index]
        # A completed bar's signal is executed at the following bar's open.
        if strategy["type"] != "buy_hold" and index > 0:
            action, reason = _signal(strategy, source_index - 1, values, position > 0)
            if action == "BUY":
                execute_buy(bar, bar["open"], reason)
            elif action == "SELL":
                execute_sell(bar, bar["open"], reason)

        market_value = _money(Decimal(str(bar["close"])) * position)
        total_value = _money(cash + market_value)
        equity_curve.append({
            "timestamp": bar["timestamp"].isoformat(),
            "date": bar["timestamp"].date().isoformat(),
            "close": bar["close"],
            "cash": float(cash),
            "position_quantity": position,
            "market_value": float(market_value),
            "portfolio_value": float(total_value),
        })

    # Liquidate at the final close to calculate realized end-of-period results.
    if position > 0:
        execute_sell(rows[-1], rows[-1]["close"], "End-of-period liquidation at final close")
        last = equity_curve[-1]
        last["cash"] = float(cash)
        last["position_quantity"] = 0
        last["market_value"] = 0.0
        last["portfolio_value"] = float(cash)

    final_value = cash
    values_equity = [point["portfolio_value"] for point in equity_curve]
    peak = values_equity[0]
    peak_date = equity_curve[0]["date"]
    maximum_drawdown = 0.0
    max_drawdown_amount = 0.0
    drawdown_peak = peak
    drawdown_trough = peak
    drawdown_peak_date = peak_date
    drawdown_trough_date = peak_date
    drawdown_curve: list[dict[str, Any]] = []
    for point in equity_curve:
        current = point["portfolio_value"]
        if current > peak:
            peak = current
            peak_date = point["date"]
        amount = peak - current
        pct = (current / peak - 1) * 100 if peak else 0.0
        point["drawdown_pct"] = round(pct, 4)
        drawdown_curve.append({"date": point["date"], "timestamp": point["timestamp"], "drawdown_pct": round(pct, 4)})
        if pct < maximum_drawdown:
            maximum_drawdown = pct
            max_drawdown_amount = amount
            drawdown_peak = peak
            drawdown_trough = current
            drawdown_peak_date = peak_date
            drawdown_trough_date = point["date"]

    daily_returns = [
        values_equity[index] / values_equity[index - 1] - 1
        for index in range(1, len(values_equity)) if values_equity[index - 1] > 0
    ]
    sharpe: float | None = None
    if len(daily_returns) >= 2:
        mean_return = sum(daily_returns) / len(daily_returns)
        variance = sum((value - mean_return) ** 2 for value in daily_returns) / (len(daily_returns) - 1)
        standard_deviation = math.sqrt(variance)
        if standard_deviation > 0:
            sharpe = mean_return / standard_deviation * math.sqrt(252)

    closed_trades = [trade for trade in trades if trade["action"] == "SELL" and trade["realized_pnl"] is not None]
    winning = [trade for trade in closed_trades if trade["realized_pnl"] > 0]
    losing = [trade for trade in closed_trades if trade["realized_pnl"] < 0]
    trade_returns = [trade["realized_pnl_pct"] for trade in closed_trades if trade.get("realized_pnl_pct") is not None]
    duration_days = max(1, (rows[-1]["timestamp"] - rows[0]["timestamp"]).days)
    years = duration_days / 365.2425
    total_return = (float(final_value / capital) - 1) * 100 if capital else 0.0
    cagr = ((float(final_value / capital) ** (1 / years)) - 1) * 100 if years >= 1 and final_value > 0 else None
    gross_wins = sum(trade["realized_pnl"] for trade in winning)
    gross_losses = abs(sum(trade["realized_pnl"] for trade in losing))

    return {
        "symbol": symbol,
        "strategy": strategy,
        "period": {"start": rows[0]["timestamp"].date().isoformat(), "end": rows[-1]["timestamp"].date().isoformat()},
        "metrics": {
            "initial_capital": float(capital),
            "final_value": float(final_value),
            "net_profit_loss": float(_money(final_value - capital)),
            "total_return_pct": round(total_return, 4),
            "total_trades": len(closed_trades),
            "buy_orders": sum(1 for trade in trades if trade["action"] == "BUY"),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate_pct": round(len(winning) / len(closed_trades) * 100, 2) if closed_trades else None,
            "average_winning_trade": round(sum(trade["realized_pnl"] for trade in winning) / len(winning), 2) if winning else None,
            "average_losing_trade": round(sum(trade["realized_pnl"] for trade in losing) / len(losing), 2) if losing else None,
            "best_trade_pct": round(max(trade_returns), 4) if trade_returns else None,
            "worst_trade_pct": round(min(trade_returns), 4) if trade_returns else None,
            "average_trade_return_pct": round(sum(trade_returns) / len(trade_returns), 4) if trade_returns else None,
            "profit_factor": round(gross_wins / gross_losses, 4) if gross_losses > 0 else None,
            "max_drawdown_pct": round(maximum_drawdown, 4),
            "max_drawdown_amount": round(max_drawdown_amount, 2),
            "drawdown_peak_value": round(drawdown_peak, 2),
            "drawdown_trough_value": round(drawdown_trough, 2),
            "drawdown_peak_date": drawdown_peak_date,
            "drawdown_trough_date": drawdown_trough_date,
            "sharpe_ratio": round(sharpe, 4) if sharpe is not None else None,
            "sharpe_annualization": "Daily returns, risk-free rate 0%, annualized with sqrt(252).",
            "cagr_pct": round(cagr, 4) if cagr is not None else None,
            "daily_volatility_pct": round(statistics.pstdev(daily_returns) * math.sqrt(252) * 100, 4) if len(daily_returns) > 1 else None,
        },
        "trades": trades,
        "equity_curve": equity_curve,
        "drawdown_curve": drawdown_curve,
        "data": {
            "candles": len(rows),
            "frequency": "Daily",
            "first_timestamp": rows[0]["timestamp"].isoformat(),
            "last_timestamp": rows[-1]["timestamp"].isoformat(),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        },
    }
