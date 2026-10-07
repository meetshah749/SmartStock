import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_market_news_endpoint():
    response = client.get("/api/v1/news")
    assert response.status_code == 200
    articles = response.json()
    assert isinstance(articles, list)
    assert len(articles) > 0
    first = articles[0]
    assert "title" in first
    assert "sentiment" in first
    assert first["sentiment"] in ["BULLISH", "BEARISH", "NEUTRAL"]


def test_ticker_news_endpoint():
    response = client.get("/api/v1/stocks/RELIANCE/news")
    assert response.status_code == 200
    articles = response.json()
    assert isinstance(articles, list)
    assert len(articles) > 0
    assert articles[0]["ticker_symbol"] == "RELIANCE"
