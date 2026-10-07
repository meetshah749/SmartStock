from fastapi.testclient import TestClient
import pytest

import app.api.v1.assistant as assistant
from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_assistant_resolves_only_supported_tickers():
    assert assistant._symbols_in_text("Can you compare RELIANCE and TCS?") == ["RELIANCE", "TCS"]
    assert assistant._symbols_in_text("What does RSI mean?") == []
    assert assistant._symbols_in_text("Give me a report on HDFC") == ["HDFCBANK"]
    assert assistant._symbols_in_text("Compare HDFC and ICICI Bank") == ["HDFCBANK", "ICICIBANK"]
    assert assistant._symbols_in_text("Compare ICICI Bank with HDFC Bank") == ["ICICIBANK", "HDFCBANK"]


@pytest.mark.asyncio
async def test_resolves_non_catalog_ticker_and_company_name(monkeypatch):
    class SearchProvider:
        async def get_stock_quote(self, symbol):
            if symbol == "NVDA":
                return {"symbol": "NVDA"}
            return None

        async def search_stocks(self, query):
            if query.lower() == "nvidia":
                return [{"symbol": "NVDA"}]
            return []

    monkeypatch.setattr(assistant, "get_market_provider", lambda: SearchProvider())

    ticker_result = await assistant._resolve_stock_symbols("NVDA", [])
    company_result = await assistant._resolve_stock_symbols("Tell me about Nvidia", [])
    search_result = await assistant._resolve_stock_symbols("Search Nvidia financials", [])

    assert ticker_result == (["NVDA"], True, [])
    assert company_result == (["NVDA"], True, [])
    assert search_result == (["NVDA"], True, [])


@pytest.mark.asyncio
async def test_reports_unknown_ticker_instead_of_generic_answer(monkeypatch):
    class EmptyProvider:
        async def get_stock_quote(self, symbol):
            return None

        async def search_stocks(self, query):
            return []

    monkeypatch.setattr(assistant, "get_market_provider", lambda: EmptyProvider())
    monkeypatch.setattr(settings, "AI_API_KEY", "")

    response = client.post("/api/v1/assistant/chat", json={"message": "UNKNOWNCO"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["stock_lookup_requested"] is True
    assert payload["stocks"] == []
    assert "couldn't verify that stock" in payload["reply"]


def test_assistant_explains_market_terms_without_llm(monkeypatch):
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    response = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Explain RSI in simple terms", "conversation": []},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "market-aware"
    assert payload["llm_configured"] is False
    assert "Relative Strength Index" in payload["reply"]
    assert "not personalized financial advice" in payload["disclaimer"]


@pytest.mark.asyncio
async def test_configured_model_receives_general_questions(monkeypatch):
    captured = {}

    class MockResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "Here is a concise general answer."}}]}

    class MockAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, headers, json):
            captured["url"] = url
            captured["messages"] = json["messages"]
            return MockResponse()

    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")
    monkeypatch.setattr(assistant.httpx, "AsyncClient", MockAsyncClient)

    response = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Explain how a binary search works", "conversation": []},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "llm"
    assert payload["llm_configured"] is True
    assert payload["reply"] == "Here is a concise general answer."
    assert "general-purpose conversational assistant" in captured["messages"][0]["content"]
    assert captured["messages"][-1] == {"role": "user", "content": "Explain how a binary search works"}


def _stock_snapshot(symbol, one_month, one_year, volatility):
    return {
        "symbol": symbol,
        "company_name": f"{symbol} Bank Limited",
        "description": "Company profile.",
        "exchange": "NSE",
        "sector": "Financial Services",
        "industry": "Banking",
        "price": 1000.0,
        "currency": "INR",
        "change_percent": 1.0,
        "open": 990.0,
        "high": 1010.0,
        "low": 980.0,
        "prev_close": 990.0,
        "volume": 100000,
        "market_status": "OPEN",
        "rsi_14": 55.0,
        "sma20": 995.0,
        "sma50": 980.0,
        "one_month_change_percent": one_month,
        "one_year_change_percent": one_year,
        "observed_one_year_high": 1200.0,
        "observed_one_year_low": 800.0,
        "annual_history_points": 250,
        "history_points": 22,
        "daily_volatility_percent": volatility,
        "volatility_band": "moderate observed volatility",
        "data_status": "LIVE",
        "source": "test market feed",
        "timestamp": "2026-10-07T09:00:00+00:00",
    }


def test_hdfc_prompt_returns_report_snapshot(monkeypatch):
    async def fake_snapshot(symbol):
        return _stock_snapshot("HDFCBANK", 2.5, 12.0, 1.1)

    monkeypatch.setattr(settings, "AI_API_KEY", "")
    monkeypatch.setattr(assistant, "_get_stock_snapshot", fake_snapshot)

    response = client.post("/api/v1/assistant/chat", json={"message": "HDFC"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["stocks"][0]["symbol"] == "HDFCBANK"
    assert payload["stocks"][0]["one_year_change_percent"] == 12.0
    assert "RSI-14 55.0" in payload["reply"]
    assert "Company profile" in payload["reply"]


def test_hdfc_icici_prompt_returns_structured_comparison(monkeypatch):
    snapshots = {
        "HDFCBANK": _stock_snapshot("HDFCBANK", 2.5, 12.0, 1.1),
        "ICICIBANK": _stock_snapshot("ICICIBANK", 3.0, 8.0, 1.4),
    }

    async def fake_snapshot(symbol):
        return snapshots[symbol]

    monkeypatch.setattr(settings, "AI_API_KEY", "")
    monkeypatch.setattr(assistant, "_get_stock_snapshot", fake_snapshot)

    response = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Compare HDFC and ICICI Bank"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [stock["symbol"] for stock in payload["stocks"]] == ["HDFCBANK", "ICICIBANK"]
    assert payload["comparison"]["one_month_performance_leader"] == "ICICIBANK"
    assert payload["comparison"]["one_year_performance_leader"] == "HDFCBANK"
    assert payload["comparison"]["lower_observed_volatility"] == "HDFCBANK"


@pytest.mark.asyncio
async def test_stock_report_includes_only_available_vendor_fundamentals(monkeypatch):
    class FakeProvider:
        async def get_stock_quote(self, symbol):
            return {
                "price": 100.0,
                "currency": "INR",
                "change_percent": 1.0,
                "source": "test feed",
            }

        async def get_company_info(self, symbol):
            return {"company_name": "HDFC Bank Limited", "sector": "Financial Services"}

        async def get_historical_prices(self, symbol, timeframe="1D"):
            return [
                {"timestamp": f"2026-01-{day:02d}", "close": float(day)}
                for day in range(1, 24)
            ]

        async def get_fundamental_data(self, symbol):
            return {"metrics": {"trailing_pe": 15.2}, "source": "test feed", "retrieved_at": "now"}

    monkeypatch.setattr(assistant, "get_market_provider", lambda: FakeProvider())

    result = await assistant._get_stock_snapshot("HDFCBANK")

    assert result["fundamentals"]["metrics"] == {"trailing_pe": 15.2}
    assert result["sma20"] == 13.5
    assert result["sma50"] is None


@pytest.mark.asyncio
async def test_yahoo_fundamentals_normalize_dividend_yield(monkeypatch):
    from app.integrations.market_data.yahoo_provider import YahooFinanceProvider

    provider = YahooFinanceProvider()

    class FakeTicker:
        info = {
            "dividendYield": 0.42,
            "trailingPE": 15.2,
        }

    async def fake_fetch_ticker(symbol):
        return FakeTicker()

    monkeypatch.setattr(provider, "_fetch_ticker", fake_fetch_ticker)

    result = await provider.get_fundamental_data("HDFCBANK")

    assert result["metrics"]["dividend_yield"] == pytest.approx(0.0042)
    assert result["metrics"]["trailing_pe"] == 15.2
