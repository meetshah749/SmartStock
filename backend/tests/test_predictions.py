import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ai_prediction_endpoint():
    response = client.get("/api/v1/stocks/RELIANCE/prediction")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "RELIANCE"
    assert data["signal"] in ["BULLISH", "BEARISH", "NEUTRAL"]
    assert 0 <= data["confidence_percent"] <= 100
    assert "target_1d" in data["price_targets"]
    assert "target_5d" in data["price_targets"]
    assert "target_30d" in data["price_targets"]
    assert len(data["feature_attributions"]) > 0


def test_ai_prediction_not_found():
    response = client.get("/api/v1/stocks/NONEXISTENT_TICKER_XYZ/prediction")
    assert response.status_code == 404
