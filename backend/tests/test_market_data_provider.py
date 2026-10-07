import app.services.market_data as market_data
from app.integrations.market_data.yahoo_provider import YahooFinanceProvider
from app.services.prediction_service import StockComparisonEngine


def test_market_provider_factory_uses_yahoo_for_live_real_data(monkeypatch):
    monkeypatch.setattr(market_data.settings, "MARKET_DATA_PROVIDER", "yahoo")
    market_data._singleton_provider = None

    provider = market_data.get_market_provider()

    assert provider.provider_name() == "Yahoo Finance"
    assert provider.is_live_provider() is True


def test_stock_compare_returns_preferred_stock_and_reasoning():
    engine = StockComparisonEngine()
    result = engine.compare_symbols("RELIANCE", "TCS")

    assert "preferred_stock" in result
    assert result["preferred_stock"] in {"RELIANCE", "TCS"}
    assert len(result["stocks"]) == 2
    assert result["decision"] in {"BUY", "HOLD", "WAIT"}
    assert len(result["rationale"]) >= 2


def test_yahoo_symbol_mapping_supports_broader_nse_and_bse_universe():
    assert YahooFinanceProvider.map_symbol("TATAPOWER") == "TATAPOWER.NS"
    assert YahooFinanceProvider.map_symbol("M&M") == "M&M.NS"
    assert YahooFinanceProvider.map_symbol("TATAPOWER.BO") == "TATAPOWER.BO"
