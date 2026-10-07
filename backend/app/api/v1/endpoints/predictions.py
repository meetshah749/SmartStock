from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.prediction_service import prediction_engine, comparison_engine
from app.services.news_service import news_service
from app.services.market_data import get_market_provider

provider = get_market_provider()

router = APIRouter(prefix="", tags=["AI Predictions & Market News"])


@router.get("/stocks/{symbol}/prediction")
async def get_stock_ai_prediction(symbol: str) -> Any:
    """Get AI prediction signal, confidence meter, target prices, and explainable feature attributions for a given ticker."""
    stock = await provider.get_stock_quote(symbol)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock ticker '{symbol}' not found")

    if isinstance(stock, dict):
        price_rupees = float(stock.get("price") or 2980.5)
    else:
        price_rupees = float(getattr(stock, "price", 2980.5))
    prediction = prediction_engine.predict(symbol=symbol, current_price=price_rupees)
    return prediction


@router.get("/stocks/{symbol}/news")
async def get_stock_news(symbol: str) -> Any:
    """Get news articles and sentiment ratings for a specific stock symbol."""
    return news_service.get_stock_news(symbol)


@router.get("/stocks/compare")
async def compare_two_stocks(
    symbol_a: str = Query(..., alias="symbol_a", description="First stock ticker to compare"),
    symbol_b: str = Query(..., alias="symbol_b", description="Second stock ticker to compare"),
) -> Any:
    """Compare two stocks using AI-style technical scoring to determine the better buy candidate."""
    try:
        return await comparison_engine.compare_stocks(symbol_a, symbol_b)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/news")
async def get_macro_market_news(category: Optional[str] = Query(None)) -> Any:
    """Get overall market news feed with sentiment badges."""
    return news_service.get_market_news(category=category)
