import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.config import settings
from app.services.indicators import calculate_rsi, calculate_sma, calculate_macd
from app.services.stock_universe import INDIAN_EQUITY_UNIVERSE
from app.services.symbol_mapper import normalize_symbol


@pytest.mark.asyncio
async def test_search_stocks_api():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        res = await ac.get(f"{settings.API_V1_STR}/stocks/search?q=REL")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        assert data[0]["symbol"] == "RELIANCE"
        assert data[0]["data_status"] in {"LIVE", "DELAYED", "DEVELOPMENT DATA"}


@pytest.mark.asyncio
async def test_stock_quote_and_history_api():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Quote
        res = await ac.get(f"{settings.API_V1_STR}/stocks/TCS/quote")
        assert res.status_code == 200
        quote = res.json()
        assert quote["symbol"] == "TCS"
        assert "price" in quote
        assert quote["data_status"] in ["LIVE", "DELAYED", "HISTORICAL"]

        # Historical Prices
        hist_res = await ac.get(f"{settings.API_V1_STR}/stocks/TCS/prices?timeframe=1M")
        assert hist_res.status_code == 200
        history = hist_res.json()
        assert len(history) > 10
        assert "open" in history[0]
        assert "close" in history[0]

        # Indicators API
        ind_res = await ac.get(f"{settings.API_V1_STR}/stocks/TCS/indicators?timeframe=1M")
        assert ind_res.status_code == 200
        ind_data = ind_res.json()
        assert "indicators" in ind_data
        assert "rsi14" in ind_data["indicators"]
        assert "macd" in ind_data["indicators"]


def test_technical_indicator_calculations():
    sample_prices = [10.0, 11.0, 12.0, 11.5, 12.5, 13.0, 12.8, 13.5, 14.0, 14.5, 14.2, 15.0, 15.5, 16.0, 15.8, 16.5]
    sma = calculate_sma(sample_prices, 5)
    assert len(sma) == len(sample_prices)
    assert sma[4] == round(sum(sample_prices[:5]) / 5, 2)

    rsi = calculate_rsi(sample_prices, 14)
    assert len(rsi) == len(sample_prices)
    assert rsi[-1] is not None
    assert 0 <= rsi[-1] <= 100

    macd = calculate_macd(sample_prices, 3, 6, 3)
    assert "macd_line" in macd
    assert "histogram" in macd


def test_broad_indian_universe_and_company_name_aliases():
    assert len(INDIAN_EQUITY_UNIVERSE) >= 100
    assert len(INDIAN_EQUITY_UNIVERSE) == len(set(INDIAN_EQUITY_UNIVERSE))
    assert normalize_symbol("Tata Power Company Limited") == "TATAPOWER"
    assert normalize_symbol("Mahindra & Mahindra") == "M&M"
    assert normalize_symbol("BAJAJ-AUTO") == "BAJAJ-AUTO"


@pytest.mark.asyncio
async def test_stock_universe_api_can_filter_nse_and_bse():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"{settings.API_V1_STR}/stocks/universe?exchange=BSE&limit=500")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 100
    assert all("BSE" in entry["listing_exchanges"] for entry in data)
    assert any(entry["symbol"] == "TATAPOWER" for entry in data)
