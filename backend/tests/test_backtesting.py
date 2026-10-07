from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.backtesting.engine import run_backtest

client = TestClient(app)


def candles(closes, opens=None):
    opens = opens or closes
    rows = []
    for index, (opening, closing) in enumerate(zip(opens, closes)):
        stamp = (datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=index)).isoformat()
        rows.append({
            "timestamp": stamp,
            "open": opening,
            "high": max(opening, closing) + 1,
            "low": min(opening, closing) - 1,
            "close": closing,
            "volume": 1000,
            "source": "Yahoo Finance",
        })
    return rows


def run(rows, strategy, capital="10000", costs="0", slippage="0", start_day=1):
    return run_backtest(
        rows,
        "TEST",
        strategy,
        datetime(2024, 1, start_day, tzinfo=timezone.utc),
        datetime(2024, 2, 1, tzinfo=timezone.utc),
        Decimal(capital),
        Decimal(costs),
        Decimal(slippage),
    )


def test_buy_and_hold_final_value_is_mathematically_correct():
    result = run(candles([10, 11, 12]), {"type": "buy_hold"})
    assert result["metrics"]["initial_capital"] == 10000
    assert result["trades"][0]["quantity"] == 1000
    assert result["metrics"]["final_value"] == 12000
    assert result["metrics"]["total_return_pct"] == 20


def test_costs_and_slippage_reduce_buy_and_hold_final_value():
    rows = candles([10, 11, 12])
    no_costs = run(rows, {"type": "buy_hold"})
    with_costs = run(rows, {"type": "buy_hold"}, costs="0.10")
    with_slippage = run(rows, {"type": "buy_hold"}, slippage="0.05")
    assert with_costs["metrics"]["final_value"] < no_costs["metrics"]["final_value"]
    assert with_slippage["trades"][0]["execution_price"] > with_slippage["trades"][0]["raw_price"]
    assert with_slippage["metrics"]["final_value"] < no_costs["metrics"]["final_value"]


def test_cannot_buy_more_than_cash_allows_or_sell_without_position():
    result = run(candles([1500, 1600, 1700]), {"type": "buy_hold"}, capital="1000")
    assert result["trades"] == []
    assert result["metrics"]["final_value"] == 1000

    no_signal = run_backtest(
        candles([100] * 60), "TEST", {"type": "golden_cross"},
        datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 3, 1, tzinfo=timezone.utc),
        Decimal("10000"), Decimal("0"), Decimal("0"),
    )
    assert all(trade["action"] != "SELL" for trade in no_signal["trades"])
    assert all(point["cash"] >= 0 and point["position_quantity"] >= 0 for point in no_signal["equity_curve"])


def test_golden_cross_waits_for_indicator_warmup_and_executes_next_open():
    from app.services.indicators import calculate_sma

    closes = [100.0] * 60 + [110.0] * 80
    rows = candles(closes)
    fast = calculate_sma(closes, 20)
    slow = calculate_sma(closes, 50)
    cross_index = next(
        index for index in range(1, len(closes))
        if fast[index - 1] is not None and slow[index - 1] is not None
        and fast[index - 1] <= slow[index - 1] and fast[index] > slow[index]
    )

    result = run_backtest(
        rows, "TEST", {"type": "golden_cross"},
        datetime(2024, 1, 1, tzinfo=timezone.utc),
        datetime(2024, 6, 1, tzinfo=timezone.utc),
        Decimal("10000"), Decimal("0"), Decimal("0"),
    )
    first_buy = next(trade for trade in result["trades"] if trade["action"] == "BUY")
    expected_execution_time = rows[cross_index + 1]["timestamp"]
    assert first_buy["timestamp"] == expected_execution_time
    assert cross_index >= 50


def test_long_warmup_strategy_rejects_insufficient_history():
    with pytest.raises(ValueError, match="Insufficient historical warm-up"):
        run(candles([100 + i for i in range(80)]), {"type": "conservative_trend"})


def test_next_bar_execution_and_no_lookahead_from_future_candles():
    values = [100 + index for index in range(60)]
    rows = candles(values)
    strategy = {
        "type": "custom",
        "name": "causal custom",
        "entry": {"join": "AND", "conditions": [{"left": "SMA20", "operator": ">", "right": {"indicator": "SMA50"}}]},
        "exit": {"join": "AND", "conditions": [{"left": "SMA20", "operator": "<", "right": {"indicator": "SMA50"}}]},
    }
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 3, 1, tzinfo=timezone.utc)
    full = run_backtest(rows, "TEST", strategy, start, end, Decimal("10000"), Decimal("0"), Decimal("0"))
    altered_rows = [dict(row) for row in rows]
    for row in altered_rows[50:]:
        row["close"] *= 5
        row["open"] *= 5
        row["high"] *= 5
        row["low"] *= 5
    altered = run_backtest(altered_rows, "TEST", strategy, start, end, Decimal("10000"), Decimal("0"), Decimal("0"))
    prefix_date = rows[45]["timestamp"][:10]
    full_prefix = [point for point in full["equity_curve"] if point["date"] <= prefix_date]
    altered_prefix = [point for point in altered["equity_curve"] if point["date"] <= prefix_date]
    assert [point["portfolio_value"] for point in full_prefix] == [point["portfolio_value"] for point in altered_prefix]
    for trade in full["trades"]:
        if trade["reason"] != "End-of-period liquidation at final close":
            candle_idx = next(i for i, row in enumerate(rows) if row["timestamp"] == trade["timestamp"])
            assert candle_idx > 0


def test_maximum_drawdown_matches_equity_peak_and_trough():
    result = run(candles([10, 20, 10]), {"type": "buy_hold"}, capital="100")
    assert result["metrics"]["max_drawdown_pct"] == -50
    assert result["metrics"]["max_drawdown_amount"] == 100
    assert result["metrics"]["drawdown_peak_value"] == 200
    assert result["metrics"]["drawdown_trough_value"] == 100


def test_invalid_duplicate_or_negative_historical_candles_are_rejected():
    duplicate = candles([10, 11])
    duplicate[1]["timestamp"] = duplicate[0]["timestamp"]
    with pytest.raises(ValueError, match="duplicate"):
        run(duplicate, {"type": "buy_hold"})

    invalid = candles([10, 11])
    invalid[1]["close"] = -1
    with pytest.raises(ValueError, match="invalid prices"):
        run(invalid, {"type": "buy_hold"})


def test_backtesting_api_requires_existing_authentication():
    response = client.post("/api/v1/backtesting/run", json={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_saved_results_are_isolated_by_authenticated_user():
    from httpx import ASGITransport, AsyncClient
    from app.core.security import get_current_active_user
    from app.database.session import AsyncSessionLocal
    from app.models.backtesting import BacktestRun
    from app.models.user import User

    first_user = User(email="backtest-one@example.test", hashed_password="unused", full_name="One", is_active=True, is_verified=True)
    second_user = User(email="backtest-two@example.test", hashed_password="unused", full_name="Two", is_active=True, is_verified=True)
    async with AsyncSessionLocal() as session:
        session.add_all([first_user, second_user])
        await session.flush()
        session.add_all([
            BacktestRun(id="first-run", user_id=first_user.id, symbol="TCS", strategy_type="buy_hold", result_json={"backtest_id": "first-run", "symbol": "TCS"}),
            BacktestRun(id="second-run", user_id=second_user.id, symbol="INFY", strategy_type="golden_cross", result_json={"backtest_id": "second-run", "symbol": "INFY"}),
        ])
        await session.commit()

    async def first_identity():
        return first_user

    async def second_identity():
        return second_user

    app.dependency_overrides[get_current_active_user] = first_identity
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_async:
            first_runs = await client_async.get("/api/v1/backtesting/runs")
            first_detail = await client_async.get("/api/v1/backtesting/runs/first-run")
            cross_account_detail = await client_async.get("/api/v1/backtesting/runs/second-run")
            cross_account = await client_async.post("/api/v1/backtesting/analyze", json={"backtest_id": "second-run"})
        assert [item["backtest_id"] for item in first_runs.json()] == ["first-run"]
        assert first_detail.status_code == 200
        assert cross_account_detail.status_code == 404
        assert cross_account.status_code == 404

        app.dependency_overrides[get_current_active_user] = second_identity
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_async:
            second_runs = await client_async.get("/api/v1/backtesting/runs")
        assert [item["backtest_id"] for item in second_runs.json()] == ["second-run"]
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)


@pytest.mark.asyncio
async def test_authenticated_run_endpoint_returns_and_persists_real_data_result(monkeypatch):
    from httpx import ASGITransport, AsyncClient
    from app.api.v1 import backtesting as backtesting_api
    from app.core.security import get_current_active_user
    from app.database.session import AsyncSessionLocal
    from app.integrations.market_data.yahoo_provider import YahooFinanceProvider
    from app.models.user import User

    user = User(email="backtest-run@example.test", hashed_password="unused", full_name="Backtest Runner", is_active=True, is_verified=True)
    async with AsyncSessionLocal() as session:
        session.add(user)
        await session.commit()

    class HistoricalTestProvider(YahooFinanceProvider):
        async def get_stock_quote(self, symbol):
            return {"symbol": symbol, "company_name": symbol, "currency": "INR", "price": 120.0, "change_percent": 0.0, "source": "Yahoo Finance"}

        async def get_historical_prices(self, symbol, timeframe="1D", **kwargs):
            start = datetime.fromisoformat(kwargs["start"]).date()
            end = datetime.fromisoformat(kwargs["end"]).date()
            result = []
            cursor = start
            index = 0
            while cursor < end:
                if cursor.weekday() < 5:
                    close = 100.0 + index * 0.1
                    result.append({
                        "timestamp": datetime(cursor.year, cursor.month, cursor.day, tzinfo=timezone.utc).isoformat(),
                        "open": close, "high": close + 1, "low": close - 1, "close": close,
                        "volume": 10000, "source": "Yahoo Finance", "data_status": "HISTORICAL",
                    })
                    index += 1
                cursor += timedelta(days=1)
            return result

        async def get_market_indices(self):
            return []

    async def active_user():
        return user

    monkeypatch.setattr(backtesting_api, "get_market_provider", lambda: HistoricalTestProvider())
    monkeypatch.setattr(backtesting_api.settings, "AI_API_KEY", "")
    app.dependency_overrides[get_current_active_user] = active_user
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_async:
            response = await client_async.post("/api/v1/backtesting/run", json={
                "symbol": "TCS", "exchange": "NSE", "start_date": "2023-01-01", "end_date": "2023-12-31",
                "initial_capital": 100000, "strategy": {"type": "buy_hold"},
                "transaction_cost_pct": 0.10, "slippage_pct": 0.05,
            })
            assert response.status_code == 200, response.text
            result = response.json()
            saved = await client_async.get("/api/v1/backtesting/runs")
            analysis_response = await client_async.post("/api/v1/backtesting/analyze", json={"backtest_id": result["backtest_id"]})
        assert result["data"]["status"] == "HISTORICAL"
        assert result["data"]["candles"] > 200
        assert result["trades"][0]["action"] == "BUY"
        assert result["trades"][0]["timestamp"] == result["data"]["first_timestamp"]
        assert result["comparison"]["buy_hold_return_pct"] == result["metrics"]["total_return_pct"]
        assert result["backtest_id"] == saved.json()[0]["backtest_id"]
        assert analysis_response.status_code == 200
        assert "Overall Assessment" in analysis_response.json()["analysis"]
        assert "Past backtest performance does not guarantee future results" in analysis_response.json()["analysis"]
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)
