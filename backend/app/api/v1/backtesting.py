import asyncio
import logging
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_active_user
from app.integrations.market_data.yahoo_provider import YahooFinanceProvider
from app.database.session import get_async_db
from app.models.backtesting import BacktestRun
from app.models.user import User
from app.schemas.backtesting import BacktestAnalysisRequest, BacktestRequest
from app.services.backtesting.engine import run_backtest, validate_candles
from app.services.market_data import get_market_provider
from app.services.stock_universe import INDIAN_EQUITY_UNIVERSE

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backtesting", tags=["Backtesting Lab"])

PRESETS: dict[str, dict[str, Any]] = {
    "golden_cross": {"type": "golden_cross", "name": "Golden Cross", "entry_text": "SMA20 crosses above SMA50", "exit_text": "SMA20 crosses below SMA50"},
    "rsi_momentum": {"type": "rsi_momentum", "name": "RSI Momentum", "entry_text": "RSI crosses above 30", "exit_text": "RSI crosses above 70"},
    "macd_trend": {"type": "macd_trend", "name": "MACD Trend", "entry_text": "MACD crosses above Signal", "exit_text": "MACD crosses below Signal"},
    "conservative_trend": {"type": "conservative_trend", "name": "Conservative Trend", "entry_text": "SMA50 > SMA200 and RSI is 40–65", "exit_text": "SMA50 < SMA200"},
    "buy_hold": {"type": "buy_hold", "name": "Buy & Hold", "entry_text": "Buy at the first period open", "exit_text": "Liquidate at the final period close"},
}


def _serialize_strategy(config) -> dict[str, Any]:
    strategy = {"type": config.type, "name": config.name or PRESETS.get(config.type, {}).get("name", "Custom strategy")}
    if config.type == "custom":
        strategy["entry"] = {
            "join": config.entry.join,
            "conditions": [
                {"left": item.left, "operator": item.operator,
                 "right": {"indicator": item.right_indicator} if item.right_indicator else float(item.right_value)}
                for item in config.entry.conditions
            ],
        }
        strategy["exit"] = {
            "join": config.exit.join,
            "conditions": [
                {"left": item.left, "operator": item.operator,
                 "right": {"indicator": item.right_indicator} if item.right_indicator else float(item.right_value)}
                for item in config.exit.conditions
            ],
        }
    return strategy


async def _fetch_daily_history(symbol: str, exchange: str | None, start_date, end_date) -> tuple[list[dict[str, Any]], str]:
    provider = get_market_provider()
    provider_name = provider.provider_name()
    if not isinstance(provider, YahooFinanceProvider):
        raise HTTPException(
            status_code=503,
            detail=f"Date-bounded real daily history is not available from the configured provider ({provider_name}). Select Yahoo Finance or configure a provider with date-range support. No substitute/mock candles were used.",
        )

    try:
        quote = await asyncio.wait_for(provider.get_stock_quote(symbol), timeout=15)
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Quote lookup timed out before the historical simulation could start.") from exc
    except Exception as exc:
        logger.exception("Backtest quote lookup failed for %s", symbol)
        raise HTTPException(status_code=502, detail="The market-data provider failed to verify this stock.") from exc
    if not quote:
        raise HTTPException(status_code=422, detail=f"No verified quote was returned for {symbol}.")
    if quote.get("currency") != "INR":
        raise HTTPException(status_code=422, detail="The Backtesting Lab currently supports INR-denominated NSE/BSE equities only.")

    ticker_symbol = symbol.strip().upper()
    is_index = ticker_symbol == "NIFTY50"
    if exchange == "BSE" and not ticker_symbol.endswith(".BO"):
        ticker_symbol = f"{ticker_symbol}.BO"
    elif exchange == "NSE" and not ticker_symbol.endswith(".NS") and not is_index:
        ticker_symbol = f"{ticker_symbol}.NS"

    warmup_start = start_date - timedelta(days=450)
    end_exclusive = end_date + timedelta(days=1)
    try:
        candles = await asyncio.wait_for(
            provider.get_historical_prices(
                ticker_symbol,
                timeframe="1D",
                start=warmup_start.isoformat(),
                end=end_exclusive.isoformat(),
            ),
            timeout=45,
        )
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Historical market-data request timed out. Please retry with a shorter period.") from exc
    except Exception as exc:
        logger.exception("Backtest history retrieval failed for %s", ticker_symbol)
        raise HTTPException(status_code=502, detail="The historical-data provider failed to retrieve this period.") from exc

    real_rows = [row for row in candles if row.get("source") == "Yahoo Finance" and row.get("data_status") != "DEVELOPMENT DATA"]
    if not real_rows:
        raise HTTPException(status_code=422, detail="Backtest unavailable because real historical OHLCV data for the selected stock/period is unavailable.")
    selected = []
    for row in real_rows:
        try:
            stamp = datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00"))
            row_date = stamp.date()
        except (KeyError, ValueError, TypeError):
            continue
        if start_date <= row_date <= end_date:
            selected.append(row)
    if len(selected) < 2:
        raise HTTPException(status_code=422, detail="Backtest unavailable because fewer than two real daily candles exist in the selected period.")
    return real_rows, ticker_symbol


@router.get("/strategies")
async def list_strategies(_: User = Depends(get_current_active_user)) -> list[dict[str, Any]]:
    return list(PRESETS.values()) + [{"type": "custom", "name": "Custom Strategy", "entry_text": "Build your own conditions", "exit_text": "Build your own conditions"}]


@router.post("/run")
async def run_historical_backtest(
    payload: BacktestRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Run an authenticated deterministic backtest using real date-bounded daily candles."""
    strategy = _serialize_strategy(payload.strategy)
    if strategy["type"] == "custom":
        allowed = {"SMA20", "SMA50", "SMA200", "EMA20", "EMA50", "RSI", "MACD", "MACD_SIGNAL", "BOLLINGER_UPPER", "BOLLINGER_MIDDLE", "BOLLINGER_LOWER", "ATR", "VOLUME"}
        for group in (strategy["entry"], strategy["exit"]):
            for condition in group["conditions"]:
                if condition["left"] not in allowed or (isinstance(condition["right"], dict) and condition["right"]["indicator"] not in allowed):
                    raise HTTPException(status_code=422, detail="Custom strategy contains an unsupported indicator.")

    candles, market_symbol = await _fetch_daily_history(payload.symbol, payload.exchange, payload.start_date, payload.end_date)
    start_dt = datetime.combine(payload.start_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(payload.end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
    initial_capital = Decimal(payload.initial_capital).quantize(Decimal("0.01"))
    costs = Decimal(payload.transaction_cost_pct)
    slippage = Decimal(payload.slippage_pct)
    position_pct = Decimal(payload.position_pct)

    try:
        result = run_backtest(candles, market_symbol, strategy, start_dt, end_dt, initial_capital, costs, slippage, position_pct)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # A same-asset buy-and-hold baseline uses the exact same daily candles,
    # costs, slippage, execution and cash constraints.
    baseline_strategy = {"type": "buy_hold", "name": "Buy & Hold"}
    baseline = run_backtest(candles, market_symbol, baseline_strategy, start_dt, end_dt, initial_capital, costs, slippage, Decimal("100"))
    benchmark_metrics = None
    benchmark_map: dict[str, float] = {}
    try:
        benchmark_candles, _ = await _fetch_daily_history("NIFTY50", "NSE", payload.start_date, payload.end_date)
        benchmark_rows = [
            row for row in validate_candles(benchmark_candles)
            if start_dt <= row["timestamp"] < end_dt
        ]
        if len(benchmark_rows) >= 2 and benchmark_rows[0]["close"] > 0:
            base_close = benchmark_rows[0]["close"]
            benchmark_map = {
                row["timestamp"].date().isoformat(): float(initial_capital) * row["close"] / base_close
                for row in benchmark_rows
            }
            benchmark_final = benchmark_map[benchmark_rows[-1]["timestamp"].date().isoformat()]
            benchmark_metrics = {
                "initial_capital": float(initial_capital),
                "final_value": round(benchmark_final, 2),
                "total_return_pct": round((benchmark_final / float(initial_capital) - 1) * 100, 4),
                "method": "NIFTY 50 price-index return; scaled to initial capital, no investable units or trading costs assumed.",
            }
    except (HTTPException, ValueError) as exc:
        logger.info("NIFTY 50 benchmark unavailable for this period: %s", exc)

    baseline_map = {item["date"]: item["portfolio_value"] for item in baseline["equity_curve"]}
    benchmark_dates = sorted(benchmark_map)
    benchmark_cursor = 0
    benchmark_last_value: float | None = None
    for point in result["equity_curve"]:
        if point.get("phase") == "initial_capital":
            point["buy_hold_value"] = float(initial_capital)
            point["benchmark_value"] = float(initial_capital) if benchmark_metrics else None
            continue
        point["buy_hold_value"] = baseline_map.get(point["date"])
        while benchmark_cursor < len(benchmark_dates) and benchmark_dates[benchmark_cursor] <= point["date"]:
            benchmark_last_value = benchmark_map[benchmark_dates[benchmark_cursor]]
            benchmark_cursor += 1
        point["benchmark_value"] = benchmark_last_value

    strategy_return = result["metrics"]["total_return_pct"]
    buy_hold_return = baseline["metrics"]["total_return_pct"]
    comparison = {
        "strategy_return_pct": strategy_return,
        "buy_hold_return_pct": buy_hold_return,
        "outperformance_vs_buy_hold_pct_points": round(strategy_return - buy_hold_return, 4),
        "nifty50_return_pct": benchmark_metrics["total_return_pct"] if benchmark_metrics else None,
        "outperformance_vs_nifty50_pct_points": round(strategy_return - benchmark_metrics["total_return_pct"], 4) if benchmark_metrics else None,
        "nifty50_unavailable_reason": None if benchmark_metrics else "NIFTY 50 benchmark unavailable for this period from the configured real-data provider.",
    }

    strategy_comparison = []
    if payload.compare_strategies:
        for preset in PRESETS.values():
            try:
                compared = run_backtest(
                    candles, market_symbol, {"type": preset["type"], "name": preset["name"]},
                    start_dt, end_dt, initial_capital, costs, slippage, position_pct,
                )
                strategy_comparison.append({
                    "strategy": preset["name"],
                    "return_pct": compared["metrics"]["total_return_pct"],
                    "max_drawdown_pct": compared["metrics"]["max_drawdown_pct"],
                    "sharpe_ratio": compared["metrics"]["sharpe_ratio"],
                    "win_rate_pct": compared["metrics"]["win_rate_pct"],
                    "total_trades": compared["metrics"]["total_trades"],
                })
            except ValueError:
                continue
        strategy_comparison.sort(key=lambda row: row["return_pct"], reverse=True)

    response_data = {
        "backtest_id": str(uuid4()),
        "symbol": market_symbol,
        "strategy": strategy,
        "strategy_summary": {
            "name": strategy["name"],
            "entry": PRESETS.get(strategy["type"], {}).get("entry_text", strategy.get("entry")),
            "exit": PRESETS.get(strategy["type"], {}).get("exit_text", strategy.get("exit")),
        },
        "assumptions": {
            "initial_capital": float(initial_capital),
            "transaction_cost_pct": float(costs),
            "slippage_pct": float(slippage),
            "position_pct": float(position_pct),
            "execution_model": "Signal on completed candle close; execute at next available candle open adjusted for slippage. Open position is liquidated at final period close.",
            "fractional_shares": False,
            "leverage": False,
            "short_selling": False,
        },
        "metrics": result["metrics"],
        "trades": result["trades"],
        "equity_curve": result["equity_curve"],
        "drawdown_curve": result["drawdown_curve"],
        "comparison": comparison,
        "strategy_comparison": strategy_comparison,
        "buy_hold_metrics": baseline["metrics"],
        "benchmark_metrics": benchmark_metrics,
        "data": {
            **result["data"],
            "provider": "Yahoo Finance",
            "source": "Yahoo Finance historical OHLCV",
            "status": "HISTORICAL",
            "price_adjustment": "Yahoo Finance auto-adjusted OHLC (adjusted for provider-reported corporate actions; volume is as reported).",
            "requested_period": {"start": payload.start_date.isoformat(), "end": payload.end_date.isoformat()},
            "warmup_days": 450,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        },
        "notice": "Historical simulation only. Past backtest performance does not guarantee future results.",
    }
    db.add(BacktestRun(
        id=response_data["backtest_id"],
        user_id=current_user.id,
        symbol=market_symbol,
        strategy_type=strategy["type"],
        result_json=response_data,
    ))
    await db.commit()
    return response_data


@router.post("/analyze")
async def analyze_backtest(
    payload: BacktestAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """Explain engine-calculated results; the model is not asked to calculate metrics."""
    query = select(BacktestRun).where(
        BacktestRun.id == payload.backtest_id,
        BacktestRun.user_id == current_user.id,
    )
    record = (await db.execute(query)).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Backtest result not found for this account.")
    result = record.result_json
    metrics = result.get("metrics")
    if not isinstance(metrics, dict) or not result.get("symbol") or not result.get("strategy"):
        raise HTTPException(status_code=422, detail="A complete engine-generated backtest result is required for analysis.")
    comparison = result.get("comparison") or {}
    if not settings.AI_API_KEY:
        return {
            "analysis": _metrics_based_analysis(result, metrics, comparison),
            "backtest_id": result.get("backtest_id"),
            "mode": "deterministic explanation of server-calculated metrics",
        }
    grounded = {
        "symbol": result["symbol"],
        "strategy": result["strategy"],
        "period": result.get("period") or result.get("data", {}).get("requested_period"),
        "metrics": metrics,
        "comparison": result.get("comparison"),
        "trade_count": len(result.get("trades", [])),
        "best_and_worst_trade_records": sorted(
            [trade for trade in result.get("trades", []) if trade.get("realized_pnl") is not None],
            key=lambda trade: trade["realized_pnl"],
        )[:1] + sorted(
            [trade for trade in result.get("trades", []) if trade.get("realized_pnl") is not None],
            key=lambda trade: trade["realized_pnl"], reverse=True,
        )[:1],
    }
    system = (
        "You explain historical backtests using only the supplied, server-calculated values. Never calculate, alter, infer, or invent financial metrics or missing periods. "
        "Use these exact headings: Overall Assessment; What Worked; Risk; Weaknesses; Important Observations; Final Assessment. "
        "Explain observations only where supported by the supplied data; if timing or strongest/weakest periods are not provided, say that they are unavailable. "
        "Use cautious phrases such as historically and under these assumptions. Never say buy this stock, guarantee profits, or claim future performance. "
        "Always end with: Past backtest performance does not guarantee future results. This is not financial advice."
    )
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.AI_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
                json={
                    "model": settings.AI_MODEL,
                    "temperature": 0.2,
                    "max_tokens": 700,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": f"Explain these verified backtest results using the required headings. Do not recalculate them:\n{grounded}"},
                    ],
                },
            )
            response.raise_for_status()
            analysis = response.json()["choices"][0]["message"]["content"]
            if not isinstance(analysis, str) or not analysis.strip():
                raise ValueError("The AI provider returned an empty analysis.")
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        logger.exception("Backtest AI analysis failed for user %s", current_user.id)
        raise HTTPException(status_code=502, detail="SmartStock AI could not analyze this result right now.") from exc
    analysis = analysis.strip()
    required_notice = "Past backtest performance does not guarantee future results. This is not financial advice."
    if required_notice not in analysis:
        analysis = f"{analysis}\n\n{required_notice}"
    return {"analysis": analysis, "backtest_id": result.get("backtest_id"), "mode": "AI explanation of server-calculated metrics"}


def _metrics_based_analysis(result: dict[str, Any], metrics: dict[str, Any], comparison: dict[str, Any]) -> str:
    """Honest no-key explanation generated only from persisted simulation metrics."""
    strategy_return = float(metrics.get("total_return_pct", 0))
    max_drawdown = float(metrics.get("max_drawdown_pct", 0))
    trades = int(metrics.get("total_trades", 0))
    win_rate = metrics.get("win_rate_pct")
    sharpe = metrics.get("sharpe_ratio")
    outperformance = comparison.get("outperformance_vs_buy_hold_pct_points")
    period = result.get("data", {}).get("requested_period") or {}
    period_text = f"{period.get('start', 'unknown start')} to {period.get('end', 'unknown end')}"
    result_line = "positive" if strategy_return > 0 else "negative" if strategy_return < 0 else "flat"
    buy_hold_line = (
        f"The strategy {'outperformed' if float(outperformance) > 0 else 'underperformed' if float(outperformance) < 0 else 'matched'} "
        f"same-stock Buy & Hold by {abs(float(outperformance)):.2f} percentage points."
        if outperformance is not None else "A same-stock Buy & Hold comparison was not available."
    )
    risk_line = (
        f"Maximum peak-to-trough drawdown was {max_drawdown:.2f}% (amount {metrics.get('max_drawdown_amount')}). "
        f"The annualized Sharpe ratio was {float(sharpe):.2f}."
        if sharpe is not None else
        f"Maximum peak-to-trough drawdown was {max_drawdown:.2f}% (amount {metrics.get('max_drawdown_amount')}). Sharpe is unavailable because the equity-return series was insufficient or had zero variation."
    )
    trade_line = (
        f"The simulation closed {trades} round trips with a win rate of {float(win_rate):.2f}%."
        if win_rate is not None else f"The simulation closed {trades} round trips; win rate is unavailable because there were no closed trades."
    )
    strategy_name = result.get("strategy", {}).get("name", result.get("strategy", {}).get("type", "strategy"))
    weak_periods = [
        trade for trade in result.get("trades", [])
        if trade.get("action") == "SELL" and trade.get("realized_pnl") is not None
    ]
    trade_observation = ""
    if weak_periods:
        worst = min(weak_periods, key=lambda trade: float(trade.get("realized_pnl", 0)))
        best = max(weak_periods, key=lambda trade: float(trade.get("realized_pnl", 0)))
        trade_observation = (
            f"Best included closed trade: {best.get('symbol')} {best.get('timestamp')} with realized P/L {best.get('realized_pnl')}. "
            f"Weakest included closed trade: {worst.get('symbol')} {worst.get('timestamp')} with realized P/L {worst.get('realized_pnl')}."
        )
    strategy_risk = {
        "golden_cross": "Moving-average crossovers can react late and can generate whipsaws in sideways markets.",
        "rsi_momentum": "RSI thresholds can trigger repeated or delayed signals; readings are historical and do not predict future returns.",
        "macd_trend": "MACD is a lagging trend indicator and may react late or whipsaw in range-bound periods.",
        "conservative_trend": "The SMA200 filter can delay entries and exits; this run still represents one stock and one selected period.",
        "buy_hold": "Buy & Hold remains exposed to the selected stock's full drawdowns and concentration risk.",
        "custom": "Custom rules may be overfit to the selected history; this single backtest is not independent validation.",
    }.get(result.get("strategy", {}).get("type"), "A historical simulation cannot establish future performance.")
    benchmark_text = (
        f" NIFTY 50 price-index return was {comparison['nifty50_return_pct']:.2f}% under the stated index-return convention."
        if comparison.get("nifty50_return_pct") is not None else " NIFTY 50 comparison was unavailable for this period."
    )
    return (
        f"Overall Assessment\n{strategy_name} produced a {result_line} historical return of {strategy_return:.2f}% "
        f"for {result.get('symbol')} over {period_text}, under the selected transaction-cost and slippage assumptions.\n\n"
        f"What Worked\n{buy_hold_line}{benchmark_text}\n\n"
        f"Risk\n{risk_line} {trade_line}\n\n"
        f"Weaknesses\n{strategy_risk} Trading costs, data coverage, and the chosen period affect these results.\n\n"
        f"Important Observations\n{trade_observation or 'No closed-trade best/worst comparison is available.'}\n\n"
        "Final Assessment\nThis describes only the supplied historical simulation and assumptions; it is not a forecast or a personalized recommendation. "
        "Past backtest performance does not guarantee future results. This is not financial advice."
    )


@router.get("/runs")
async def list_my_backtests(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> list[dict[str, Any]]:
    query = select(BacktestRun).where(BacktestRun.user_id == current_user.id).order_by(BacktestRun.created_at.desc()).limit(25)
    rows = (await db.execute(query)).scalars().all()
    return [
        {
            "backtest_id": row.id,
            "symbol": row.symbol,
            "strategy_type": row.strategy_type,
            "strategy_name": row.result_json.get("strategy", {}).get("name"),
            "period": row.result_json.get("data", {}).get("requested_period"),
            "metrics": row.result_json.get("metrics", {}),
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@router.get("/runs/{backtest_id}")
async def get_my_backtest(
    backtest_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    query = select(BacktestRun).where(BacktestRun.id == backtest_id, BacktestRun.user_id == current_user.id)
    record = (await db.execute(query)).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Backtest result not found for this account.")
    return record.result_json
